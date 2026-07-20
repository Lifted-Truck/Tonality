#!/usr/bin/env bash
# Local replica of the cloud CI (.github/workflows/ci.yml) — for when GitHub
# Actions is unavailable (e.g. cloud credits exhausted). Runs the exact two legs
# CI runs, across whichever of the CI Python versions {3.10, 3.13} are installed,
# and reports honestly which legs it could NOT reproduce (never a silent pass).
#
#   bash scripts/ci-local.sh
#
# Exit 0 iff every leg that RAN passed. A missing interpreter is a loud WARN, not
# a pass — a 3.10-only break can still slip through until you install 3.10.

set -u
cd "$(cd "$(dirname "$0")/.." && pwd)"
VERSIONS=("3.10" "3.13")   # the ends of requires-python, exactly as CI's matrix
fail=0 ran=0 missing=()

leg() { # $1 = python bin, $2 = label, rest = pytest args
  local py="$1" label="$2"; shift 2
  local out st
  out="$("$py" -m pytest "$@" -q 2>&1)"; st=$?
  printf '    %-46s %s\n' "$label" "$(printf '%s' "$out" | tail -1)"
  [ "$st" -ne 0 ] && { fail=1; printf '%s\n' "$out" | tail -12 | sed 's/^/      | /'; }
}

find_py() { # echo a usable interpreter for version $1, or nothing
  local v="$1"
  if   [ -x ".venv/bin/python${v}" ]; then echo ".venv/bin/python${v}"
  elif [ -x ".venv/bin/python3" ] && \
       [ "$(.venv/bin/python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null)" = "$v" ]; then
       echo ".venv/bin/python3"
  elif command -v "python${v}" >/dev/null 2>&1; then echo "python${v}"; fi
}

for v in "${VERSIONS[@]}"; do
  py="$(find_py "$v")"
  [ -z "$py" ] && { missing+=("$v"); continue; }
  echo "=== Python $v  ($("$py" --version 2>&1)) ==="
  ran=1; before=$fail
  leg "$py" "dev suite (tests/)"           tests/
  leg "$py" "audit invariants (checks/)"   audit/checks/
  [ "$fail" -eq "$before" ] && echo "    ✓ green"
  echo
done

echo "──────────────────────────────────────────────"
if [ ${#missing[@]} -gt 0 ]; then
  echo "⚠  NOT reproduced: Python ${missing[*]} not installed (CI's matrix is 3.10 + 3.13)."
  echo "   A break that only shows on ${missing[*]} can still slip through. To close it:"
  echo "     pyenv install ${missing[0]} && .venv re-created on it   (or python.org)"
fi
[ "$ran" -eq 0 ] && { echo "✗ no CI Python found — nothing ran."; exit 2; }
[ "$fail" -ne 0 ] && { echo "✗ CI-local FAILED — do not merge."; exit 1; }
echo "✓ CI-local PASSED (every leg that ran is green; heed any ⚠ above)."
exit 0
