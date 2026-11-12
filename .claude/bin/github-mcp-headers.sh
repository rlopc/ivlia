#!/usr/bin/env bash
# headersHelper for GitHub's remote MCP server in Claude Code: prints the
# request headers as JSON, with the token read from the macOS Keychain
# (service github-mcp-token), so the token is never in a config file or in
# Claude's context. The user installs it as ~/.local/bin/github-mcp-headers,
# out of Claude's reach. docs/standards/ai-development.md#github-access
set -euo pipefail

token="$(security find-generic-password -s github-mcp-token -w)"
if [[ ! "$token" =~ ^[A-Za-z0-9_]+$ ]]; then
  echo "github-mcp-headers: unexpected token format" >&2
  exit 1
fi
# Only the toolsets the pull request workflow needs; lockdown hides content
# written by users without push access (a filter, not a security boundary).
printf '{"Authorization": "Bearer %s", "X-MCP-Toolsets": "%s", "X-MCP-Lockdown": "true"}\n' \
  "$token" "context,issues,pull_requests,actions,dependabot,code_security"
