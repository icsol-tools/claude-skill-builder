---
name: add-skill
description: Build one new repo-specific Claude Code skill in a repository that already has the Claude kit - interview for purpose and trigger, mine real examples from the code, draft it, review it against the code, and deploy it to .claude/skills with the guide and manifest updated. Use when a team says "we need a skill for X".
argument-hint: "<what the skill should help with>"
---

# Add a skill to a repository

Requires the kit (`.ai/kit/manifest.json`). If it is missing, use `/skill-builder:setup-repo`. `$BUILDER` is this plugin's folder
(two folders above this file).

1. **Understand the need** (one question round, at most 4 questions):
   - What task does it do, and who runs it? Get one or two example requests, exactly as a developer would type them.
   - Which unit(s) and archetype(s)? Read `.ai/kit/manifest.json` → `units`.
   - Is it a **recipe** (build something step by step in an archetype) or **custom** (a process, such as release notes, a migration
     or a data fix)?
   - What does "done" look like, and what must it never do?
2. **Check for overlap**: read the existing `.claude/skills/*/SKILL.md`. If an existing skill already covers this, propose extending
   it instead, and stop if the user agrees.
3. **Mine examples**:
   - Find 2 or 3 places in the code where this task was done before. Use `git log -S`/`--grep`, `generated/entry-points.md`, or a
     search.
   - Note the files touched, the registration points, the tests and the traps.
   - For a recipe, also update or add the matching `Recipe:` section in `.ai/archetypes/<archetype>.md` (the skill points there).
4. **Draft** `.claude/skills/<prefix>-<name>/SKILL.md` from `$BUILDER/library/skills/_recipe/SKILL.md` or `_custom/SKILL.md`:
   - The name is lower-case with hyphens and starts with the repo prefix.
   - The `description` says when to use the skill, in under about 300 characters.
   - The steps are concrete for this repo: real folders, real example files.
   - It always ends with `<prefix>-verify` and the docgen step.
5. **Review**: run the `skill-reviewer` subagent on the draft and fix its blockers. Then walk one of the user's example requests
   through the skill, as a plan only, and show the plan to the user.
6. **Deploy on confirmation**:
   - Write the file.
   - Add the name to `.ai/kit/manifest.json` → `skills`.
   - Add a row to the skills table in `.ai/GUIDE.md`, between the `kit:skills-table` markers.
   - Run `python tools/claude-kit/kit_check.py`.
7. Tell the user how to invoke it (`/<prefix>-<name> ...`), and suggest adding an eval for it to the unit's `.ai/evals.md`.
