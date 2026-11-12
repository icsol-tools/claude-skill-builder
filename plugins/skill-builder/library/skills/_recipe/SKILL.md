---
name: {{SKILL_NAME}}
description: {{DESCRIPTION}}
argument-hint: "<unit> <what to add or change>"
---

# {{TITLE}}

Applies to folders whose archetype is {{ARCHETYPES}} (see `<unit>/.ai/unit.yaml`). For any other archetype, stop and use
`{{PREFIX}}-feature`.

## 1. Load context
- `.ai/standards/` files for this stack, `{{RECIPE_FILE}}` (flow and rules), and the unit's `overview.md` and `gotchas.md`.
- Pick the closest existing example in the same unit from `<unit>/.ai/generated/entry-points.md` and open it with the files it uses.
  New files copy its structure, imports, logging, error handling and naming.

## 2. Ask for anything missing
{{INPUTS}}

## 3. Build - follow `{{RECIPE_FILE}}` → "{{RECIPE_SECTION}}" step by step
{{BODY}}

## 4. Check before you finish
{{CHECKLIST}}
- [ ] `{{PREFIX}}-verify` passes.
- [ ] `python tools/claude-kit/docgen.py` run; the new item appears in `<unit>/.ai/generated/entry-points.md`.
- [ ] The developer has a concrete way to test it (sample request, screen + steps, or message).
