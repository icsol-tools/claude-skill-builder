# Archetype A1: CQS HTTP API (request-driven)

**Where:** Gain.Integrations (all controllers), and the newer areas of Gain.MobileApp.Integrations
(`RiverMobileAppApisController`, `Warranty{DC,GRN,QC}Controller`, `TransitController`).
**Read first:** `.ai/standards/icsol-cqs.md`, `.ai/standards/sql-safety.md`.

## How a request flows

```
HTTP -> Controller action
          -> (token check: ValidateToken() / VerifyAccessTokenQuery)
          -> (ValidationFilter<TDto> at the API, or validator inside the handler)
          -> map DTO -> Command / Query
          -> _commandDispatcher.HandleAsync<TCommand>(cmd)  |  _queryDispatcher.HandleAsync<TQuery,TResult>(qry)
               -> Handler: Dapper read / EF write / proc call
          -> ApiResponse.AddData(result); IsSuccess
       <- ApiResponseWrapper<ApiResponse>(response, HttpStatusCode.OK)
Exceptions -> IcsolException / LogAndThrow -> global ConfigureExceptionHandler<SharedResource>()
```

Some A1 actions also start an outbound integration. MobileApp publishes straight to
`Queues:IntegrationOutBoundQueueKey`. Everything else goes through Common.API `/api/v1/common/mqWriter`.
See `.ai/system/system-map.md` before adding a new trigger.

## Recipe: add an endpoint (`/gain-dev:add-endpoint`)

Touch these, in this order. Skip a step only if the thing already exists.

1. **DTO**: `<API>/Dto/<Area>/<Thing>Dto.cs` (request shape exposed to the caller).
2. **Command or Query**: `<Domain>.CQS/Commands/<Verb><Thing>Command.cs : BaseCommand`, or
   `Queries/Get<Thing>Query.cs : BaseQuery<TResult>` + the result class.
3. **Validator**: put it where the solution already puts them (see standards → Validation).
   API-level: add `IValidator<TDto>` and `ValidationFilter<TDto>` registrations in `DILoader`.
4. **Handler**: `<Verb><Thing>CommandHandler : ICommandHandler<...>` or `Get<Thing>QueryHandler`.
   Use the constructor-injected `ILogger<>`, `IOptions<XConnectionStrings>`,
   `IStringLocalizer<SharedResource>`, and the DbContext or repositories. Log on entry and exit.
   On failure call `LogAndThrow(ex, _localizer["E781"].Value, "E781")`. Parameterised SQL only.
5. **Persistence** (writes through EF): entity in `Models/`, `DbSet` + `ToTable` in the context,
   `IRepository<T>` implementation in `Repositories/`, and its registration in `DILoader`.
6. **Controller action**: `[HttpPost] [Route("<area>/<action>")]` under the controller's
   `[Route("api/v1/...")]`. Same try/catch/finally shape as its neighbours. Return `ApiResponseWrapper`.
7. **Config**: any new key goes into `appsettings.json`, with an empty value for secrets.
8. **Docs**: run `python tools/gain-docgen/gain_docgen.py`, then add business meaning to
   `<Solution>/.ai/overview.md` if this is a new flow.

New handlers in an existing CQS project are auto-registered. New CQS projects are not (see standards → DI).

## Rules specific to A1

- One controller per area. Actions stay thin: map, dispatch, wrap. Business logic lives in handlers.
- Authentication: reuse what the controller already does (`ValidateToken()` in Gain.Integrations,
  `VerifyAccessTokenQuery` in RiverMobileApp). Never ship an action without the check its
  neighbours have.
- Return `IsSuccess=false` with an `IcsolException` code for business failures. Don't return a 200
  that carries an error string.
- Gain.Integrations takes calls from Salesforce and SAP (`api/v1/sf`, `SAPIntegrationController`).
  Treat every field as untrusted, and never change a route or a response shape without agreeing
  it with the external system's owner.

## Known variations (follow the local one, do not "fix" in passing)

| Topic | Gain.Integrations | MobileApp (CQS areas) |
|---|---|---|
| Validation | in handler (`new XValidator(_localizer).Validate(cmd)`) | `ValidationFilter<TDto>` at API |
| Write style | EF keyless result + `FromSqlRaw(EXEC proc ...)` (convert to `FromSqlInterpolated` when touched) | EF / Dapper |
| Options classes | one per domain (`LeadConnectionStrings`, `ProductConnectionStrings`...) over the same section | single `ConnectionStrings` |
