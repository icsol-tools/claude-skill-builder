---
name: {{PREFIX}}-new-service
description: Create a brand-new Icsol CQS .NET API solution in {{REPO_NAME}} from the kit template - scaffold API + CQS projects, auth, config, starter knowledge pack, build, then add the first endpoints. Use when someone wants a new API/service/solution, not an endpoint in an existing one.
argument-hint: "<Name, e.g. Company.Area.API> <what it is for>"
---

# Create a new API solution

An endpoint in an **existing** unit is `{{PREFIX}}-feature`, not this skill.

1. **Agree the basics** (one message): name (dotted PascalCase ending `.API`), purpose, folder (default: where the repo's other
   services live), callers and authentication (template ships a fail-closed `X-Api-Key` middleware; replace if callers need
   another scheme and record it in `decisions.md`), databases, first endpoints, whether it triggers integrations.
2. **Scaffold**:
   `powershell -NoProfile -ExecutionPolicy Bypass -File tools/claude-kit/templates/new-service.ps1 -Name <Name> -Purpose "<purpose>" -Folder <folder>`
   (refuses to overwrite; picks a free local port and a user-secrets id).
3. **Adapt**: `ConnectionStrings` (properties + empty appsettings keys + `db-map.json`), auth, `.ai/unit.yaml` owners/depends_on,
   `overview.md`, `decisions.md`. Rename `.ai/solution.yaml` to `.ai/unit.yaml` if the template created the former.
4. **Build**: `dotnet build <folder>/<Name>/<Name>.slnx -c Release` → 0 errors.
5. **First endpoints**: follow the API archetype recipe in `.ai/archetypes/` (or the `{{PREFIX}}-add-endpoint` skill) for each,
   using `HealthController` + `GetHealthQueryHandler` as the shape.
6. **Finish**: local run instructions (user-secrets, `dotnet run`, `/api/v1/health`), `python tools/claude-kit/docgen.py`,
   add the unit to `.ai/kit/manifest.json` → `units` (run `python tools/claude-kit/kit_check.py` to confirm), `{{PREFIX}}-verify`.
