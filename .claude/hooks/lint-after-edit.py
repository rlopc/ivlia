"""PostToolUse hook: format and lint each file Claude edits, with its zone's tools.

- backend/**/*.py: `ruff format`, then `ruff check --fix`, in the locked uv
  environment.
- frontend/**: Prettier, then (TypeScript only) `eslint --fix`. Both read the
  repository's ignore files, so generated code is left alone.

Errors that the tools cannot fix go back to Claude (exit 2), so it corrects
them in the next step. Other files are ignored.

Input: the hook JSON on stdin, with `tool_input.file_path`.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

PRETTIER_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".css", ".json", ".html"}
ESLINT_SUFFIXES = {".ts", ".tsx"}


def run(project: Path, *command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["mise", "exec", "--", *command],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )


def backend(project: Path, path: Path) -> list[tuple[str, list[str]]]:
    if path.suffix != ".py":
        return []
    ruff = ["uv", "run", "--locked", "--quiet", "--project", "backend", "ruff"]
    return [
        ("ruff format", [*ruff, "format", "--quiet", str(path)]),
        ("ruff check", [*ruff, "check", "--fix", "--quiet", "--output-format", "concise", str(path)]),
    ]


def frontend(project: Path, path: Path) -> list[tuple[str, list[str]]]:
    steps = []
    if path.suffix in PRETTIER_SUFFIXES:
        # From the root, so the root .prettierignore applies.
        steps.append(("prettier", ["pnpm", "exec", "prettier", "--write", "--log-level", "warn", str(path)]))
    if path.suffix in ESLINT_SUFFIXES:
        eslint = ["pnpm", "--dir", "frontend", "exec", "eslint", "--fix", "--no-warn-ignored"]
        steps.append(("eslint", [*eslint, str(path)]))
    return steps


ZONES = {"backend": backend, "frontend": frontend}


def main() -> int:
    payload = json.load(sys.stdin)
    file_path = payload.get("tool_input", {}).get("file_path")
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd())).resolve()
    if not file_path:
        return 0
    path = Path(file_path).resolve()
    if not path.is_relative_to(project) or not path.exists():
        return 0
    zone = ZONES.get(path.relative_to(project).parts[0])
    if zone is None:
        return 0

    for name, command in zone(project, path):
        result = run(project, *command)
        if result.returncode != 0:
            sys.stderr.write(f"{name} found errors it cannot fix in {path}:\n{result.stdout}{result.stderr}")
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
