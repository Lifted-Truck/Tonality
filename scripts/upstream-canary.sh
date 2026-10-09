#!/usr/bin/env bash
# Local twin of .github/workflows/upstream-canary.yml, for when GitHub Actions is
# unavailable (it has been: credits exhausted). Same three checks, same
# meanings — read that workflow's header for what each verdict means.
#
#   bash scripts/upstream-canary.sh
#
# Needs network and `uv` (it builds throwaway venvs; nothing touches .venv).
# Exit status follows the BLOCKING checks only (mcp-ceiling, vulnerability
# scan); mcp-newest is gap 29's meter and is reported, never failed on —
# exactly as `continue-on-error` treats it in the workflow.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if ! command -v uv >/dev/null 2>&1; then
  echo "upstream-canary: WARN — uv not found; NOTHING was checked (install uv)." >&2
  exit 2
fi
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
status=0

run_mcp() {  # $1 = ceiling | newest
  local venv="$WORK/$1" py
  uv venv -q -p 3.13 "$venv" || return 1
  py="$venv/bin/python"
  if [ "$1" = ceiling ]; then
    # Resolves the extra itself, so the bound comes from pyproject.toml.
    uv pip install -q -p "$py" --upgrade -e "$ROOT[dev,mcp]" || return 1
  else
    uv pip install -q -p "$py" -e "$ROOT[dev]" && uv pip install -q -p "$py" --upgrade mcp || return 1
  fi
  echo "   mcp $("$py" -c 'import importlib.metadata as m; print(m.version("mcp"))')"
  (cd "$ROOT" && "$py" -m pytest -q -p no:cacheprovider \
      tests/test_mcp_tools.py tests/test_resource_limits.py | tail -1)
  return "${PIPESTATUS[0]}"
}

echo "== mcp (ceiling) — what users install today; blocking"
if run_mcp ceiling; then echo "   ok"; else echo "   RED: a break users are about to hit"; status=1; fi

echo "== mcp (newest) — gap 29 meter; informational"
if run_mcp newest; then
  echo "   green: the newest SDK works — gap 29's port may be unnecessary or done"
else
  echo "   red (expected until gap 29 ports build_server to the 2.x API)"
fi

echo "== vulnerability scan (pip-audit, both locks); blocking"
for lock in "$ROOT"/requirements/*.lock; do
  # Capture first, THEN read $?: an exit status read after `echo "$(...)"` is
  # echo's, so a vulnerable lock would have printed its findings and passed.
  out="$(uvx -q pip-audit --require-hashes --disable-pip -r "$lock" 2>&1)"
  rc=$?
  echo "   $(basename "$lock"): $(printf '%s\n' "$out" | tail -1)"
  [ "$rc" -eq 0 ] || { printf '%s\n' "$out" | sed 's/^/      /'; status=1; }
done

if [ "$status" -eq 0 ]; then echo "upstream-canary: green"; else echo "upstream-canary: RED"; fi
exit "$status"
