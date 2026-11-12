#!/usr/bin/env python3
"""
kit_check.py (claude-kit): checks that this repo's Claude Code setup is complete and safe.

Read-only. Prints PASS / WARN / FAIL per check and exits 1 if anything FAILs, so it can run in CI.
Python 3.10+, standard library only. Run from anywhere:

  python tools/claude-kit/kit_check.py            # from the repo root
  python tools/claude-kit/kit_check.py --ci       # no colours, exit code only matters
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COUNTS = {"PASS": 0, "WARN": 0, "FAIL": 0}
COLOR = {"PASS": "\033[32m", "WARN": "\033[33m", "FAIL": "\033[31m"}
USE_COLOR = sys.stdout.isatty() and os.name != "nt"
SKIP = {".git", "node_modules", "bin", "obj", ".vs", "dist", "build", ".next", ".angular", "coverage", "packages"}


def report(status: str, msg: str) -> None:
    COUNTS[status] += 1
    tag = f"{COLOR[status]}[{status}]\033[0m" if USE_COLOR else f"[{status}]"
    print(f"{tag} {msg}")


def section(title: str) -> None:
    print(f"\n== {title} ==")


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def git(*args: str) -> tuple[int, str]:
    try:
        r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, timeout=60)
        return r.returncode, r.stdout.strip()
    except Exception:
        return 1, ""


def load_excludes() -> list[str]:
    f = ROOT / ".ai" / "exclude-paths.txt"
    if not f.exists():
        return []
    return [l.split("#", 1)[0].strip().replace("\\", "/").strip("/") for l in f.read_text(encoding="utf-8-sig").splitlines()
            if l.split("#", 1)[0].strip()]


def excluded(relp: str, excludes: list[str]) -> bool:
    r = relp.lower()
    return any(r == e.lower() or r.startswith(e.lower() + "/") for e in excludes)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def frontmatter(text: str) -> dict:
    m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"([A-Za-z_-]+)\s*:\s*(.*)$", line)
        if mm:
            out[mm.group(1)] = mm.group(2).strip().strip('"').strip("'")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ci", action="store_true")
    a = ap.parse_args()
    global USE_COLOR
    if a.ci:
        USE_COLOR = False
    print(f"Checking {ROOT}")
    excludes = load_excludes()

    # ------------------------------------------------------------ kit manifest
    section("Kit files")
    man_path = ROOT / ".ai" / "kit" / "manifest.json"
    manifest = {}
    if not man_path.exists():
        report("FAIL", ".ai/kit/manifest.json missing - the kit was not installed with install_kit.py")
    else:
        manifest = json.loads(man_path.read_text(encoding="utf-8"))
        print(f"       kit {manifest.get('kit_version')} installed {manifest.get('installed_at')} by builder {manifest.get('builder_version')}")
        missing, modified = [], []
        for f, h in manifest.get("managed_files", {}).items():
            p = ROOT / f
            if not p.exists():
                missing.append(f)
            elif sha256(p) != h:
                modified.append(f)
        for m in missing:
            report("FAIL", f"managed file missing: {m}")
        if modified:
            report("WARN", f"{len(modified)} managed file(s) changed locally (an upgrade will ask before replacing them): " + ", ".join(modified[:6]) + (" ..." if len(modified) > 6 else ""))
        if not missing and not modified:
            report("PASS", f"all {len(manifest.get('managed_files', {}))} managed files present and unmodified")
    for f in ("CLAUDE.md", ".ai/README.md", ".ai/GUIDE.md", ".claude/settings.json"):
        if not (ROOT / f).exists():
            report("FAIL", f"missing {f}")
    for f in manifest.get("seeded_files", []):
        p = ROOT / f
        if p.exists() and re.search(r"\{\{[A-Z_]+\}\}", p.read_text(encoding="utf-8-sig")):
            report("WARN", f"{f} still has unfilled {{{{PLACEHOLDERS}}}} - finish setup-repo or fill them by hand")
    pending = [rel(p) for p in ROOT.rglob("*.kit-new") if not any(part in SKIP for part in p.parts)]
    for x in pending:
        report("WARN", f"pending kit upgrade merge: {x} (merge into the file without .kit-new, then delete it)")

    # ------------------------------------------------------------ skills
    section("Skills")
    skills_dir = ROOT / ".claude" / "skills"
    skill_files = sorted(skills_dir.glob("*/SKILL.md")) if skills_dir.exists() else []
    if not skill_files:
        report("FAIL", "no skills in .claude/skills/")
    names = set()
    for f in skill_files:
        fm = frontmatter(f.read_text(encoding="utf-8-sig"))
        folder = f.parent.name
        problems = []
        if fm.get("name") != folder:
            problems.append(f"name '{fm.get('name')}' does not match folder '{folder}'")
        if not fm.get("description"):
            problems.append("no description")
        elif len(fm["description"]) > 1024:
            problems.append("description over 1024 characters")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", folder):
            problems.append("folder name must be lower-case letters, digits and hyphens")
        if re.search(r"\{\{[A-Z_]+\}\}", f.read_text(encoding="utf-8-sig")):
            problems.append("unfilled {{PLACEHOLDER}} left in the skill")
        names.add(folder)
        for pr in problems:
            report("FAIL", f".claude/skills/{folder}: {pr}")
    if skill_files:
        report("PASS", f"{len(skill_files)} skill(s): " + ", ".join(sorted(names)))
    for s in manifest.get("skills", []):
        if s not in names:
            report("WARN", f"manifest lists skill '{s}' but .claude/skills/{s}/SKILL.md is missing")

    # ------------------------------------------------------------ settings
    section("Claude settings")
    try:
        settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        report("PASS", ".claude/settings.json is valid JSON")
        deny = settings.get("permissions", {}).get("deny", [])
        for e in excludes:
            if f"Read({e}/**)" in deny and f"Edit({e}/**)" in deny:
                report("PASS", f"Claude is denied reading and editing {e}/")
            elif not e.startswith("tools/"):
                report("WARN", f"excluded path {e}/ is not denied in .claude/settings.json (add Read({e}/**) and Edit({e}/**))")
        if not any("appsettings.Development.json" in d or ".env" in d for d in deny):
            report("WARN", "settings.json denies no secret files (appsettings.Development.json, .env)")
    except Exception as ex:  # noqa: BLE001
        report("FAIL", f".claude/settings.json unreadable: {ex}")

    # ------------------------------------------------------------ units
    section("Units (solutions and apps)")
    units = manifest.get("units", [])
    if not units:
        report("WARN", "manifest lists no units")
    for u in units:
        path, base = u["path"], ROOT / u["path"]
        if excluded(path, excludes):
            report("WARN", f"{path}: listed as a unit but excluded in .ai/exclude-paths.txt")
            continue
        issues, warns = [], []
        if not (base / ".ai" / "generated").exists():
            issues.append("no generated docs - run python tools/claude-kit/docgen.py")
        yaml = base / ".ai" / "unit.yaml"
        if not yaml.exists():
            yaml = base / ".ai" / "solution.yaml"
        if not yaml.exists():
            warns.append("no unit.yaml / narrative pack yet (use the map-unit skill)")
        else:
            y = yaml.read_text(encoding="utf-8-sig")
            if re.search(r"(?m)^\s*-\s*TODO", y):
                warns.append("owners still TODO")
        if not (base / "CLAUDE.md").exists():
            warns.append("no CLAUDE.md")
        nf = base / "db" / "NOT-FOUND.md"
        if nf.exists():
            warns.append(f"db/NOT-FOUND.md lists {sum(1 for l in nf.read_text(encoding='utf-8-sig').splitlines() if l.startswith('- '))} object(s)")
        for i in issues:
            report("FAIL", f"{path}: {i}")
        for w in warns:
            report("WARN", f"{path}: {w}")
        if not issues and not warns:
            report("PASS", f"{path}: complete")

    # ------------------------------------------------------------ generated docs fresh
    section("Generated docs")
    gen = ROOT / "tools" / "claude-kit" / "docgen.py"
    if gen.exists():
        r = subprocess.run([sys.executable, str(gen), "--root", str(ROOT), "--check"], capture_output=True, text=True)
        if r.returncode == 0:
            report("PASS", "docgen --check: up to date")
        else:
            report("FAIL", "generated docs are stale - run: python tools/claude-kit/docgen.py")

    # ------------------------------------------------------------ secrets in docs / excluded leftovers
    section("Safety")
    hits = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        d = Path(dirpath)
        relp = d.relative_to(ROOT).as_posix()
        dirnames[:] = [x for x in dirnames if x not in SKIP and not excluded((d / x).relative_to(ROOT).as_posix(), excludes)]
        if not re.search(r"(^|/)(\.ai|db|\.claude)(/|$)", relp):
            continue
        for fn in filenames:
            if fn.endswith((".md", ".json", ".yaml", ".yml", ".sql")):
                t = (d / fn).read_text(encoding="utf-8", errors="replace")
                for m in re.finditer(r"(?i)(password|pwd)\s*=\s*[^;\"\s{<]{3,}|accountkey=|-----BEGIN [A-Z ]*PRIVATE KEY-----|sk_live_[0-9A-Za-z]{10,}|AKIA[0-9A-Z]{16}", t):
                    hits.append(f"{rel(d / fn)}:{t.count(chr(10), 0, m.start()) + 1}")
    if hits:
        for h in hits[:20]:
            report("FAIL", f"possible secret in docs: {h}")
    else:
        report("PASS", "no password-like values in .ai/, db/ or .claude/")
    left = []
    for e in excludes:
        b = ROOT / e
        if b.is_dir() and not e.startswith("tools/"):
            left += [rel(p) for p in b.rglob(".ai") if p.is_dir()]
    if left:
        report("WARN", f"{len(left)} .ai folder(s) inside excluded paths - delete them: " + ", ".join(left[:5]))

    # ------------------------------------------------------------ tools + git
    section("Tools and git")
    report("PASS" if sys.version_info >= (3, 10) else "FAIL", f"Python {sys.version.split()[0]}")
    kinds = {u.get("kind", "") for u in units}
    if any(k.startswith("dotnet") for k in kinds):
        rc = subprocess.run(["dotnet", "--version"], capture_output=True, text=True, shell=os.name == "nt").returncode if shutil_which("dotnet") else 1
        report("PASS" if rc == 0 else "WARN", "dotnet SDK found" if rc == 0 else "dotnet SDK not on PATH (verify cannot build .NET units)")
    if "frontend" in kinds:
        report("PASS" if shutil_which("node") else "WARN", "node found" if shutil_which("node") else "node not on PATH (verify cannot build frontend units)")
    rc, branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if rc == 0:
        report("WARN" if branch in ("main", "master") else "PASS", f"on branch '{branch}'" + (" - work on a feature branch" if branch in ("main", "master") else ""))
        ignored = []
        for f in ["CLAUDE.md", ".ai/README.md", ".claude/settings.json", ".ai/kit/manifest.json"] + [s.relative_to(ROOT).as_posix() for s in skill_files[:3]]:
            if git("check-ignore", "-q", "--", f)[0] == 0:
                ignored.append(f)
        for i in ignored:
            report("FAIL", f".gitignore excludes {i} - it would not be committed")

    print(f"\nSummary: {COUNTS['PASS']} PASS, {COUNTS['WARN']} WARN, {COUNTS['FAIL']} FAIL")
    print("Fix the FAIL items." if COUNTS["FAIL"] else ("WARN items are fine to start with; keep them on your list." if COUNTS["WARN"] else "All good."))
    return 1 if COUNTS["FAIL"] else 0


def shutil_which(cmd: str) -> bool:
    import shutil
    return shutil.which(cmd) is not None


if __name__ == "__main__":
    sys.exit(main())
