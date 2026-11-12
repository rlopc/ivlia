"""PostToolUse hook: format and lint each file Claude edits, as pre-commit does.

The same file tools, order and file selection as .pre-commit-config.yaml, so a
problem is reported while writing, not at commit. File types come from
identify, the library pre-commit uses for `types`, so a file is a shell script
or YAML here exactly when it is for pre-commit:

- GitHub Actions files (YAML): zizmor (offline), and actionlint for workflows.
- Shell scripts: shellcheck.
- Markdown: markdownlint-cli2 with --fix; .markdownlint-cli2.jsonc decides
  which files it skips.
- backend/**/*.py: `ruff check --fix`, then `ruff format` (Ruff's order), in
  the locked uv environment.
- Any file: Prettier with --ignore-unknown; .prettierignore decides.
- frontend/**/*.ts(x): `eslint --fix`, as `just check-frontend` runs it.

gitleaks is not here: it scans what is staged, at commit.

Paths are passed relative to the repository root, which is the working
directory, as pre-commit does, so the ignore patterns match the same way.

Errors that the tools cannot fix go back to Claude (exit 2), so it corrects
them in the next step. Files outside the repository are ignored.

Input: the hook JSON on stdin, with `tool_input.file_path`.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ESLINT_SUFFIXES = {".ts", ".tsx"}
# The same `files` patterns as the zizmor and actionlint hooks.
ZIZMOR_FILES = re.compile(
    r"(^|/)(\.github/(workflows/[^/]+|dependabot)\.ya?ml|action\.ya?ml|\.pre-commit-(config|hooks)\.ya?ml)$"
)
ACTIONLINT_FILES = re.compile(r"^\.github/workflows/.*\.ya?ml$")


def run(project: Path, *command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["mise", "exec", "--", *command],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )


def file_types(project: Path, file: str) -> set[str]:
    """identify's tags for a file, from the locked environment; none on error."""
    result = run(project, "uv", "run", "--locked", "--quiet", "identify-cli", file)
    try:
        return set(json.loads(result.stdout)) if result.returncode == 0 else set()
    except json.JSONDecodeError:
        return set()


def steps(project: Path, path: Path) -> list[tuple[str, list[str]]]:
    """The commands for a path relative to the repository root, in order."""
    file, zone = path.as_posix(), path.parts[0]
    types = file_types(project, file)
    result = []
    if "yaml" in types and ZIZMOR_FILES.search(file):
        result.append(("zizmor", ["zizmor", "--offline", "--no-progress", file]))
    if "shell" in types:
        result.append(("shellcheck", ["shellcheck", file]))
    if ACTIONLINT_FILES.match(file):
        result.append(("actionlint", ["actionlint", file]))
    if "markdown" in types:
        result.append(("markdownlint", ["pnpm", "exec", "markdownlint-cli2", "--fix", file]))
    if zone == "backend" and path.suffix == ".py":
        ruff = ["uv", "run", "--locked", "--quiet", "--project", "backend", "ruff"]
        result.append(("ruff check", [*ruff, "check", "--fix", "--quiet", "--output-format", "concise", file]))
        result.append(("ruff format", [*ruff, "format", "--quiet", file]))
    result.append(("prettier", ["pnpm", "exec", "prettier", "--write", "--ignore-unknown", "--log-level", "warn", file]))
    if zone == "frontend" and path.suffix in ESLINT_SUFFIXES:
        eslint = ["pnpm", "--dir", "frontend", "exec", "eslint", "--fix", "--no-warn-ignored"]
        # ESLint runs in frontend/, so its path is relative to it.
        result.append(("eslint", [*eslint, str(path.relative_to("frontend"))]))
    return result


def main() -> int:
    payload = json.load(sys.stdin)
    file_path = payload.get("tool_input", {}).get("file_path")
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd())).resolve()
    if not file_path:
        return 0
    path = Path(file_path).resolve()
    if not path.is_relative_to(project) or not path.is_file():
        return 0

    for name, command in steps(project, path.relative_to(project)):
        result = run(project, *command)
        if result.returncode != 0:
            sys.stderr.write(f"{name} found errors it cannot fix in {path}:\n{result.stdout}{result.stderr}")
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
