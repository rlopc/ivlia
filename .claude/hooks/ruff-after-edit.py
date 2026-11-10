"""PostToolUse hook: format and lint each Python file Claude edits in backend/.

It runs `ruff format` and `ruff check --fix` on the file, through the locked
uv environment. Errors that ruff cannot fix go back to Claude (exit 2), so it
corrects them in the next step. Other files are ignored.

Input: the hook JSON on stdin, with `tool_input.file_path`.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def ruff(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    command = ["mise", "exec", "--", "uv", "run", "--locked", "--quiet"]
    command += ["--project", str(project / "backend"), "ruff", *args]
    return subprocess.run(command, cwd=project, capture_output=True, text=True, check=False)


def main() -> int:
    payload = json.load(sys.stdin)
    file_path = payload.get("tool_input", {}).get("file_path")
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd())).resolve()
    if not file_path:
        return 0
    path = Path(file_path).resolve()
    if path.suffix != ".py" or not path.is_relative_to(project / "backend") or not path.exists():
        return 0

    formatted = ruff(project, "format", "--quiet", str(path))
    if formatted.returncode != 0:
        sys.stderr.write(f"ruff format failed on {path}:\n{formatted.stdout}{formatted.stderr}")
        return 2
    checked = ruff(project, "check", "--fix", "--quiet", "--output-format", "concise", str(path))
    if checked.returncode != 0:
        sys.stderr.write(f"ruff found errors it cannot fix:\n{checked.stdout}{checked.stderr}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
