"""PostToolUse hook: format and lint each file Claude edits, as pre-commit does.

The same file tools, order and file selection as .pre-commit-config.yaml, so a
problem is reported while writing, not at commit. File types come from
identify, the library pre-commit uses for `types`, so a file is a shell script
or YAML here exactly when it is for pre-commit:

- Text files that no formatter owns (TOML, shell, SQL, justfile, ignore files,
  .python-version): end-of-file-fixer and trailing-whitespace-fixer.
- GitHub Actions files (YAML): zizmor (offline), and actionlint for workflows.
- Shell scripts: shellcheck.
- Markdown: markdownlint-cli2 with --fix; .markdownlint-cli2.jsonc decides
  which files it skips.
- Python in backend/ and .claude/hooks/: `ruff check --fix`, then `ruff format`
  (Ruff's order), in the locked uv environment.
- Any file: Prettier with --ignore-unknown; .prettierignore decides.
- frontend/**/*.ts(x): `eslint --fix`, as `just check-frontend` runs it.

gitleaks and pre-commit-hooks' commit checks (large files, case and merge
conflicts) are not here: they check the commit, not one file.

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
# The `files` of the end-of-file-fixer and trailing-whitespace hooks (`*unowned`).
UNOWNED_FILES = re.compile(
    r"(\.(toml|sh|sql)|(^|/)(justfile|\.gitignore|\.prettierignore|\.python-version))$"
)
RUFF_FILES = re.compile(r"^(backend/.*|\.claude/hooks/[^/]+)\.py$")


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


def steps(project: Path, path: Path) -> list[tuple[str, list[str], bool]]:
    """The commands for a path relative to the repository root, in order, and
    whether each is a pre-commit-hooks fixer."""
    file, zone = path.as_posix(), path.parts[0]
    types = file_types(project, file)
    result = []
    if "text" in types and UNOWNED_FILES.search(file):
        for fixer in ("end-of-file-fixer", "trailing-whitespace-fixer"):
            result.append(
                (fixer, ["uv", "run", "--locked", "--quiet", fixer, file], True)
            )
    if "yaml" in types and ZIZMOR_FILES.search(file):
        result.append(("zizmor", ["zizmor", "--offline", "--no-progress", file], False))
    if "shell" in types:
        result.append(("shellcheck", ["shellcheck", file], False))
    if ACTIONLINT_FILES.match(file):
        result.append(("actionlint", ["actionlint", file], False))
    if "markdown" in types:
        result.append(
            (
                "markdownlint",
                ["pnpm", "exec", "markdownlint-cli2", "--fix", file],
                False,
            )
        )
    if RUFF_FILES.match(file):
        ruff = ["uv", "run", "--locked", "--quiet", "--project", "backend", "ruff"]
        result.append(
            (
                "ruff check",
                [
                    *ruff,
                    "check",
                    "--fix",
                    "--quiet",
                    "--output-format",
                    "concise",
                    file,
                ],
                False,
            )
        )
        result.append(("ruff format", [*ruff, "format", "--quiet", file], False))
    result.append(
        (
            "prettier",
            [
                "pnpm",
                "exec",
                "prettier",
                "--write",
                "--ignore-unknown",
                "--log-level",
                "warn",
                file,
            ],
            False,
        )
    )
    if zone == "frontend" and path.suffix in ESLINT_SUFFIXES:
        eslint = [
            "pnpm",
            "--dir",
            "frontend",
            "exec",
            "eslint",
            "--fix",
            "--no-warn-ignored",
        ]
        # ESLint runs in frontend/, so its path is relative to it.
        result.append(("eslint", [*eslint, str(path.relative_to("frontend"))], False))
    return result


def succeeded(result: subprocess.CompletedProcess[str], fixer: bool) -> bool:
    """Exit 0, or, for a fixer, exit 1 with its "Fixing <file>" message: it
    changed the file. A crash also exits 1, but with a traceback on stderr."""
    if result.returncode == 0:
        return True
    return (
        fixer
        and result.returncode == 1
        and result.stdout.startswith("Fixing ")
        and not result.stderr.strip()
    )


def main() -> int:
    payload = json.load(sys.stdin)
    file_path = payload.get("tool_input", {}).get("file_path")
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd())).resolve()
    if not file_path:
        return 0
    path = Path(file_path).resolve()
    if not path.is_relative_to(project) or not path.is_file():
        return 0

    for name, command, fixer in steps(project, path.relative_to(project)):
        result = run(project, *command)
        if not succeeded(result, fixer):
            sys.stderr.write(
                f"{name} found errors it cannot fix in {path}:\n{result.stdout}{result.stderr}"
            )
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
