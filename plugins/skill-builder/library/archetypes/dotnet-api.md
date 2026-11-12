# Archetype: .NET HTTP API (<!-- fill: variant, e.g. CQS handlers / MediatR / controllers + services / minimal API -->)

**Applies to:** <!-- fill: units and folder globs -->
**Read first:** `.ai/standards/` (dotnet conventions, SQL safety, definition of done).

## How it flows
```
HTTP -> <!-- fill: controller / endpoint group --> -> <!-- fill: auth (attribute, filter, middleware) -->
     -> <!-- fill: validation (FluentValidation / data annotations / in handler) -->
     -> <!-- fill: dispatch (ICommandDispatcher / IMediator.Send / service call) --> -> handler/service
     -> <!-- fill: data access (EF repository / Dapper / proc) -->
     <- <!-- fill: response envelope and status codes -->
Errors -> <!-- fill: exception type, error codes, global handler -->
```

## Rules for new code
<!-- fill from convention-miner: naming, layering, DI registration (what is automatic, what is manual), logging style,
error handling, validation placement, config access (IOptions vs IConfiguration), async rules. One line each with evidence. -->
- SQL values are always parameters (`.ai/standards/sql-safety.md`).
- Secrets never in appsettings.json; user-secrets locally, environment / vault on servers.

## Recipe: add-endpoint
1. DTO/request model in <!-- fill: folder, naming -->.
2. <!-- fill: command or query + result / MediatR request / service method --> in <!-- fill: project/folder -->.
3. Validator: <!-- fill: where and how registered -->.
4. Handler/service: <!-- fill: base interface, constructor dependencies, logging, error style -->.
5. Persistence: <!-- fill: entity, DbSet/ToTable, repository, registration --> (only for new tables).
6. Controller action / endpoint mapping: <!-- fill: route prefix and style, auth attribute, response wrapper -->.
7. Registration: <!-- fill: what must be added to Program/Startup/DI (handlers auto? validators manual?) -->.
8. Config keys in the base appsettings.json (empty values for secrets).
9. Copy from: <!-- fill: best existing example file -->.

## Recipe: add-entity
1. <!-- fill: entity location, naming, keyless vs keyed, migrations or DB-first scripts -->.
2. DB script in `<unit>/db/changes/<yyyyMMdd>-<name>.sql`, re-runnable.
3. <!-- fill: DbContext, repository, DI -->.

## Diagnosing
<!-- fill: where logs go, correlation ids, how errors surface to callers -->

## Known variations
<!-- fill: units/folders that do it differently - follow the local one -->
