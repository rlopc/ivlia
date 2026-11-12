#!/usr/bin/env bash
# Run gh on this repository with its own fine-grained token from the macOS
# Keychain. Claude Code runs it outside the Bash sandbox, where gh can verify
# TLS, so it accepts only the subcommands listed below and gives gh an empty
# configuration: no aliases, extensions or user settings.
# docs/standards/ai-development.md#github-access
set -euo pipefail

case "${1:-} ${2:-}" in
  "pr view" | "pr diff" | "pr checks" | "pr list" | "pr status" | \
    "run list" | "run view" | "issue view" | "issue list" | "repo view" | \
    "pr create" | "pr edit" | "pr comment" | "pr review" | "pr ready" | \
    "pr close" | "pr reopen" | "pr merge" | "pr update-branch" | \
    "run rerun" | "run cancel" | \
    "issue create" | "issue edit" | "issue comment" | "issue close" | \
    "issue reopen") ;;
  "api "*) ;;
  *)
    echo "gh-repo: '$*' is not allowed (docs/standards/ai-development.md#github-access)" >&2
    exit 2
    ;;
esac

# shellcheck source=/dev/null # github-repo.sh, checked on its own
source "$(dirname "$0")/github-repo.sh"

config="$(mktemp -d)"
trap 'rm -rf "$config"' EXIT
status=0
GH_TOKEN="$TOKEN" GH_REPO="$REPO" GH_CONFIG_DIR="$config" GH_PAGER=cat \
  GH_PROMPT_DISABLED=1 GH_NO_UPDATE_NOTIFIER=1 gh "$@" || status=$?
exit "$status"
