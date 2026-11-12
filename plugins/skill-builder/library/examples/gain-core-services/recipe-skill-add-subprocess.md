---
name: add-subprocess
description: Add or extend an outbound integration flow (new SubProcessCode, or a new IntegrationType branch for an existing code) in Gain.Integration.Outbound - config mapper row, details query, payloads, endpoint constant, domain method, both consumers, write-back command, DI, docs. Use for "send X to River SF/SAP" requests.
argument-hint: "<subprocesscode> <integration type> <what it sends>"
---

# Add an A2 SubProcessCode

Read `.ai/archetypes/a2-queue-worker.md` (golden rules + recipe), `.ai/system/system-map.md`,
`<Solution>/.ai/gotchas.md`, and `<Solution>/.ai/generated/entry-points.md` (routing tables).

## 1. Gather inputs (ask for anything missing, never guess)

- ProcessCode and SubProcessCode as the DMS sends them, and the IntegrationType (`riversf`, `riversap`, ...).
- External API: method, path, request JSON and response JSON (sample or spec), and which external id
  comes back and where in the DMS it must be stored.
- Source data: which DMS tables or proc provide the fields, keyed by `ReferenceSlno`.
- Required fields: which missing fields make it a `PayloadBuild` failure.
- Whether a document attachment is needed. This goes through `CreateAttachmentQueue` in Common.API.

## 2. Find the template

Choose the closest existing code from the routing table, for the same domain and the same target.
Open its query handler, domain method, payload and response classes, update command, and both
consumer cases. Copy their structure exactly.

## 3. Implement (all steps, in order)

1. **Config mapper row**: `<Solution>/db/changes/<date>-<code>-mapper.sql`, re-runnable
   (`IF NOT EXISTS`), for `TSCommon.dbo.ExternalSystemIntegrationConfigurationMapper`. Without it
   the Common.API router never publishes the code.
2. **Details query**: `Queries/Get<Thing>DetailsQuery.cs`, `...QueryHandler.cs`, `<Thing>Details.cs`.
   Dapper with parameters (proc or SQL). On exception: log with `ErrorCode E781`, set
   `IsSuccess=false`, return. **Don't throw.**
3. **Payloads**: `APIRequestPayload/<Target>/<Target><Action>Payload.cs` and
   `APIResponsePayload/<Target>/<Target><Action>Response.cs`. Property names follow the external
   API (use `[JsonProperty]` if the C# name differs).
4. **Endpoint**: `Helpers/ApiEndpoints.cs` → `public const string <Target><Action> = "...";`
5. **Domain method** in `CQS/<Domain>/<Thing>.cs` (and the interface):
   fetch → `if (!query.IsSuccess || data == null)` return `FailureStage.DataFetch` →
   validate required fields → return `FailureStage.PayloadBuild` →
   `switch (queuePayload.IntegrationType?.ToLower())` with an `_ =>` "Unknown Integration Type" failure →
   build the payload → `result.Url`, `result.RequestPayload = JsonConvert.SerializeObject(payload)` →
   `_apiCallingInterface.<Verb>Async<TResponse>(fullUrl, payload, integrationName: "<ExternalAuth section>")` →
   `IntegrationDomainHelper.MapResponse(...)`. Wrap the method in try/catch → `FailureStages.Unexpected`.
   **Idempotency:** for create flows, check whether the DMS row already has the external id, and decide with
   the developer whether a duplicate becomes an update or is skipped.
6. **DI**: `services.AddScoped<I<Thing>, <Thing>>()` in `DILoader` if the domain service is new.
7. **IntegrationConsumer**: resolve the service from the scope (next to the others) and add
   `case "<code lower-case>": responseDetails = await <svc>.<Method>(queuePayload); break;`
8. **Write-back**: `Commands/Update<Thing>Command(.cs, Handler.cs)`. Deserialize the response, write
   the external ids to the DMS table through repositories, set `SyncToMainTable = 1` on the
   `integration_response_details` row, and save **that** context last. Log id mismatches the way
   `UpdateOpportunityCommandHandler` does, if the flow overwrites ids.
9. **IntegrationResponseSyncConsumer**: `case "<code>":` → `CallUpdate<Thing>Command(...)`.
   **This is the step people forget.**
10. **EF** (new tables only): model, `DbSet` + `ToTable`, repository, DI.
11. **Monitoring**: check whether `MonitoringService` republish logic needs anything for this code
    (attachments, special keys). Usually it doesn't.

## 4. Check before you finish

- [ ] The code appears in **both** consumer switches (`python tools/gain-docgen/gain_docgen.py`, then
      compare the two routing tables in `generated/entry-points.md`).
- [ ] No path throws out of the consumer. Every failure sets `Status=false` and a `FailureStage`.
- [ ] The `ExternalAuth:<name>` and `APIBaseUrl` keys exist in `appsettings.json`.
- [ ] `/gain-dev:verify` passes.
- [ ] Tell the developer how to test: the sample message to publish on `IntegrationOutBoundQueue`
      (or `POST api/v1/integration/outbound`), and the query showing the resulting
      `integration_response_details` row and the write-back.
- [ ] Add the code and its business meaning to `<Solution>/.ai/overview.md`.
