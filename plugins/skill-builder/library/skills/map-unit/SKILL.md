---
name: {{PREFIX}}-map-unit
description: Create or fully rebuild the .ai knowledge pack for one unit (solution or frontend app) of {{REPO_NAME}} - generated catalogue, unit.yaml with archetype per folder, overview / gotchas / decisions / evals drafts and CLAUDE.md - ready for owner review. Use once per unit, after a big refactor, or when a pack is missing.
argument-hint: "<unit folder>"
---

# Map a unit

Output: `<unit>/.ai/` per `.ai/README.md`, delivered as a PR the unit's owners review. Do not change code.

1. **Generated layer**: `python tools/claude-kit/docgen.py --solution <unit>` (works for frontends too), then read
   `generated/overview.md` and `entry-points.md`.
2. **Database (backend units with SQL Server)**: if `<unit>/db/` is empty, ask the developer to fill `<unit>/.ai/db-map.json`
   (connection key → database name, names only) and run `tools/claude-kit/export-db-objects.ps1`, or continue without it.
3. **Analyse in parallel**: start the `unit-mapper` subagent (flows, conventions, deviations from `.ai/archetypes/`, traps) and,
   when `db/` has definitions, the `db-mapper` subagent.
4. **Write the pack** from the templates in `.ai/templates/`:
   - `unit.yaml`: archetype per folder/glob (every controller, page area, hosted service matches exactly one), owners (ask),
     build/test/lint/run commands, `last_mapped_commit`.
   - `overview.md`: purpose, callers/calls, main flows end to end with paths, table of endpoints/pages/codes with business meaning.
   - `gotchas.md`, `decisions.md` (business decisions found in code comments, marked `(from code comment - confirm)`), `evals.md`
     (3-5 realistic tasks with must-touch / must-not / pass-if).
   - `<unit>/CLAUDE.md` from `.ai/templates/CLAUDE.unit.md`, under 40 lines.
   Mark anything inferred `(inferred - confirm)`.
5. **Independent review**: run the `pack-reviewer` subagent; fix or mark every unsupported claim.
6. **Hand over**: list the files, the `(confirm)` items for owners, and the PR title `docs(<unit>): knowledge pack`.
