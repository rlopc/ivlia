# Sourced by gh-repo and git-credential-gh-repo, next to it in ~/.local/bin:
# sets REPO to the OWNER/REPO of the origin remote and TOKEN to that
# repository's token from the macOS Keychain (service gh-repo-token), or exits.
# docs/standards/ai-development.md#github-access
# shellcheck shell=bash disable=SC2034 # REPO and TOKEN are for the caller

remote="$(git remote get-url origin)"
if [[ "$remote" =~ ^(https://([^@/]+@)?github\.com/|git@github\.com:|ssh://git@github\.com/)([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/?$ ]]; then
  REPO="${BASH_REMATCH[3]%.git}"
else
  echo "origin is not a GitHub repository: $remote" >&2
  exit 1
fi

if ! TOKEN="$(security find-generic-password -s gh-repo-token -a "$REPO" -w 2> /dev/null)"; then
  echo "No token for $REPO in the Keychain. Add it with:" >&2
  echo "  security add-generic-password -s gh-repo-token -a $REPO -w" >&2
  exit 1
fi
