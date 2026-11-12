# Knowledge base (`.ai/`) for {{REPO_NAME}}

What Claude Code and new developers read before changing code here. **New here? Read [`GUIDE.md`](GUIDE.md).**
Installed and maintained with skill-builder (kit {{KIT_VERSION}}); `kit/manifest.json` records what it manages.

| Layer | Where | Holds | Owner |
|---|---|---|---|
| Standards | `.ai/standards/` | The team's rules per stack, mined from this repo and confirmed | Tech leads (PR) |
| Archetypes | `.ai/archetypes/` | How each kind of unit is built here, with recipes | Tech leads |
| System | `.ai/system/` | How units connect; generated contracts | Script + tech leads |
| Unit packs | `<unit>/.ai/` | unit.yaml, overview, gotchas, decisions, evals, generated/ | Unit owners |
| Templates | `.ai/templates/` | Starting points for new packs | Kit |

Generated files (`generated/`) are rewritten by `python tools/claude-kit/docgen.py` and checked in CI. Everything else is edited by people (and
proposed by the docs-refresh skill on each PR). Excluded folders: `exclude-paths.txt`.
