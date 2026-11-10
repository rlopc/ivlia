#!/usr/bin/env bash
# Tests for ruff-after-edit.py.
# Usage: .claude/hooks/ruff-after-edit.test.sh
# Each case writes a file, sends the hook its path and checks the exit code
# and, for fixable problems, that the file was fixed.

set -uo pipefail

project="$(cd "$(dirname "$0")/../.." && pwd)"
hook="$project/.claude/hooks/ruff-after-edit.py"
# Inside backend/ so ruff uses its configuration; removed on exit.
scratch="$(mktemp -d "$project/backend/.hook-test.XXXXXX")"
trap 'rm -rf "$scratch"' EXIT
failures=0

run_hook() {
  python3 -I -c 'import json, sys
print(json.dumps({"tool_name": "Edit", "tool_input": {"file_path": sys.argv[1]}}))' "$1" |
    CLAUDE_PROJECT_DIR="$project" python3 -I "$hook" 2>"$scratch/stderr"
}

check() {
  local name=$1 expected=$2 file=$3 actual
  run_hook "$file"
  actual=$?
  if [[ $actual != "$expected" ]]; then
    echo "FAIL: $name: expected exit $expected, got $actual"
    cat "$scratch/stderr"
    failures=$((failures + 1))
  fi
}

# Fixable: unsorted imports and bad formatting are fixed in place.
printf 'import sys\nimport os\nx=[os.sep,sys.platform]\n' >"$scratch/fixable.py"
check "fixable file" 0 "$scratch/fixable.py"
if [[ $(cat "$scratch/fixable.py") != $'import os\nimport sys\n\nx = [os.sep, sys.platform]' ]]; then
  echo "FAIL: fixable file was not fixed:"
  cat "$scratch/fixable.py"
  failures=$((failures + 1))
fi

# Not fixable: the error goes back to Claude with exit 2.
printf 'print(undefined_name)\n' >"$scratch/broken.py"
check "unfixable error" 2 "$scratch/broken.py"
grep -q "F821" "$scratch/stderr" || {
  echo "FAIL: unfixable error not reported"
  failures=$((failures + 1))
}

# Ignored: files outside backend/ and files that are not Python.
outside="$(mktemp -d)"
printf 'print(undefined_name)\n' >"$outside/outside.py"
check "outside backend" 0 "$outside/outside.py"
rm -rf "$outside"
printf 'not python\n' >"$scratch/notes.txt"
check "not python" 0 "$scratch/notes.txt"

if ((failures > 0)); then
  echo "$failures failure(s)"
  exit 1
fi
echo "ruff-after-edit: all tests passed"
