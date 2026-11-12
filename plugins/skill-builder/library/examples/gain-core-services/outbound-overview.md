# Gain.Integration.Outbound: overview

> Narrative. Facts the code proves are in `generated/`. Items marked `(inferred - confirm)` still need owner review.

## Purpose

When something happens in the DMS (an opportunity is created, a booking is invoiced, a receipt is
posted, a job card is opened), a message lands on `IntegrationOutBoundQueue`. This service reads
the full record from the DMS databases, builds the request the OEM system expects, calls **River
Salesforce** (`riversf`) or **River SAP** (`riversap`), logs every attempt in
`TSCommon.dbo.integration_response_details`, and writes the ids the OEM returns back into the DMS
tables. It also exposes monitoring APIs for the integration dashboard and sends daily summary and
alert mails.

## Where it sits

Upstream: Gain.Integration.Common.API routes DMS events here after looking them up in
`ExternalSystemIntegrationConfigurationMapper`. MobileApp CQS areas publish directly.
Downstream: River Salesforce and River SAP. See `.ai/system/system-map.md`.

## Main flows

### 1. Send an event (IntegrationConsumer)
`BackgroundServices/IntegrationConsumer.cs` → guards (ReferenceSlno, IntegrationType,
SubProcessCode, `RetryCount > MaxQueueRetryCount` discarded as duplicates) → special case:
`riversf` + `ProcessCode RECEIPT` with ReceiptMode `'W'` is dropped (`GetReceiptModeQuery`) →
`switch SubProcessCode` → domain service in `CQS/<Domain>/` (e.g. `Presale/Opportunity.cs`) →
`Get<Thing>DetailsQuery` (Dapper; inline SQL or a `*DetailsForIntegration` / `API_*_Sync_Proc` proc) →
validation → payload (`APIRequestPayload/RiverSF|RiverSap`) → `APICall/ApiCallingInterface.cs`
(auth handler resolved from `ExternalAuth:<name>:AuthType`) → `Helpers/IntegrationDomainHelper.MapResponse`
→ `CreateAndUpdateIntegrationResponseDetailCommand` (row with Status `S`/`F` and `FailureStage`).
- `FailureStage` `PayloadBuild` / `DataFetch` with DB retry count < 3 → republished immediately
  (an external id may not be synced yet, e.g. the Salesforce opportunity id a follow-up needs).
- Success → `IntegrationResponseSyncQueue`.
- The consumer **always ACKs**.

### 2. Write back external ids (IntegrationResponseSyncConsumer)
`BackgroundServices/IntegrationResponseSyncConsumer.cs` → `switch SubProcessCode` →
`Commands/Update<Thing>CommandHandler.cs` → deserialize the OEM response → update DMS tables via
repositories (e.g. `Enquiry.ExternalSystemEnquiryId`, `Oppurtunity.ExternalSystemLeadId`) →
`integration_response_details.SyncToMainTable = 1`. Opportunity create also records id
mismatches in `TSCommon.dbo.ExternalSystem_Id_Mismatch_Log`, which `SendIdMismatchAlertsScheduler` mails daily.

### 3. Retries and re-syncs (schedulers)
- `QueuePublishingScheduler` (every `QueuePublishingSchedulerRunTimer` min): rows with Status `I`
  older than 30 min, or `F`/`C` older than 10 min, `RetryCount < 3`, `Type='O'` → republished
  (through `CreateAttachmentQueue` when the config says an attachment is required).
  Status values: `I` initiated, `S` success, `F` failed, `C` corrected by an admin (inferred - confirm `I` and `C`).
- `IntegrationResponseSyncScheduler`: `S` rows with `SyncToMainTable = 0` older than 10 min → re-sync.
- `SendAlertsMessagesScheduler` / `SendInboundAlertsMessagesScheduler`: daily summary mails (outbound / inbound).

### 4. Monitoring APIs (A1)
`Controllers/MonitoringController.cs` (`api/v1/monitoring/*`): summary, analytics, trend,
failed, success, stuck, transaction search, inbound logs, external API logs, plus **actions**:
`reset` (PATCH), `republish`, `republish-sync`. `OutBoundIntegrationController`:
`integration/outbound` and `integration/response-sync` publish a message by hand.

## Business codes

Routing tables with handlers: `generated/entry-points.md`. Meaning of each code (inferred from
method names - confirm):

| Area | SubProcessCodes | Meaning |
|---|---|---|
| Presale | createopportunity, updateopportunity, opportunityclosed, opportunitylost | Opportunity lifecycle to SF |
| Presale | createfollowup, updatefollowup | Follow-ups to SF |
| Presale | createtestride, updatetestride, canceltestride, completetestride | Test rides to SF |
| Booking | slbkgcrt, slbkgcan, slfinroc, psallotmentcreate, slaccinv, psapprovalcreate, slinscom, slregcom, sldelcom | Booking create/cancel, finance, allotment, accessories invoice, invoice approval, insurance, registration (RTO), delivery |
| Accounts | receipt | Payment receipt to SF (mode `W` skipped) |
| Workshop | createjobcard, updatejobcard, createservicejobvor, creatersa, createew | Job cards, VOR, RSA and extended-warranty sales |
| Spares | countersalecreate, countersaleupdate | Over-the-counter sales |
| CRM | caseupdate, caseclosure, casefollowups | Case updates and follow-ups |
| SAP | generategrn, createpurchaseorderforcoco/dodo, createsparepurchaseorderforcoco/dodo | GRN, vehicle and spare purchase orders (COCO / DODO dealer types) |

## Running locally

`dotnet run --project Gain.Integration.Outbound.API`. Needs RabbitMQ and the DMS databases. Config
keys: `generated/config.md`. Use user-secrets for connection strings and `ExternalAuth` secrets.
Five schedulers start immediately (`TimeSpan.Zero`). Point `ConnectionStrings` at a dev database
so they don't republish real records.
