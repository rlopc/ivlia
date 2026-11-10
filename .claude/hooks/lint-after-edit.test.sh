#!/usr/bin/env bash
# Tests for lint-after-edit.py.
# Usage: .claude/hooks/lint-after-edit.test.sh
# Each case writes a file, sends the hook its path and checks the exit code
# and, for fixable problems, that the file was fixed.

set -uo pipefail

project="$(cd "$(dirname "$0")/../.." && pwd)"
hook="$project/.claude/hooks/lint-after-edit.py"
# Inside each zone, so its tools use its configuration; removed on exit.
# The frontend one is not hidden or gitignored: TypeScript and Prettier skip those.
backend="$(mktemp -d "$project/backend/.hook-test.XXXXXX")" || exit 1
frontend="$(mktemp -d "$project/frontend/src/hook-test-XXXXXX")" || exit 1
outside="$(mktemp -d "${TMPDIR:-/tmp}/lint-hook.XXXXXX")" || exit 1
trap 'rm -rf "$backend" "$frontend" "$outside"' EXIT
stderr="$outside/stderr"
failures=0

fail() {
  echo "FAIL: $1"
  failures=$((failures + 1))
}

check() {
  local name=$1 expected=$2 file=$3 actual
  python3 -I -c 'import json, sys
print(json.dumps({"tool_name": "Edit", "tool_input": {"file_path": sys.argv[1]}}))' "$file" |
    CLAUDE_PROJECT_DIR="$project" python3 -I "$hook" 2>"$stderr"
  actual=$?
  if [[ $actual != "$expected" ]]; then
    fail "$name: expected exit $expected, got $actual"
    cat "$stderr"
  fi
}

# Backend, fixable: unsorted imports and bad formatting are fixed in place.
printf 'import sys\nimport os\nx=[os.sep,sys.platform]\n' >"$backend/fixable.py"
check "python fixable" 0 "$backend/fixable.py"
[[ $(cat "$backend/fixable.py") == $'import os\nimport sys\n\nx = [os.sep, sys.platform]' ]] ||
  fail "python fixable file was not fixed"

# Backend, not fixable: the error goes back to Claude with exit 2.
printf 'print(undefined_name)\n' >"$backend/broken.py"
check "python unfixable" 2 "$backend/broken.py"
grep -q "F821" "$stderr" || fail "python error not reported"

# Frontend, fixable: Prettier formats the file.
printf "export const x = {a:1}\n" >"$frontend/fixable.ts"
check "typescript fixable" 0 "$frontend/fixable.ts"
[[ $(cat "$frontend/fixable.ts") == 'export const x = { a: 1 };' ]] ||
  fail "typescript fixable file was not fixed: $(cat "$frontend/fixable.ts")"

# Frontend, not fixable: ESLint's error goes back to Claude with exit 2.
printf 'export const x: any = 1;\n' >"$frontend/broken.ts"
check "typescript unfixable" 2 "$frontend/broken.ts"
grep -q "no-explicit-any" "$stderr" || fail "typescript error not reported"

# Ignored: generated code, files outside the zones, other file types.
contract="$project/frontend/src/contract/events.ts"
before="$(cat "$contract")"
check "generated contract" 0 "$contract"
[[ $(cat "$contract") == "$before" ]] || fail "generated contract was changed"
printf 'print(undefined_name)\n' >"$outside/outside.py"
check "outside the zones" 0 "$outside/outside.py"
printf 'not python\n' >"$backend/notes.txt"
check "backend non-python" 0 "$backend/notes.txt"

if ((failures > 0)); then
  echo "$failures failure(s)"
  exit 1
fi
echo "lint-after-edit: all tests passed"
