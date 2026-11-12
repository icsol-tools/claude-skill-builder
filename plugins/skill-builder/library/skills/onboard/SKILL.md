---
name: {{PREFIX}}-onboard
description: Walk a developer through one unit (solution or app) of {{REPO_NAME}} using its .ai knowledge pack - purpose, where it sits, one real flow end to end, where code goes, traps. Use when someone is new to a unit, asks how something works, or before planning a first change.
argument-hint: "[unit folder, or a flow / screen / endpoint to explain]"
---

# Onboard to a unit of {{REPO_NAME}}

Explain existing code. Do not change files.

## 1. Load context
1. Resolve the unit: the argument, or walk up from the current directory to the nearest folder that holds
   `.ai/unit.yaml` (or `.ai/solution.yaml`) or is listed in `.ai/kit/manifest.json` → `units`. Ask if ambiguous.
   Never use folders listed in `.ai/exclude-paths.txt`.
2. Read in this order: `<unit>/.ai/unit.yaml`, `<unit>/.ai/overview.md`, `gotchas.md`, `decisions.md`,
   `<unit>/.ai/generated/overview.md` and `entry-points.md`, the archetype files named in `unit.yaml`
   (`.ai/archetypes/`), and `.ai/system/system-map.md`.
3. No pack yet: say so, offer `{{PREFIX}}-map-unit`, and continue from code plus `generated/`.
4. If `last_mapped_commit` in `unit.yaml` is far behind `git log -1 --format=%h -- <unit>`, warn that the pack may be stale.

## 2. Explain, in this order
1. **Purpose** in 2-3 sentences: who uses it, what it calls, which business it serves.
2. **Where it sits**: other units, external systems, queues, APIs it calls or serves (system map; for frontends,
   `generated/contracts-and-risks.md` → backend calls).
3. **Anatomy**: folders/projects and the archetype each follows, with what a developer must know about it.
4. **One real flow end to end** with file paths: the one asked about, or the most central (an endpoint, a
   message, a page and the API calls behind it). Open the files and quote the key lines briefly.
5. **Where new code goes** for the 3 most likely changes, and which skill to use (`{{PREFIX}}-feature`,
   the recipe skills listed in `.claude/skills/`, `{{PREFIX}}-fix`).
6. **Traps**: top items from `gotchas.md` and the generated "Traps" / "Risks" sections.
7. **Run it locally**: commands from the pack or `generated/overview.md` (scripts / build). Config key
   names from `generated/config.md`. Never print config values.

Finish by asking which area to go deeper on. If the code contradicts the pack, say so and propose the correction.
