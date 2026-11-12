# Using Claude Code in {{REPO_NAME}}

Read sections 1-3 once; use section 4 day to day.

## 1. What is set up
- **Knowledge** - `CLAUDE.md` files and `.ai/`: this team's standards (mined from the code and confirmed), how each kind of unit is
  built (archetypes with recipes), and a pack per unit (purpose, flows, traps, decisions, generated catalogues).
- **Skills** - `.claude/skills/{{PREFIX}}-*`: commands that make Claude follow the team's process. They live in this repo; nothing to install.
- **Tools** - `tools/claude-kit/`: `docgen.py` (catalogues from code), `kit_check.py` (setup check), `export-db-objects.ps1` (SQL Server
  definitions){{TEMPLATE_LINE}}. CI: `.github/workflows/kit-docs-*.yml`.
- **Out of scope**: folders in `.ai/exclude-paths.txt` - skipped by the tools and blocked for Claude.

## 2. One-time setup per developer
1. Install Claude Code, Git, Python 3.10+{{STACK_TOOLS}}.
2. Clone, open a terminal at the repo root, run `python tools/claude-kit/kit_check.py` (expect 0 FAIL).
3. Start `claude` at the repo root; type `/{{PREFIX}}-` to see the skills.

## 3. Five habits
1. Start every task with a skill, not a blank prompt.
2. Name the unit and give the business detail (routes, screens, fields, who calls it). Answer Claude's questions instead of letting it guess.
3. Review the plan before it builds.
4. Finish with `/{{PREFIX}}-verify`.
5. When Claude gets something wrong because the docs are wrong or missing, fix the docs (`gotchas.md`, `decisions.md`, archetype recipe).

## 4. Skills
<!-- kit:skills-table -->
{{SKILLS_TABLE}}
<!-- /kit:skills-table -->

## 5. Keeping knowledge current
| What | When | How |
|---|---|---|
| `generated/` | every code change | `python tools/claude-kit/docgen.py`; CI `kit-docs-check` fails if stale |
| Narrative packs | every PR | `kit-docs-update` workflow proposes a `[docs-bot]` commit; review it |
| Stale packs | weekly | `kit-docs-drift` keeps one issue updated; fix with `/{{PREFIX}}-docs-refresh <unit>` |
| A unit without a pack | once | `/{{PREFIX}}-map-unit <unit>` |
| Kit itself | when the builder releases | a lead runs `/skill-builder:upgrade-kit` (keeps local edits) |

## 6. Rules that always apply
Excluded folders are off-limits · SQL values are parameters · no secrets in code, config, docs or prompts · legacy code follows its
own archetype · contracts between units change only via `/{{PREFIX}}-change-contract` (if installed) · never hand-edit `generated/`.
{{REPO_RULES}}

## 7. Troubleshooting
| Symptom | Fix |
|---|---|
| `/{{PREFIX}}-` shows nothing | Start Claude Code at the repo root; check `.claude/skills/` exists in your checkout |
| `kit-docs-check` fails | Run `python tools/claude-kit/docgen.py` and commit; for "SQL built from values" use parameters |
| Claude didn't follow a rule | Put the rule in the right `.ai` file (archetype recipe / standards / unit `gotchas.md`), or the unit's `CLAUDE.md` if it must always apply |
