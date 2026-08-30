#!/usr/bin/env bash
# Verifies the marketplace and plugin manifests are present and valid.
set -euo pipefail
# This script now lives in .instructor/, one level below the repo root where
# the manifests it checks actually are, so climb one extra level to get there.
cd "$(dirname "$0")/.."

fail=0
check() {
  if [ -f "$1" ]; then
    python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$1" \
      && echo "ok    $1" \
      || { echo "BAD   $1 (invalid JSON)"; fail=1; }
  else
    echo "MISS  $1"; fail=1
  fi
}
present() {
  if [ -f "$1" ]; then echo "ok    $1"; else echo "MISS  $1"; fail=1; fi
}

check   .claude-plugin/marketplace.json
check   plugins/cms-starter/.claude-plugin/plugin.json
present plugins/cms-starter/skills/ledger/SKILL.md
present plugins/cms-starter/commands/checkpoint.md

python3 - <<'PY' || fail=1
import json
m = json.load(open(".claude-plugin/marketplace.json"))
p = json.load(open("plugins/cms-starter/.claude-plugin/plugin.json"))
names = [x["name"] for x in m["plugins"]]
assert m["name"] == "cms-f26", f'marketplace name is {m["name"]!r}, expected "cms-f26"'
assert "cms-starter" in names, f"cms-starter missing from marketplace plugins: {names}"
src = [x["source"] for x in m["plugins"] if x["name"] == "cms-starter"][0]
assert src == "./plugins/cms-starter", f"unexpected source {src!r}"
assert p["name"] == "cms-starter", f'plugin name is {p["name"]!r}'
print("ok    manifests agree")
PY

exit $fail
