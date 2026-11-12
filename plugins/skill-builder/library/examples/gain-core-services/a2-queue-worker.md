# Archetype A2: CQS queue worker (message-driven)

**Where:** Gain.Integration.Outbound (outbound to River Salesforce / SAP), Gain.Integration.Common.API
(router + attachment + warranty QR consumers).
**Read first:** `.ai/standards/icsol-cqs.md`, `.ai/system/system-map.md`.

## How a message flows (Outbound)

```
IntegrationOutBoundQueue  {ProcessCode, SubProcessCode, ReferenceSlno, TenantSlno, IntegrationType, RetryCount}
  -> IntegrationConsumer.HandleAsync          (always ACK, see below)
     -> guards: ReferenceSlno > 0, IntegrationType and SubProcessCode present, RetryCount <= MaxQueueRetryCount
     -> switch SubProcessCode  -> domain service (Presale/Opportunity, Product/Booking, Workshop/JobCard, ...)
          -> switch IntegrationType ("riversf", "riversap") -> <Action>_<Target>()
               -> Get<Thing>DetailsQuery (Dapper; inline SQL or *DetailsForIntegration proc)
               -> validate -> build request payload (APIRequestPayload/<Target>/...)
               -> ApiCallingInterface.Post/Patch/PutAsync<TResponse>(url, payload, "<ExternalAuth section>")
               -> IntegrationDomainHelper.MapResponse -> IntegrationResponseDetails {Status, FailureStage, ...}
     -> CreateAndUpdateIntegrationResponseDetailCommand -> TSCommon.dbo.integration_response_details (S/F)
     -> FailureStage PayloadBuild|DataFetch and retry < 3  -> republish immediately (RetryCount+1)
     -> Status success -> publish IntegrationResponseSyncQueue
IntegrationResponseSyncQueue
  -> IntegrationResponseSyncConsumer: switch SubProcessCode -> Update<Thing>Command
       -> write external ids back to DMS tables (EF), SyncToMainTable = 1
Schedulers: QueuePublishingScheduler (retry F rows, RetryCount < 3), IntegrationResponseSyncScheduler
            (re-sync S rows not yet synced), Send*AlertsScheduler (daily mails), SendIdMismatchAlertsScheduler
```

## Golden rules

1. **A consumer never throws and never NACKs for business failures.** It persists the failure
   (`Status='F'`, `FailureStage`) and returns `true` (ACK). Retries belong to the schedulers. A
   NACK loop calls the external API again and again.
2. **Handlers called from consumers don't throw.** They catch, log and set `IsSuccess=false`.
   This is the opposite of A1.
3. **Set `FailureStage` correctly**, because retry behaviour depends on it:
   `DataFetch` (query failed or empty) and `PayloadBuild` (missing required data) are retried immediately.
   `APICall` (network/auth/timeout), `APIResponse` (external system said no), `DBPersist`,
   `SyncToMainTable` and `Unexpected` wait for the scheduler.
4. **Idempotency:** a message can arrive twice. Create flows must tolerate it: check for an
   existing external id or a prior `S` row before creating again.
5. **Every routing code appears in several tables.** `generated/entry-points.md` lists every
   `switch` and its codes. A new SubProcessCode that is missing from the sync consumer never writes
   its external ids back, and nothing reports an error.

## Recipe: add a SubProcessCode (`/gain-dev:add-subprocess`)

| # | Where | What |
|---|---|---|
| 1 | DB: `TSCommon.dbo.ExternalSystemIntegrationConfigurationMapper` | Row for ProcessCode / SubProcessCode / IntegrationType (the router in Common.API only publishes configured codes). Script it and attach it to the PR |
| 2 | `CQS/Queries/Get<Thing>DetailsQuery(.cs, Handler.cs)` + `<Thing>Details.cs` | Data fetch. Swallow-and-flag error style. Proc or parameterised SQL |
| 3 | `CQS/APIRequestPayload/<Target>/<Target><Action>Payload.cs` | Request body |
| 4 | `CQS/APIResponsePayload/<Target>/<Target><Action>Response.cs` | Response body |
| 5 | `CQS/Helpers/ApiEndpoints.cs` | `public const string <Target><Action> = "api/..."` |
| 6 | `CQS/<Domain>/I<Thing>.cs` + `<Thing>.cs` | Domain method: fetch → validate → build → call → `MapResponse`; `switch IntegrationType` with an `_ =>` failure branch |
| 7 | `API/DILoader.cs` | `services.AddScoped<I<Thing>, <Thing>>()` if the domain service is new |
| 8 | `API/BackgroundServices/IntegrationConsumer.cs` | `case "<code>":` + resolve the service from the scope |
| 9 | `CQS/Commands/Update<Thing>Command(.cs, Handler.cs)` | Write-back of external ids + `SyncToMainTable = 1` |
| 10 | `API/BackgroundServices/IntegrationResponseSyncConsumer.cs` | `case "<code>":` → `CallUpdate<Thing>Command` |
| 11 | EF (only if writing new tables) | Model, DbSet/ToTable, repository, DI registration |
| 12 | Monitoring / alerts | Usually nothing to do: they read `integration_response_details` generically. Check `MonitoringService` if the code needs special republish handling |
| 13 | Docs | Run the generator. Add the code's business meaning to `overview.md` |

## Recipe: add an integration target (new `IntegrationType`)

`appsettings.json` → `ExternalAuth:<Name>` (`AuthType`, `ClientId`, `ClientSecret` empty) and
`APIBaseUrl:<Client>:<Url>`. If the auth scheme is new, implement `IAuthHandler`, then register it in
`AddAuthHandlers`. Add a `"<type>" =>` branch in each domain method that should support it, add the
payload and response classes under `APIRequestPayload/<Target>/`, and add rows in the config mapper table.

## Diagnosing a failure (`/gain-dev:fix`)

Start from the business key, not from the logs:

```sql
SELECT TOP 20 Uid, Status, FailureStage, StatusCode, ErrorMessage, RetryCount, SyncToMainTable, LastUpdatedTime
FROM TSCommon.dbo.integration_response_details
WHERE ReferenceSlno = @ReferenceSlno AND SubprocessCode = @SubProcessCode
ORDER BY Uid DESC;
-- then TSCommon.dbo.ExternalAPILog for the raw HTTP exchange
```

`FailureStage` points to the layer to look at. `RetryCount >= 3` rows are not retried until
someone resets them (`/api/v1/monitoring/reset` or `republish`).
