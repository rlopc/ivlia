set shell := ["bash", "-euo", "pipefail", "-c"]

# uv resolves the pre-commit environments with the same 7-day cooldown as the lockfiles.
export UV_EXCLUDE_NEWER := "7 days"

# OpenSpec telemetry is off: nothing leaves the machine without a reason.
export OPENSPEC_TELEMETRY := "0"
export DO_NOT_TRACK := "1"

# List the recipes.
default:
    @just --list

# Install the tools and dependencies. Uses the network.
setup:
    mise install
    pnpm install --frozen-lockfile
    pre-commit install
    pre-commit install-hooks

# Run every local check.
check:
    pre-commit run --all-files
    gitleaks git --redact --no-banner
    .claude/hooks/researcher-bash-guard.test.sh
    pnpm exec openspec validate --all --strict
    lychee --offline --include-fragments --no-progress --exclude-path node_modules --exclude-path .dev '**/*.md'

# Run the formatters and auto-fixes.
fix:
    pnpm exec prettier --write .
    pnpm exec markdownlint-cli2 --fix "**/*.md"

# Write the branch diff against main for the reviewer agent.
review-diff:
    mkdir -p .dev/review
    git diff main...HEAD > .dev/review/diff.patch
    git diff --name-status main...HEAD > .dev/review/files.txt
