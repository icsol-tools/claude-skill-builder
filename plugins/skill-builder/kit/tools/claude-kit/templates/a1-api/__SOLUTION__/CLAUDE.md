# __SOLUTION__

__PURPOSE__
Archetype: A1 CQS HTTP API. See `.ai/solution.yaml`.

Read before changing code: `.ai/overview.md`, `.ai/gotchas.md`, `.ai/decisions.md`, then the repo-root
`.ai/archetypes/a1-cqs-api.md` and `.ai/standards/`. Facts: `.ai/generated/`.

Build: `dotnet build __SOLUTION__.slnx -c Release`
Run:   `dotnet run --project __PREFIX__.API` (Swagger at /swagger in Development)

Solution-specific rules:
- New endpoints: `the `{{PREFIX}}-add-endpoint` skill`. Copy the shape of `HealthController` / `GetHealthQueryHandler`.
- Every request except `Security:AnonymousPaths` needs header `X-Api-Key` (`Middleware/ApiKeyMiddleware.cs`). Keys come from user-secrets or server environment, never appsettings.json.
- Validation runs inside handlers (`new XValidator(_localizer).Validate(command)`).
