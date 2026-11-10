set shell := ["bash", "-euo", "pipefail", "-c"]

# uv resolves the pre-commit environments with the same 7-day cooldown as the lockfiles.
export UV_EXCLUDE_NEWER := "7 days"

# Every recipe runs against the dev installation, never the real data.
export IVLIA_ENV := "dev"
export IVLIA_HOME := justfile_directory() / ".dev"

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
    uv sync --locked --project backend
    pre-commit install
    pre-commit install-hooks

# Run every local check.
check:
    pre-commit run --all-files
    gitleaks git --redact --no-banner
    .claude/hooks/researcher-bash-guard.test.sh
    .claude/hooks/ruff-after-edit.test.sh
    pnpm exec openspec validate --all --strict
    lychee --offline --include-fragments --no-progress --exclude-path node_modules --exclude-path .dev '**/*.md'
    just check-backend

# Backend checks. ruff runs as a pre-commit hook in `check`. --locked: never rewrite uv.lock.
[working-directory: 'backend']
check-backend:
    uv run --locked mypy
    uv run --locked lint-imports
    uv run --locked coverage erase
    uv run --locked coverage run -m pytest
    uv run --locked coverage report --include='src/ivlia/domain/*' --fail-under=100
    uv run --locked coverage report --omit='src/ivlia/domain/*' --fail-under=95

# Run the API of the dev installation with reload.
[working-directory: 'backend']
dev:
    uv run --locked ivlia-server --reload

# Run the formatters and auto-fixes.
fix:
    pnpm exec prettier --write .
    pnpm exec markdownlint-cli2 --fix "**/*.md"

# Export the event contract and the OpenAPI document to backend/schemas/.
[working-directory: 'backend']
contract:
    uv run --locked python -m ivlia.api.schemas schemas

# Write the branch diff against main for the reviewer agent.
review-diff:
    mkdir -p .dev/review
    git diff main...HEAD > .dev/review/diff.patch
    git diff --name-status main...HEAD > .dev/review/files.txt
