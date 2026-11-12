---
name: setup-repo
description: Set up Claude Code for the current repository end to end - scan the code (.NET Core, .NET Framework, React/Vite, Next.js, Angular), interview the team about scope, standards and which skills they need, show a plan, and on confirmation deploy repo-specific skills, knowledge packs, doc tools and CI into the repo. Use when a repo has no Claude kit yet, or to redo one.
argument-hint: "[optional: units or folders to focus on]"
---

# Set up a repository with the Claude kit

You are deploying a self-contained Claude Code setup **into this repository**: skills in `.claude/skills/`, knowledge in `.ai/`
and `CLAUDE.md` files, tools in `tools/claude-kit/`, CI in `.github/workflows/`. After setup the repo needs nothing from this
plugin. Teams differ: **discover this repo's conventions from its code and confirm them with the team. Never impose another
team's standards.**

**Builder files.** This skill lives in `<plugin>/skills/setup-repo/`. Everything it uses is under `<plugin>` (two folders up from
this file; Claude Code shows the skill's base directory when it loads). Below, `$BUILDER` means that plugin folder:
`$BUILDER/scripts/` (scanner, installer), `$BUILDER/library/` (skills, archetype starters, standards, doc templates,
`examples/gain-core-services/` = a finished reference repo), `$BUILDER/kit/` (tools and workflows copied into repos).

**Ground rules for the whole run**
- Nothing is written to the repo before the plan is confirmed, except `.ai/kit/scan.*` and `.ai/kit/plan.*`.
- Never read secret files or print config values. The scanner reports key names only; keep it that way.
- Ask with the question tool, at most 4 questions per round, each with a recommended option first.
- Use the task list: one item per phase below.

## Phase 0 - Preflight
1. Repo root: `git rev-parse --show-toplevel`; work from there. Python 3.10+ (`python --version`, or `py` on Windows).
2. `git status --porcelain`: if there are uncommitted changes, recommend committing or stashing first. Propose a branch
   `chore/claude-kit` and create it if the user agrees.
3. Existing setup:
   - `.ai/kit/manifest.json` exists → the kit is already installed. Offer `/skill-builder:upgrade-kit` or
     `/skill-builder:add-skill` instead, and stop unless the user wants a full redo.
   - An existing `CLAUDE.md`, `.ai/`, `.claude/` or a plugin-based setup like the Gain-Core-Services POC → keep their content. The
     installer never overwrites files it did not create; you merge the kit sections into them in Phase 5. Existing
     `.ai/archetypes`, `.ai/standards` and `<unit>/.ai/` packs are reused as the starting point instead of re-mining.
   - **Migrating a POC setup** (for example Gain-Core-Services with `tools/claude/gain-dev`, `tools/gain-docgen`, `docs-*.yml`
     workflows and a marketplace entry in `.claude/settings.json`), add these clean-up items to the plan in Phase 5:
     - Map the old skills onto kit skills with the same prefix (`gain-dev:feature` → `gain-feature`). Old recipe skills become
       recipe skills.
     - Rename `<unit>/.ai/solution.yaml` to `unit.yaml`; the kit reads both.
     - After the kit is verified, with the user's confirmation: remove the old workflows, generator folder, plugin folder,
       `.claude-plugin/marketplace.json`, and the plugin entries in `.claude/settings.json`, so CI and skills don't run twice.
     - Resolve each `.kit-new` conflict by merging the kit template into the existing file, then run
       `install_kit.py --accept <file>`.

## Phase 1 - Scan
```
python "$BUILDER/scripts/scan_repo.py" --root .
```
Read `.ai/kit/scan.md` (and `scan.json` for details). Show the user a short summary: units, stack and version, proposed
archetype per unit with evidence, tests yes/no, activity, suggested exclusions, and risks (secret-looking config by file and key
name only, SQL built from values, hard-coded credentials).

## Phase 2 - Interview: scope and identity (one round)
1. **Excluded folders**: multi-select from the suggested ones (retired-looking names, inactive units), plus "other". Excluded folders
   get no docs and are blocked for Claude.
2. **Units in scope**: confirm the unit list. If there are more than ~12 units, ask which to set up fully now; the rest get generated
   docs only and are mapped later.
3. **Skill prefix and repo name**: propose a 2-6 letter prefix from the repo/product name (skills become `/<prefix>-feature` and
   so on), and a one-line description of what the repo is for.
4. **Archetypes**: for every unit whose proposal is not `high` confidence, or that has several, ask which archetype each folder
   follows. For legacy archetypes, ask the policy: keep legacy and patch in place, or migrate when touched.

Re-run the scanner with `--exclude` for each chosen exclusion if the list changed.

## Phase 3 - Mine the team's conventions
Group the in-scope units by stack (for example ".NET Core APIs", ".NET Framework web", "React+Vite", "Next.js", "Angular").
Start one `convention-miner` subagent **per stack, in parallel**. Give each the repo root, the stack name, its unit paths and
`.ai/kit/scan.md`. If the repo already has `.ai/standards/` or `.ai/archetypes/`, give those too and ask the miner to confirm or
flag drift instead of starting from zero.

Then confirm with the team, one round per stack (max 4 questions each):
- Show the **rules for new code** found (with consistency counts) as one list and ask them to confirm or correct it.
- For each **inconsistent** topic, ask which variant new code must follow. Offer the variants as options and recommend the majority one.
- For each **observed but not recommended** pattern (string-built SQL, secrets in config, no auth on endpoints...), confirm that new
  code must not copy it. SQL parameters and no-secrets are non-negotiable kit rules; say so, and don't ask to drop them.
- Ask for anything the code can't show: review rules, branch/release process, required approvals.

## Phase 4 - Choose the skills
Propose the skill set and ask with one multi-select question (and a free-text "other skills you want"):
- **Core** (always): `<prefix>-onboard`, `-feature`, `-fix`, `-verify`, `-docs-refresh`, `-map-unit`.
- **Optional**: `<prefix>-change-contract` (recommend it when there are several units, queues, or frontend → backend calls in
  `.ai/kit/scan.md`); `<prefix>-new-service` (only when the repo has Icsol CQS .NET APIs: the template is Icsol-based).
- **Recipe skills**: for each in-scope archetype, the recipes listed in `$BUILDER/library/archetypes/index.json`, named
  `<prefix>-<recipe>`, for example `dms-add-endpoint` or `dms-add-page`. If two archetypes share a recipe name, either merge them
  into one skill that branches by archetype, or suffix them (`-add-endpoint-fx`). Decide this in the plan.
- **Custom skills** the team asks for: capture the purpose and trigger for each. Each one is built in Phase 5 with the
  `add-skill` method.
Also ask: GitHub workflows yes or no (recommend yes when `scan.repo.git.host` is `github`), the default branch, and whether the DB
export tool is wanted (recommend it when the units use SQL Server).

## Phase 5 - Plan, confirm, deploy
1. Write `.ai/kit/plan.json` for the installer:
   ```json
   {"prefix": "dms", "repo_name": "<name>", "default_branch": "main", "excludes": ["Archive"],
    "units": [{"path": "src/Api", "kind": "dotnet-solution", "archetypes": ["dotnet-cqs-api"]}],
    "skills": ["change-contract"], "generated_skills": ["dms-add-endpoint", "dms-add-page"],
    "include_db_export": true, "include_service_template": false, "include_workflows": true, "has_dotnet_framework": false}
   ```
   `skills` lists only the optional library skills (`change-contract`, `new-service`). The core skills are always installed.
   `generated_skills` lists the recipe and custom skills you will write.
2. `python "$BUILDER/scripts/install_kit.py" --repo . --dry-run`, then write `.ai/kit/plan.md`. It holds the files the installer will
   create, the files you will write (standards, archetypes, recipe skills, CLAUDE.md files, unit packs), the files it will merge,
   any conflicts, and the decisions from the interview. Show a short summary and **ask for confirmation**. Stop here if it isn't given.
3. Deploy the kit: `python "$BUILDER/scripts/install_kit.py" --repo .`
4. Write the repo-owned knowledge. Use the evidence from Phase 3, and reach the depth of `$BUILDER/library/examples/gain-core-services/`:
   - `.ai/standards/<stack>-conventions.md` for each stack, from `$BUILDER/library/standards/conventions.template.md`.
   - Fill every `<!-- fill -->` in the seeded standards (`secrets-and-config.md`, `frontend-security.md`, `definition-of-done.md`)
     with this repo's facts. Delete lines that don't apply.
   - `.ai/archetypes/<archetype-id>.md` for each in-scope archetype, from its starter in `$BUILDER/library/archetypes/`
     (`index.json` → `starter`) and following `$BUILDER/library/archetypes/_FORMAT.md`. Every recipe gives exact folders, base
     classes, registration points and the existing file to copy.
   - Seeded docs: fill the `{{...}}` placeholders in `CLAUDE.md` (merge into the existing file if there was one), `.ai/GUIDE.md`
     (the skills table between the `kit:skills-table` markers lists every installed skill with an example prompt), and
     `.ai/system/system-map.md` (mermaid diagram of the units and external systems, plus the contracts table).
5. Write the recipe and custom skills: `.claude/skills/<prefix>-<name>/SKILL.md`, from `$BUILDER/library/skills/_recipe/SKILL.md`
   (or `_custom`).
   - Fill every placeholder. `{{BODY}}` holds the numbered steps of the archetype's recipe, made concrete for this repo, and
     `{{CHECKLIST}}` holds the checks that catch the usual misses: registration, sibling lists, config, tests.
   - The `description` says when to use the skill, under about 300 characters.
   - Use `$BUILDER/library/examples/gain-core-services/recipe-skill-add-subprocess.md` as the bar for concreteness.
6. Units:
   - Run `python tools/claude-kit/docgen.py`.
   - For each in-scope unit, write `<unit>/.ai/unit.yaml` and `<unit>/CLAUDE.md` from `.ai/templates/`. Fill in the archetype per
     folder, the build/test/lint/run commands (from `scan.json`: csproj, sln, package.json scripts), and owners (top committers from
     the scan, as suggestions to confirm).
   - Ask whether to fully map one or two pilot units now with the `<prefix>-map-unit` procedure. Recommend the most active unit.
     The others are mapped later.

## Phase 6 - Review and check
1. Start the `skill-reviewer` subagent on everything you wrote in Phase 5 (skills, archetypes, standards, CLAUDE.md files).
   Fix every blocker, and the "should" items where you agree.
2. Run `python tools/claude-kit/docgen.py --check` and `python tools/claude-kit/kit_check.py`. Fix FAILs until it shows 0 FAIL.
   Remaining WARNs, such as owners still TODO or units without a pack, are reported, not hidden.
3. Smoke test: for one recipe skill, write the plan it would produce for a realistic small task in this repo. Check the plan names
   real files, the right registration points and the right example. Fix the recipe if it doesn't.

## Phase 7 - Hand over
Tell the user:
- what was installed, by layer
- the open `(confirm)` items, and which owner should answer each
- the next steps:
  - commit on the branch
  - open a PR titled `chore: Claude kit`
  - add the `ANTHROPIC_API_KEY` secret and the Claude GitHub App if the workflows were installed
  - share `.ai/GUIDE.md` with the team
  - map the remaining units with `/<prefix>-map-unit`

Commit only if the user asks. Never push without being asked.
