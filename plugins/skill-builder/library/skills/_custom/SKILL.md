---
name: {{SKILL_NAME}}
description: {{DESCRIPTION}}
---

# {{TITLE}}

{{BODY}}

## Always
- Load the unit's context first: `<unit>/.ai/unit.yaml`, the archetype file(s) it names, `.ai/standards/`, `gotchas.md`.
- Never touch folders in `.ai/exclude-paths.txt`, never read secret files, never invent business rules - ask.
- Finish with `{{PREFIX}}-verify` and `python tools/claude-kit/docgen.py`.
