# Standard: definition of done ({{REPO_NAME}})

`{{PREFIX}}-verify` runs every check that can be automated and prints the rest.

## Automated (must pass)
1. Build: <!-- fill per stack: dotnet build / msbuild / npm run build --> with no new warnings in touched files.
2. Tests: <!-- fill: dotnet test / npm test / ng test --> when the unit has them.
3. Lint/format: <!-- fill: eslint / prettier / dotnet format, if the team uses them -->.
4. Vulnerable packages: `dotnet list package --vulnerable --include-transitive` / `npm audit --omit=dev` - nothing new.
5. `python tools/claude-kit/docgen.py --check` and `python tools/claude-kit/kit_check.py` pass.
6. No new SQL built from values, hard-coded credentials, or unsanitised raw HTML in the diff.

## Reviewed (author confirms in the PR)
- [ ] Followed the archetype recipe for the folder changed.
- [ ] New config/env keys declared in the base config (secrets empty / in .env.example by name only).
- [ ] Cross-unit contracts checked (`.ai/system/generated/contracts.md`) if routes, payloads, queues or shared SQL changed.
- [ ] Manual test evidence in the PR: request + response, screen + steps, or message + resulting row.
- [ ] Narrative docs updated if behaviour changed (`overview.md` / `gotchas.md` / `decisions.md`).
<!-- fill: team-specific items (code review rules, release notes, migrations) -->
