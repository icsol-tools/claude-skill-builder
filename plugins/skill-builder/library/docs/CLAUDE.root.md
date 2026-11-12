# {{REPO_NAME}}

{{REPO_SUMMARY}}

## Before changing code
1. Find the unit you are working in (`.ai/kit/manifest.json` → `units`) and read `<unit>/CLAUDE.md` and `<unit>/.ai/unit.yaml`.
2. Load the archetype file for the folder you will change (`.ai/archetypes/`) and the standards for its stack (`.ai/standards/`).
3. Anything shared between units (API routes used by a frontend, payloads, queues, shared SQL) → `.ai/system/system-map.md`.

Skills: `/{{PREFIX}}-onboard`, `/{{PREFIX}}-feature`, `/{{PREFIX}}-fix`, `/{{PREFIX}}-verify` (+ recipe skills in `.claude/skills/`).
How-to guide: `.ai/GUIDE.md`.

## Always
- Never read or change anything in the folders listed in `.ai/exclude-paths.txt`.
- SQL values are always parameters; no secrets in code, config, docs or prompts (`.ai/standards/`).
- Never edit `**/.ai/generated/**` by hand: run `python tools/claude-kit/docgen.py`.
- Plan and confirm before large changes; run `/{{PREFIX}}-verify` before saying a change is done.
{{REPO_RULES}}
