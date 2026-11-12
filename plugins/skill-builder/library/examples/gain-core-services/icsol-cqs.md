# Org standard: Icsol CQS (archetypes A1 and A2)

Applies to every folder `solution.yaml` marks as A1 or A2. Legacy BA/DA code (B) has its own
rules in `.ai/archetypes/b-legacy-ba-da.md`. Wherever this file says "observed", it describes
what the code does today. "Rule" means what new or changed code must do.

## Building blocks (from the internal NuGet packages)

| Package | What we use from it |
|---|---|
| `Icsol.Infrastructure` | `ICommandHandler<TCommand>`, `IQueryHandler<TQuery,TResult>`, `BaseCommand` / `BaseQuery<T>` (carry `IsSuccess`), `ICommandDispatcher` / `IQueryDispatcher` (`HandleAsync<...>`), `IRepository<T>` (`Create`, `FindById`, `Update(id, model, isDetached)`, `Delete`) |
| `Icsol.Common` | `ApiResponse`, `ApiResponseWrapper<T>`, `IcsolException` + `ExceptionType`, `LogAndThrow` logger extension, `ConfigureExceptionHandler<T>()`, RabbitMQ (`RabbitMQConnectionProvider`, `RabbitMQPublisher`, `RabbitMQConsumer`), alerts (`AddAlertsExtensions`) |
| `Icsol.GlobalizationResources` | `SharedResource` + `IStringLocalizer<SharedResource>` for error texts by code, `AddDataAnnotationsGlobalization`, `UseGlobalizationHandler` |
| `Icsol.Communication` | Email / Amazon SES internal alerts |

Do not re-implement anything these packages already provide. If a package is missing something,
raise it with the package owners rather than copying code into a solution.

## Solution shape

- `<Name>.API` (or `.APIs`) is the host. It contains `Program.cs`, `DILoader.cs`, `Controllers/`,
  `Dto/`, `BackgroundServices/` and `appsettings*.json`.
- `<Name>.CQS` (one or more class libraries) holds `Commands/`, `Queries/`, `Context/` (EF DbContexts),
  `Models/` (EF entities), `Repositories/`, `Helpers/` (incl. `ConnectionStrings` options class),
  `Validators/`, and optionally `QueuePayload/`.
- Multi-domain APIs split CQS by domain (`Gain.Lead.CQS`, `Gain.Product.CQS`, ...). Add new code to the
  domain project it belongs to. Create a new project only for a genuinely new domain.

## Dependency injection (`DILoader`)

- Command and query handlers are registered **automatically**, by reflection, from each assembly
  passed to `AddCommandQueryHandlers(services, "<Assembly>")`. A new handler in an existing CQS
  project needs no registration. A **new CQS project** needs a new `AddCommandQueryHandlers` line
  and a `ProjectReference` from the API project.
- Everything else is registered **by hand** in `DILoader`: repositories (`IRepository<T>`),
  DbContexts (`AddDbContext<T>(... GetConnectionString("<Key>"))`), domain services, validators,
  `ValidationFilter<T>`, hosted services, `Configure<TOptions>` sections and HttpClients.
- Lifetimes observed: handlers, repositories and domain services are scoped. RabbitMQ connection
  providers are singletons. Hosted services must create a scope (`IServiceScopeFactory.CreateScope()`)
  before resolving scoped services.

## Data access

- **Reads**: Dapper on a `SqlConnection` built from the `ConnectionStrings` options class
  (`options.Value.<Key>ConnectionString`). Use inline SQL for simple lookups and `EXEC <proc>` or
  `commandType: CommandType.StoredProcedure` for anything a proc already does.
- **Writes**: EF Core through `IRepository<T>` + `SaveChangesAsync()` on the owning DbContext, or
  a stored procedure.
- Cross-database three-part names (`Presale.dbo.Oppurtunity`, `TSCommon.dbo.Branch`) are normal
  here. Keep the database, schema and table spelling exactly as the database has it, including
  existing typos such as `Oppurtunity`.
- **Rule:** every value goes into SQL as a parameter. See `sql-safety.md`. This is the one place
  where new code must not copy the surrounding code if the surrounding code concatenates.

## Logging (NLog through `ILogger<T>`)

- Observed: every handler and action logs entry and exit (`Entering {Class}.{Method}` /
  `Exiting ...`), plus `LogDebug` around inner steps.
- **Rule:** use structured templates (`"... ReferenceSlno: {ReferenceSlno}"`), not string
  concatenation or `$"..."`, for new log lines. Always include the business key: `ReferenceSlno`,
  `SubProcessCode`, `FranchiseSlno`, `UID` or the document number.
- Never log secrets, tokens, passwords or full request payloads that contain personal data, unless
  the solution already stores them deliberately (for example `integration_response_details`).

## Errors

| Situation | A1 (HTTP API) | A2 (queue worker) |
|---|---|---|
| Invalid input / business rule | `throw new IcsolException(_localizer["E741"]..., "E741", ExceptionType.INVALID_DATA_ERROR)` | Return a failure result (`Status=false`, `FailureStage=PayloadBuild` or `DataFetch`). Never throw out of a consumer |
| Unexpected exception in a handler | `_logger.LogAndThrow(ex, _localizer["E781"].Value, "E781")`. The global `ConfigureExceptionHandler` turns it into a response | Catch, log, set `IsSuccess=false`, return. The consumer persists the failure and ACKs |
| Response | `new ApiResponseWrapper<ApiResponse>(response, HttpStatusCode.OK)` with `response.AddData(...)` and `response.IsSuccess` | n/a |

Error codes come from `SharedResource` in `Icsol.GlobalizationResources`. Observed: `E741` means
invalid or missing data and `E781` means a processing error. Reuse existing codes. Ask before
inventing a new one, because it has to be added to the shared package.

## Validation

- FluentValidation `AbstractValidator<T>`, with messages and `.WithErrorCode("E741")`.
- Two placements are in use. Follow the one the solution already uses:
  - **In the handler** (Gain.Integrations): `new XCommandValidator(_localizer).Validate(command)`,
    then throw `ValidationException` when it is invalid.
  - **At the API** (Gain.MobileApp.Integrations, RiverMobileApp area): register
    `IValidator<TDto>` + `ValidationFilter<TDto>` in `DILoader` and put
    `[ServiceFilter(typeof(ValidationFilter<TDto>))]` on the action.

## Configuration

- Read options through `IOptions<T>` / `services.Configure<T>(GetSection(...))` in new code.
  `configuration["Key"]` is acceptable in hosted services, where it is the observed style.
- Every key the code reads must exist in `appsettings.json`, with an empty value if it is a secret.
  `generated/config.md` lists keys that are read but not declared.
- **Secrets never go in `appsettings*.json`.** Use user-secrets locally and the server's environment
  or vault in deployment. Claude is denied read access to `appsettings.Development.json`.

## Naming

- `<Verb><Thing>Command` + `<Verb><Thing>CommandHandler`; `Get<Thing>Query` + `Get<Thing>QueryHandler`
  + `<Thing>Result` / `<Thing>Details` / `<Thing>QueryResult` (match the project's existing suffix).
- One class per file, and the file name equals the class name.
- Routes are lower-case and versioned: `api/v1/<area>/<action>`.
