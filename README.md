# Infocruise Claude Code skill builder

One plugin that sets up Claude Code in any of our repositories the way we did for Gain-Core-Services: it **scans the repo**,
**interviews the team** (scope, conventions, which skills they want), shows a **plan**, and on confirmation **deploys** everything
**into the repo**: skills, knowledge packs, doc tools and CI. After setup the repo is self-contained. Developers just clone it and
run `claude`.

```
skill-builder (this repo, installed once per lead)           each repository (after /skill-builder:setup-repo)
├─ skills/  setup-repo · add-skill · upgrade-kit · status   ├─ CLAUDE.md, <unit>/CLAUDE.md
├─ agents/  convention-miner · skill-reviewer               ├─ .claude/skills/<prefix>-*      core + recipe + custom skills
├─ scripts/ scan_repo · install_kit · fleet_scan            ├─ .claude/agents/                unit-mapper, db-mapper, pack-reviewer
├─ library/ skills · archetype starters · standards ·       ├─ .claude/settings.json          secrets + excluded folders denied
│           doc templates · examples/gain-core-services     ├─ .ai/  standards (mined) · archetypes (+recipes) · system · GUIDE
└─ kit/     tools/claude-kit · workflows (copied to repos)  ├─ <unit>/.ai/  unit.yaml · overview · gotchas · decisions · generated/
                                                            ├─ tools/claude-kit/  docgen · kit_check · export-db · templates
                                                            └─ .github/workflows/kit-docs-{check,update,drift}.yml
```

## Install (each lead or platform engineer, once)
1. Push this folder to a GitHub repo, e.g. `Infocruise/claude-skill-builder`.
2. In Claude Code: `/plugin marketplace add Infocruise/claude-skill-builder`, then `/plugin install skill-builder@infocruise-tools`.
   Local alternative for testing: `/plugin marketplace add C:\path\to\claude-skill-builder`.
3. Requirements: Python 3.10+, git. PowerShell only for the DB export and the .NET API template.

## Use
| Command (in a repo) | What it does |
|---|---|
| `/skill-builder:setup-repo` | Scan → interview → plan → deploy → review → hand over. 1-3 hours with the team, depending on repo size |
| `/skill-builder:add-skill <need>` | One more repo-specific skill, built from real examples in the code and reviewed |
| `/skill-builder:upgrade-kit` | Bring a repo to this builder's kit version; never overwrites the team's edits |
| `/skill-builder:status` | Kit version, problems, units without packs, next action |
| `python plugins/skill-builder/scripts/fleet_scan.py --repos C:\Repos --out fleet.md --no-write` | Plan the rollout across all repos |

## How it stays maintainable across 50 repos
- **Skills are generic procedures; knowledge is per repo.** The core skills (`onboard`, `feature`, `fix`, `verify`,
  `docs-refresh`, `map-unit`) contain no repo facts. They read the repo's `.ai/` folder. One fix in `library/skills/` reaches
  every repo on its next `upgrade-kit`.
- **Standards are discovered, not imposed.** Teams differ, so `convention-miner` reads each repo's code (with consistency counts)
  and the team confirms or chooses. Only two rules are non-negotiable kit-wide: SQL values as parameters, and no secrets in
  code, docs or prompts.
- **Managed vs seeded files.** `.ai/kit/manifest.json` records a hash of every kit-managed file. An upgrade replaces only the
  untouched ones. An edited file gets a `.kit-new` file next to it, to merge and then `--accept`. Repo-owned knowledge is never
  touched.
- **A finished reference.** `library/examples/gain-core-services/` is the POC output: the depth every repo's archetype recipes and
  packs should reach.

See `ROLLOUT.md` for the 50-repo plan.
