# Skill library

Generic procedures, installed into a repo as `.claude/skills/{{PREFIX}}-<name>/SKILL.md`.
They contain no repo knowledge. They read it from the repo's `.ai/` folder, which the builder
writes per repo (standards, archetype recipes, unit packs). Keep them that way: a fix here
reaches every repo on the next upgrade.

| Folder | Installed as | When |
|---|---|---|
| onboard, feature, fix, verify, docs-refresh, map-unit | `{{PREFIX}}-<name>` | always (core) |
| change-contract | `{{PREFIX}}-change-contract` | repo has more than one unit, queues, or frontend -> backend calls |
| new-service | `{{PREFIX}}-new-service` | repo has Icsol CQS .NET APIs (template in tools/claude-kit/templates) |
| _recipe | `{{PREFIX}}-<recipe-name>` (one per recipe the team picks) | generated from an archetype's "Recipe" section |
| _custom | `{{PREFIX}}-<name>` | any other repo-specific skill the team asks for |

Placeholders filled at install time: `{{PREFIX}}`, `{{REPO_NAME}}`. In `_recipe` and `_custom` the builder also
fills `{{SKILL_NAME}}`, `{{DESCRIPTION}}`, `{{ARCHETYPES}}`, `{{RECIPE_FILE}}`, `{{RECIPE_SECTION}}`, `{{BODY}}`.
