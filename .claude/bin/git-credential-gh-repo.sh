#!/usr/bin/env bash
# git credential helper for github.com: answers "get" with this repository's
# token from the macOS Keychain. Installed by the user as
# ~/.local/bin/git-credential-gh-repo. git runs it for `git push`, which Claude
# Code runs outside the Bash sandbox; run directly by Claude, it stays inside
# the sandbox, where the user's Keychain is not visible.
# docs/standards/ai-development.md#github-access
set -euo pipefail

[[ "${1:-}" == get ]] || exit 0
host=""
while IFS='=' read -r key value && [[ -n "$key" ]]; do
  [[ "$key" == host ]] && host="$value"
done
[[ "$host" == github.com ]] || exit 0

# shellcheck source=/dev/null # github-repo.sh, checked on its own
source "$(dirname "$0")/github-repo.sh"
printf 'username=x-access-token\npassword=%s\n' "$TOKEN"
