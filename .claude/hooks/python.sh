#!/usr/bin/env bash
# Runs a Claude Code hook with the project's Python, the root .venv's (the same
# as `just check` and CI), in isolated mode: python.sh <hook.py>.
# Without the .venv it exits 2 and says what to do, so neither hook fails
# without a reason (the researcher's guard also blocks on any failure, with
# `onFailure: "block"` in .claude/settings.json).

set -euo pipefail

python="${CLAUDE_PROJECT_DIR:?}/.venv/bin/python"
if [[ ! -x $python ]]; then
  echo "No .venv with the project's Python: run \`just setup\`." >&2
  exit 2
fi
exec "$python" -I "$@"
