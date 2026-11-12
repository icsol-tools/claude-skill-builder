---
name: status
description: Report the Claude kit status of the current repository (installed version, skills, units without packs, stale docs, setup problems) and recommend the next action. Use to check a repo before or after setup, or when someone asks what state the Claude setup is in.
---

# Kit status

1. If `.ai/kit/manifest.json` is missing, say the repo has no kit. Offer `/skill-builder:setup-repo`, or run
   `python "<plugin>/scripts/scan_repo.py" --root . --stdout` to preview what setup would find. `<plugin>` is this plugin's folder,
   two levels above this file.
2. Otherwise, run `python tools/claude-kit/kit_check.py`, and compare the installed `kit_version` with `<plugin>/kit/VERSION`.
3. Summarise in at most 8 lines:
   - the installed version, and whether an upgrade is available
   - the number of skills
   - units with a full pack against units without one
   - FAILs, then the top WARNs
4. Then give the single most useful next action, such as `/skill-builder:upgrade-kit`, `/<prefix>-map-unit <unit>` or fixing a FAIL.
