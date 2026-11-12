# Org standard: definition of done

There are no automated test projects yet, so "done" means all of the following. `/gain-dev:verify`
runs every check that can be automated and prints the rest as a checklist.

## Automated (must pass)

1. `dotnet build <solution>.slnx -c Release` finishes with no errors and no new warnings in the
   files you touched.
2. `dotnet list <solution>.slnx package --vulnerable --include-transitive` reports nothing new.
3. `python tools/gain-docgen/gain_docgen.py --check` passes. If it fails, run it without
   `--check` and commit the regenerated files.
4. No new SQL is built from values (compare `generated/contracts-and-risks.md` before and after).
   The count for files you touched must not go up.
5. If a test project exists for the solution: `dotnet test` passes.

## Reviewed (author confirms in the PR description)

- [ ] Followed the archetype recipe for the folder you changed (A1 / A2 / B).
- [ ] Every new config key is declared in `appsettings.json` (secrets with an empty value).
- [ ] If a queue payload, queue name, routing code or `ExternalSystemIntegrationConfigurationMapper`
      row changed: every solution listed in `.ai/system/generated/contracts.md` was checked.
- [ ] If a stored procedure or table changed: every user in the `data-map.md` reverse index was checked.
- [ ] Manual test evidence pasted in the PR: request + response (A1), or message + resulting
      `integration_response_details` row (A2), or before/after screenshot (B mobile flows).
- [ ] Narrative docs updated if behaviour changed: `gotchas.md` / `decisions.md` / `overview.md`.
