---
name: {{PREFIX}}-docs-refresh
description: Bring {{REPO_NAME}}'s .ai knowledge packs up to date with the code - regenerate catalogues and update only the narrative sections affected by recent changes (a diff, a branch, or since last_mapped_commit). Use after a change, on request, when a pack is flagged stale, and from the kit-docs-update GitHub workflow.
argument-hint: "[unit folder] [base ref]"
---

# Refresh docs

## 1. Scope
- Units: the argument, or every unit with changed files in the diff.
- Base: the argument; else `last_mapped_commit` in `<unit>/.ai/unit.yaml`; else the default branch.
- `git diff --stat <base>...HEAD -- <unit>` and `git log --oneline <base>..HEAD -- <unit>`. Nothing changed → stop and say so.

## 2. Regenerate
`python tools/claude-kit/docgen.py` (all units, so system files stay consistent), then
`git diff --stat -- '*/.ai/generated' .ai/system/generated` shows what changed in the facts.

## 3. Update the narrative surgically
- New/removed endpoint, page, route, consumer, scheduler → `overview.md` flows and tables.
- New trap, workaround or failure mode in the diff or commit messages → `gotchas.md`.
- Business rule changes stated in commits/PR text → `decisions.md` with date and source.
- Cross-unit change → `.ai/system/system-map.md`. New folder/area → archetype map in `unit.yaml`.
Rules: edit only affected sections; keep reviewers' wording; never delete a gotcha/decision unless the code proves it no longer
applies (say why); mark inferences `(inferred - confirm)`; set `last_mapped_commit` to `git log -1 --format=%h -- <unit>`.

## 4. Report
Files changed, one line each, and the `(confirm)` items for reviewers. In CI: do not commit; the workflow does.
