---
name: upgrade-kit
description: Upgrade the Claude kit in the current repository to this skill-builder version - replaces kit-managed files the team has not edited, saves new versions next to edited ones and helps merge them, never touches repo-owned knowledge. Use after a skill-builder release, or when kit_check reports an old kit.
---

# Upgrade the kit in a repository

`$BUILDER` is this plugin's folder (two folders above this file). Requires `.ai/kit/manifest.json`.

1. Show the versions: the installed kit (`kit_version` in the manifest) and this builder's kit (`$BUILDER/kit/VERSION`). Summarise
   what changed if `$BUILDER/CHANGELOG.md` covers it.
2. Recommend a branch `chore/claude-kit-<version>`, and create it if the user agrees.
3. Dry run: `python "$BUILDER/scripts/install_kit.py" --repo . --upgrade --dry-run`. Show the UPDATE, CONFLICT and OBSOLETE lines,
   and **ask for confirmation**.
4. Upgrade: `python "$BUILDER/scripts/install_kit.py" --repo . --upgrade`.
5. **Conflicts**: these are files the team changed. For each `<file>.kit-new`:
   - Show what the team changed relative to the kit version, and what the new kit changed.
   - Propose a merged file that keeps the team's intent and takes the kit's fixes.
   - Apply it once the user agrees, then run `python "$BUILDER/scripts/install_kit.py" --repo . --accept <file>`. This records the
     file as team-customised, deletes the `.kit-new`, and offers future kit changes to that file as a new `.kit-new` instead of
     overwriting it.
6. **OBSOLETE** files: check that nothing references them (search the repo), then delete them if the user agrees.
7. Repo-owned files are never changed by the upgrade: `.ai/standards`, `.ai/archetypes`, unit packs, recipe skills and `CLAUDE.md`.
   If the release notes mention template improvements, offer to apply them to those files as a separate, reviewed step.
8. Run `python tools/claude-kit/docgen.py` and `python tools/claude-kit/kit_check.py`, and report the result. Commit only if asked.
