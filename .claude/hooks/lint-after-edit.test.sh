#!/usr/bin/env bash
# Tests for lint-after-edit.py.
# Usage: .claude/hooks/lint-after-edit.test.sh
# Each case writes a file, sends the hook its path and checks the exit code
# and, for fixable problems, that the file was fixed.

# shellcheck disable=SC2016  # the test files are literal scripts and workflows
set -uo pipefail

project="$(cd "$(dirname "$0")/../.." && pwd)"
hook="$project/.claude/hooks/lint-after-edit.py"
# Inside each zone, so its tools use its configuration; removed on exit.
# The frontend and root ones are not hidden or gitignored: TypeScript, Prettier
# and markdownlint skip those.
backend="$(mktemp -d "$project/backend/.hook-test.XXXXXX")" || exit 1
frontend="$(mktemp -d "$project/frontend/src/hook-test-XXXXXX")" || exit 1
root="$(mktemp -d "$project/hook-test-XXXXXX")" || exit 1
outside="$(mktemp -d "${TMPDIR:-/tmp}/lint-hook.XXXXXX")" || exit 1
# Workflows must sit in .github/workflows/ itself, where zizmor and actionlint
# look. Gitignored; leftovers of a killed run are removed first.
rm -f "$project"/.github/workflows/hook-test-*.yml
workflow="$project/.github/workflows/hook-test-$$"
trap 'rm -rf "$backend" "$frontend" "$root" "$outside" "$workflow"-*.yml' EXIT
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

# Any zone: Prettier formats every type it knows, as pre-commit does.
printf 'a:   [1,2]\n' >"$root/fixable.yaml"
check "yaml fixable" 0 "$root/fixable.yaml"
[[ $(cat "$root/fixable.yaml") == 'a: [1, 2]' ]] ||
  fail "yaml fixable file was not fixed: $(cat "$root/fixable.yaml")"

# Markdown, fixable: markdownlint fixes the file.
printf '#Title\n' >"$root/fixable.md"
check "markdown fixable" 0 "$root/fixable.md"
[[ $(cat "$root/fixable.md") == '# Title' ]] ||
  fail "markdown fixable file was not fixed: $(cat "$root/fixable.md")"

# Markdown, not fixable: the error goes back to Claude with exit 2.
printf '# Title\n\n[link](#missing)\n' >"$root/broken.md"
check "markdown unfixable" 2 "$root/broken.md"
grep -q "MD051" "$stderr" || fail "markdown error not reported"

# Shell, as identify (pre-commit's `types`) sees it: by suffix, or by the
# shebang of an executable file. A clean script passes.
printf '#!/usr/bin/env bash\necho "$1"\n' >"$root/clean.sh"
check "shell clean" 0 "$root/clean.sh"
printf '#!/usr/bin/env bash\necho $1\n' >"$root/broken.sh"
check "shell unfixable" 2 "$root/broken.sh"
grep -q "SC2086" "$stderr" || fail "shell error not reported"
printf '#!/usr/bin/env bash\necho $1\n' >"$root/broken-script"
chmod +x "$root/broken-script"
check "shell by shebang" 2 "$root/broken-script"
grep -q "SC2086" "$stderr" || fail "shell error by shebang not reported"
# Not shell for pre-commit either: a shebang without the executable bit, and fish.
printf '#!/usr/bin/env bash\necho $1\n' >"$root/not-executable"
check "shebang, not executable" 0 "$root/not-executable"
printf '#!/usr/bin/env fish\necho $argv\n' >"$root/fish-script"
chmod +x "$root/fish-script"
check "fish script" 0 "$root/fish-script"

# Text files no formatter owns: end-of-file-fixer and trailing-whitespace-fixer.
printf 'a = 1   \nb = 2' >"$root/fixable.toml"
check "unowned text fixable" 0 "$root/fixable.toml"
[[ $(cat "$root/fixable.toml") == $'a = 1\nb = 2' && $(tail -c 1 "$root/fixable.toml" | od -An -c | tr -d ' ') == '\n' ]] ||
  fail "unowned text file was not fixed: $(cat "$root/fixable.toml")"

# Workflows: zizmor (security) and actionlint (syntax), each on its own case.
# workflow_dispatch: no third-party trigger, even if a leftover reached git.
printf 'on: workflow_dispatch\npermissions: {}\njobs:\n  a:\n    runs-on: ubuntu-latest\n    timeout-minutes: 5\n    steps:\n      - run: echo "${{ github.event.issue.title }}"\n' >"$workflow-injection.yml"
check "workflow zizmor" 2 "$workflow-injection.yml"
if ! { grep -q "^zizmor found errors" "$stderr" && grep -q "template-injection" "$stderr"; }; then
  fail "zizmor error not reported: $(head -1 "$stderr")"
fi
printf 'on: push\npermissions: {}\njobs:\n  a:\n    runs-on: ubuntu-latest\n    timeout-minutes: 5\n    foo: bar\n    steps:\n      - run: echo hi\n' >"$workflow-syntax.yml"
check "workflow actionlint" 2 "$workflow-syntax.yml"
if ! { grep -q "^actionlint found errors" "$stderr" && grep -q "syntax-check" "$stderr"; }; then
  fail "actionlint error not reported: $(head -1 "$stderr")"
fi

# Ignored: generated files, files outside the repository, unknown types.
for generated in "$project/frontend/src/contract/events.ts" "$project/CHANGELOG.md"; do
  before="$(cat "$generated")"
  check "generated ${generated#"$project/"}" 0 "$generated"
  [[ $(cat "$generated") == "$before" ]] || fail "generated ${generated#"$project/"} was changed"
done
printf 'print(undefined_name)\n' >"$outside/outside.py"
check "outside the repository" 0 "$outside/outside.py"
printf 'not python\n' >"$backend/notes.txt"
check "unknown type" 0 "$backend/notes.txt"

if ((failures > 0)); then
  echo "$failures failure(s)"
  exit 1
fi
echo "lint-after-edit: all tests passed"
