# Gain.Integration.Outbound: gotchas

> One line per trap: `- <trap>: <cause / evidence>. <how to avoid>`.

## Code
- New SubProcessCode never writes ids back: it was added to `IntegrationConsumer` but not to `IntegrationResponseSyncConsumer`. Add both. Compare the two routing tables in `generated/entry-points.md`.
- Editing a file changes nothing: `InternalAlerts/**` and 4 files in `APIRequestPayload/` (`ProductPurchaseInvoiceCreatePayload`, `ProductPurchaseOrderCreatePayload`, `SparePartsPurchaseCreatePayload`, `SparePurchaseOrderCreate`) are `<Compile Remove>`d in the CQS csproj. Check `generated/overview.md` → Traps before editing.
- Misleading name: `ApiEndpoints.RiverSapCreateOpportunity` is the **Salesforce** opportunities endpoint (used with `SFBaseUrl`). Don't "fix" it to SAP.
- Shared endpoints: `api/otc-orders` serves counter sale, RSA and EW, and `http/DMS/COCO-Sales/Payment` is shared by counter sale, RSA, EW and future domains. A change to one payload can affect the others.
- Throwing from a handler or domain method that the consumer calls breaks the "always ACK" contract and can loop the external call. Return a failure `IntegrationResponseDetails` with a `FailureStage` instead.
- `ReferenceSlno` means a different key per code (OppurtunitySlno, ProductSaleSlno, ReceiptSlno, CallSlno...). Check the details query for the code before assuming.

## Retry and duplicates
- Three retry limits exist: the immediate-republish guard (`dbRetryCount < 3`, hard-coded in the consumer), the scheduler SQL (`RetryCount < 3`, hard-coded), and `MaxQueueRetryCount` (default 15, set only in `appsettings.Development.json`). `QueueRetryCount: 3` in appsettings is **not read** by the code (confirm). Change all of them together or not at all.
- RabbitMQ can deliver a message twice. Create flows must check for an existing external id before creating again.
- `RetryCount >= 3` rows are never retried automatically. Use monitoring `reset` / `republish` after fixing the cause.

## Data and procs
- Keep DB spelling: `Oppurtunity`, `OppurtunitySlno`, `OppurtunityNo` are real names.
- Several details procs return multiple result sets read **by position** (`QueryMultipleAsync`: booking, product purchase, purchase orders). Never reorder result sets in those procs.
- Some details procs are called without a database prefix (`GetBookingDetailsForIntegration`, `GetEWDetailsForIntegration`, ...), so they run in the database of the handler's connection string. Export them with the right `db-map.json` entry.

## Business rules hidden in code
- RiverSF receipts with ReceiptMode `'W'` are dropped. The same rule exists in Common.API's router. Change both.
- Opportunity create sends `FollowUp = null`. The follow-up block is commented out "changes requested by chandan on 27th july" (see `decisions.md`).
- `ExpectedCloseDate` for a new opportunity is today + 3 months, hard-coded.

## Configuration
- `MaxQueueRetryCount` and `IdMismatchAlertSchedulerRunTimer` are read by code but missing from the base `appsettings.json`. Production falls back to code defaults (15 and 1440).
- `AllowedOrigin` is `*` in the base config.

## Security (confirm with owners)
- No ASP.NET authentication is configured (`UseAuthorization` without any scheme). `monitoring/reset`, `republish`, `republish-sync` and `integration/outbound` accept any caller that can reach the port. Confirm the nginx vhost does not expose them publicly.
- `appsettings.Development.json` contains real-looking secrets. Move them to user-secrets and rotate them.
