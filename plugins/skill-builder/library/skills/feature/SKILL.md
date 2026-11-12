---
name: {{PREFIX}}-feature
description: Plan and build a feature or enhancement in {{REPO_NAME}} the team's way - load the unit's standards and archetype, impact analysis across units, a plan to confirm, then build with the matching recipe, verify and update docs. Use for any add / change / enhance / support-X request.
argument-hint: "<what to build>"
---

# Feature or enhancement

## 1. Load context (always)
1. Find the unit(s) the request touches (`.ai/kit/manifest.json` → `units`). Never work in `.ai/exclude-paths.txt` folders;
   if the request is about one, stop and ask. If it crosses units (frontend + API, a queue message, a shared table), list all.
2. For each unit read `<unit>/.ai/unit.yaml` and work out the **archetype of the exact folder you will change**. Then read:
   - every file in `.ai/standards/` that applies to that stack (the team's rules, mined from this repo)
   - the archetype file(s) in `.ai/archetypes/` (flow, rules, recipes)
   - `<unit>/.ai/overview.md`, `gotchas.md`, `decisions.md`
   - `<unit>/.ai/generated/entry-points.md`, `data-map.md` or `contracts-and-risks.md` (search, don't paste)
3. Open the **2-3 closest existing examples** in the code (same controller / page / module). New code copies their shape.

## 2. Impact analysis - write it down
- Routes, DI registrations, routing tables, menus, config keys, env vars that change.
- Cross-unit contracts: `.ai/system/generated/contracts.md` (frontend → backend calls, shared payloads, queues, shared SQL).
- Stored procedures / tables that change and who else uses them (data-map reverse index). Export current definitions if `db/` lacks them.
- Traps from `gotchas.md` for this area.

## 3. Plan and confirm
Short plan: files to add/change (paths), DB scripts, config/env keys, the recipe you will follow, open questions.
**Wait for confirmation** unless told to go ahead. Ask for business rules you cannot see in code; never invent them.

## 4. Build with the recipe
Use the recipe for the folder's archetype: the matching `{{PREFIX}}-*` recipe skill in `.claude/skills/` if there is one,
otherwise the "Recipe" section of the archetype file. A brand-new unit: `{{PREFIX}}-new-service` if installed,
else ask. A change to anything shared between units: `{{PREFIX}}-change-contract` first (if installed).

While building:
- Match neighbouring code style, except where `.ai/standards/` says new code must differ (e.g. SQL parameters, no secrets).
- Don't refactor unrelated code; list improvements for the PR instead.
- Never read or print secret files or values (`.claude/settings.json` denies them).
- DB changes as re-runnable scripts in `<unit>/db/changes/<yyyyMMdd>-<name>.sql`.

## 5. Finish
1. `{{PREFIX}}-verify`.
2. `python tools/claude-kit/docgen.py` and include regenerated files.
3. Update the narrative pack where behaviour changed: `overview.md` (flow), `decisions.md` (business rules given, who/when),
   `gotchas.md` (new traps).
4. Draft the PR description: what and why, files by layer, DB scripts, config keys, cross-unit impact, manual test evidence needed.
