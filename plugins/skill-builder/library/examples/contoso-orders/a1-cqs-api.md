# Archetype: dotnet-cqs-api (Contoso.Orders.API)

## How it flows
`Controller` → `ICommandDispatcher` / `IQueryDispatcher` → `XxxCommandHandler` / `XxxQueryHandler` → repository (Dapper) → SQL Server `Orders` DB.
Responses are wrapped in `ApiResponse<T>` by `ApiResponseWrapperFilter`. Errors throw `AppException(code)`; `ExceptionMiddleware`
maps them to 4xx/5xx and a localised message from `Resources/SharedResource.resx`.

| Layer | Folder | Example to copy |
|---|---|---|
| Controller | `Contoso.Orders.API/Controllers/V1/` | `OrdersController.cs` |
| Command + handler | `Contoso.Orders.CQS/Commands/<Feature>/` | `Commands/CancelOrder/CancelOrderCommand.cs`, `CancelOrderCommandHandler.cs` |
| Query + handler | `Contoso.Orders.CQS/Queries/<Feature>/` | `Queries/GetOrder/GetOrderQuery.cs`, `GetOrderQueryHandler.cs` |
| DTOs | `Contoso.Orders.Model/Dto/` | `OrderDto.cs` |
| Registration | `Contoso.Orders.API/DILoader.cs` → `RegisterHandlers()` | |
| Tests | `Contoso.Orders.Tests/Handlers/` | `CancelOrderCommandHandlerTests.cs` |

## Rules for new code (confirmed with the team)
- One command or query per file; the handler sits next to it. Handlers implement `ICommandHandler<TCommand, TResult>` or `IQueryHandler<TQuery, TResult>`.
- Controllers contain no logic: validate the route/body, dispatch, return. Route prefix `api/v1/<resource>`.
- SQL only through Dapper with parameters (`new { OrderId = id }`). Never interpolate values. Stored procedures are called with `CommandType.StoredProcedure`.
- Config through `IOptions<XxxSettings>` bound in `DILoader`; no `IConfiguration["..."]` in handlers.
- Every handler gets at least one happy-path and one failure test (xUnit + NSubstitute).

## Recipe: add-endpoint
1. Decide command (changes state) or query (reads). Name it `<Verb><Noun>Command` / `Get<Noun>Query`.
2. Create the folder `Contoso.Orders.CQS/Commands/<Verb><Noun>/` and copy `CancelOrder/` as the starting point.
3. Put request/response DTOs in `Contoso.Orders.Model/Dto/`; reuse an existing DTO if the shape matches.
4. Write the handler. Data access goes in `Contoso.Orders.CQS/Repositories/OrderRepository.cs` (add a method; parameters only).
5. Register the handler in `DILoader.RegisterHandlers()` - the API starts without it but fails at the first call with `No handler registered`.
6. Add the action to the controller in `Controllers/V1/`, with `[ProducesResponseType]` for 200 and 400.
7. New error? Add the code to `ErrorCodes.cs` and the message to `SharedResource.resx` (and `SharedResource.ar.resx`).
8. Tests in `Contoso.Orders.Tests/Handlers/`. Run `dotnet test services/Contoso.Orders.sln`.
9. Update `.ai/` if the endpoint is a new contract: `services/Contoso.Orders.API/.ai/overview.md` → Contracts.

## Recipe: add-entity
1. Table change as a script in `db/changes/<yyyymmdd>-<name>.sql` (idempotent: `IF NOT EXISTS`).
2. Model in `Contoso.Orders.Model/Entities/`, repository methods in `Repositories/`, then follow add-endpoint for the API.

## Diagnosing
- 500 with `No handler registered for ...` → step 5 was missed.
- Message key shows instead of text → missing `.resx` entry.
- Works locally, fails in test env → setting missing from the environment's config; check `appsettings.json` key names only.

## Known variations
- `Controllers/Legacy/ReportsController.cs` calls the repository directly (pre-CQS). Leave it; don't copy it.
