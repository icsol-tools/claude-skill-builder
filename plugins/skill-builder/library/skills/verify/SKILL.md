---
name: {{PREFIX}}-verify
description: Run {{REPO_NAME}}'s definition-of-done checks for the units changed on this branch - build, tests, lint, vulnerable packages, generated-docs freshness, unsafe SQL / secrets in the diff, config keys - and print the manual checklist. Use before saying a change is done or opening a PR.
---

# Verify a change

Follow `.ai/standards/definition-of-done.md`. Report each check PASS / FAIL / SKIPPED (with reason) in a table at the end.
Never mark PASS what you did not run.

## 1. What changed
`git status --porcelain` and `git diff --name-only $(git merge-base HEAD origin/HEAD 2>/dev/null || git merge-base HEAD origin/main)...HEAD`.
Group files by unit (`.ai/kit/manifest.json` → `units`).

## 2. Automated checks per changed unit
Use the commands in `<unit>/.ai/unit.yaml` (`build`, `test`, `lint`) when present; otherwise:
- **.NET Core**: `dotnet build <sln|slnx> -c Release -nologo`; `dotnet test` if a test project exists;
  `dotnet list <sln|slnx> package --vulnerable --include-transitive`.
- **.NET Framework**: `msbuild <sln> /p:Configuration=Release /m` (find it with `vswhere -latest -find MSBuild\**\Bin\MSBuild.exe`
  on Windows). If MSBuild is not available, mark SKIPPED; do not claim it builds.
- **Frontend**: the unit's package manager (`npm ci` / `pnpm i --frozen-lockfile` / `yarn --frozen-lockfile` only if
  `node_modules` is missing), then `run lint`, `run build`, `run test -- --run` (vitest) or the configured test script;
  `npm audit --omit=dev` (report, don't auto-fix).
Then for the whole branch:
- `python tools/claude-kit/docgen.py --check`; if stale, run it without `--check` and tell the developer to commit the result.
- `python tools/claude-kit/kit_check.py`.
- **Diff rules**: new lines that build SQL from values (`"...SELECT..." +`, `$"... {x}"` with SQL), hard-coded credentials,
  new `dangerouslySetInnerHTML` / `bypassSecurityTrust*` / `eval`. Any hit is FAIL; show the line and the fix.
- **Config**: every new config/env key the diff reads exists in the unit's base config (`appsettings.json`, `Web.config`,
  `.env.example`, `environment.ts`) - see `generated/config.md` "read but not declared".
- **Contracts**: if the diff touches a shared payload, queue, route used by another unit, or a shared proc, point to
  `{{PREFIX}}-change-contract`.

## 3. Manual checklist
Print the "Reviewed" checklist from `definition-of-done.md` with applicable items ticked or explained, plus the exact manual test
(request/response, screen + steps, or message + resulting row).
