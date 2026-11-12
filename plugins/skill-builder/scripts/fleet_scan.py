#!/usr/bin/env python3
"""
fleet_scan.py - plan a rollout across many repositories.

Runs scan_repo.py on every git repository under a folder (e.g. where you cloned all 50 repos) and writes one summary:
stacks, units, archetypes, tests, activity, risks and whether the kit is already installed - so you can choose the order
and group similar repos. Read-only for the repos except .ai/kit/scan.* inside each (use --no-write to keep them clean).

  python fleet_scan.py --repos C:\\Repos\\Infocruise --out fleet.md [--no-write]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repos", required=True, help="folder that contains the cloned repositories")
    ap.add_argument("--out", default="fleet.md")
    ap.add_argument("--no-write", action="store_true", help="write each scan to a temp folder instead of <repo>/.ai/kit")
    a = ap.parse_args()
    base = Path(a.repos).resolve()
    repos = sorted(p.parent for p in base.glob("*/.git"))
    if not repos:
        print(f"No git repositories directly under {base}", file=sys.stderr)
        return 2
    rows, archetypes, stacks = [], Counter(), Counter()
    for r in repos:
        out = Path(tempfile.mkdtemp()) if a.no_write else r / ".ai" / "kit"
        res = subprocess.run([sys.executable, str(HERE / "scan_repo.py"), "--root", str(r), "--out", str(out)], capture_output=True, text=True)
        if res.returncode != 0:
            rows.append([r.name, "scan failed", "", "", "", "", "", ""])
            continue
        prof = json.loads((out / "scan.json").read_text(encoding="utf-8"))
        units = prof["units"]
        st = Counter()
        for u in units:
            an = u.get("analysis", {})
            fw = an.get("framework", u["kind"])
            st[fw] += 1
            stacks[fw] += 1
            for x in an.get("archetypes", []):
                archetypes[x["archetype"]] += 1
        active = sum(u.get("activity", {}).get("commits_90d", 0) for u in units)
        tests = sum(1 for u in units if u.get("analysis", {}).get("has_tests"))
        unsafe = sum(u.get("analysis", {}).get("unsafe_sql_fragments", 0) for u in units)
        kit = "yes" if (r / ".ai" / "kit" / "manifest.json").exists() else ("other AI setup" if prof["repo"]["existing_ai_setup"] else "no")
        rows.append([r.name, ", ".join(f"{k}×{v}" if v > 1 else k for k, v in st.most_common()), len(units), active,
                     f"{tests}/{len(units)}", unsafe, len(prof["config_secrets"]), kit])
    rows.sort(key=lambda x: -(x[3] if isinstance(x[3], int) else 0))
    L = ["# Fleet scan", "", f"{len(repos)} repositories under `{base}`, most active first.", "",
         "| Repo | Stacks | Units | Commits 90d | Units with tests | SQL built from values | Secret-looking config | Kit |",
         "|---|---|---|---|---|---|---|---|"]
    L += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    L += ["", "## Stacks across the fleet", ""] + [f"- {k}: {v} unit(s)" for k, v in stacks.most_common()]
    L += ["", "## Archetypes across the fleet", "", "Write and polish these starters first - they cover the most repos.", ""]
    L += [f"- {k}: {v} unit(s)" for k, v in archetypes.most_common()]
    Path(a.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Scanned {len(repos)} repositories -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
