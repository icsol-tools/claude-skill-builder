#!/usr/bin/env bash
# Builds a tiny fictional repo, then runs the scanner, installer (dry run, install, re-install, upgrade) and kit checks on it.
set -euo pipefail
B="$(cd "$(dirname "$0")/.." && pwd)/plugins/skill-builder"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
cd "$T"
git init -q -b main && git config user.email ci@example.com && git config user.name ci
mkdir -p services/Contoso.Demo.API/Controllers web/portal/src archive/old
cat > services/Contoso.Demo.API/Contoso.Demo.API.csproj <<'X'
<Project Sdk="Microsoft.NET.Sdk.Web"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>
X
cat > services/Contoso.Demo.API/Controllers/PingController.cs <<'X'
using Microsoft.AspNetCore.Mvc;
[ApiController][Route("api/v1/ping")] public class PingController : ControllerBase { [HttpGet] public IActionResult Get() => Ok(); }
X
cat > web/portal/package.json <<'X'
{"name":"portal","private":true,"scripts":{"dev":"vite","build":"vite build"},"dependencies":{"react":"18.3.1"},"devDependencies":{"vite":"5.4.0"}}
X
echo 'export const ping = () => fetch("/api/v1/ping");' > web/portal/src/api.ts
echo 'old' > archive/old/readme.txt
git add -A && git commit -qm init
python "$B/scripts/scan_repo.py" --root .
test -s .ai/kit/scan.json && test -s .ai/kit/scan.md
cat > .ai/kit/plan.json <<'X'
{"prefix":"demo","repo_name":"demo","default_branch":"main","excludes":["archive"],
 "units":[{"path":"services/Contoso.Demo.API","kind":"dotnet-project","archetypes":["dotnet-web-api"]},
          {"path":"web/portal","kind":"frontend","archetypes":["react-vite-spa"]}],
 "skills":["change-contract"],"generated_skills":[],"include_db_export":false,"include_service_template":false,
 "include_workflows":true,"has_dotnet_framework":false}
X
python "$B/scripts/install_kit.py" --repo . --dry-run
python "$B/scripts/install_kit.py" --repo .
test -f .ai/kit/manifest.json && test -f .claude/settings.json && test -f .github/workflows/kit-docs-check.yml
python "$B/scripts/install_kit.py" --repo .            # idempotent
python "$B/scripts/install_kit.py" --repo . --upgrade --dry-run
python tools/claude-kit/docgen.py
python tools/claude-kit/docgen.py --check
python tools/claude-kit/kit_check.py | tee "$T/check.txt"   # WARNs are expected: packs are not written in a smoke test
grep -q " 0 FAIL" "$T/check.txt"
python - <<'X'
import json; s=json.load(open(".claude/settings.json")); d=" ".join(s["permissions"]["deny"])
assert "archive" in d, "excluded folder not denied"
X
echo "smoke OK"
