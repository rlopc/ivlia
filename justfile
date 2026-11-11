set shell := ["bash", "-euo", "pipefail", "-c"]

# Comment lines inside recipes are neither echoed nor run.
set ignore-comments := true

# Every recipe runs against the dev installation, never the real data.
# mise.toml sets the same; repeated here so it holds however just is started.
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
    mise install --locked
    pnpm install --frozen-lockfile
    pnpm --filter ivlia-frontend exec playwright install chromium
    # Every workspace member and dev group; a plain `uv sync` installs only one part.
    uv sync --locked --all-packages
    uv run --locked pre-commit install
    uv run --locked pre-commit install-hooks

# Run every local check.
check:
    uv run --locked pre-commit run --all-files
    gitleaks git --redact --no-banner
    .claude/hooks/researcher-bash-guard.test.sh
    .claude/hooks/lint-after-edit.test.sh
    pnpm exec openspec validate --all --strict
    just check-links --offline
    just check-backend
    just check-frontend

# Links and anchors in every versioned Markdown file, the files pre-commit sees.
# Options are in lychee.toml; `check` adds --offline, links.yml checks online.
check-links *args:
    git ls-files '*.md' | lychee --files-from - {{ args }}

# Backend checks. ruff runs as a pre-commit hook in `check`. --locked: never rewrite uv.lock.
[working-directory: 'backend']
check-backend:
    uv run --locked mypy
    uv run --locked lint-imports
    uv run --locked coverage erase
    uv run --locked coverage run -m pytest
    uv run --locked coverage report --include='src/ivlia/domain/*' --fail-under=100
    uv run --locked coverage report --omit='src/ivlia/domain/*' --fail-under=95

# Frontend checks. Prettier runs as a pre-commit hook in `check`.
[working-directory: 'frontend']
check-frontend:
    pnpm run contract:check
    pnpm run lint
    pnpm run knip
    pnpm run test
    pnpm run build
    pnpm run e2e

# Run the API of the dev installation with reload.
[working-directory: 'backend']
dev:
    uv run --locked ivlia-server --reload

# Run the API and the Vite dev server together; `ivlia web` opens Vite.
dev-web:
    #!/usr/bin/env bash
    set -euo pipefail
    trap 'kill 0' EXIT
    (cd backend && uv run --locked ivlia-server --reload) &
    pnpm --filter ivlia-frontend run dev

# Export the contract and OpenAPI to backend/schemas/, then generate frontend/src/contract/.
contract:
    cd backend && uv run --locked python -m ivlia.api.schemas schemas
    pnpm --filter ivlia-frontend run contract

# Upgrade the tools in mise.toml to their newest release at least 7 days old, and mise.lock. Uses the network.
update-tools:
    mise upgrade --bump

# Write the branch diff against its base (main unless stacked) for the reviewer agent.
review-diff base="main":
    mkdir -p .dev/review
    git diff {{ base }}...HEAD > .dev/review/diff.patch
    git diff --name-status {{ base }}...HEAD > .dev/review/files.txt
