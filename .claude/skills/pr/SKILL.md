---
name: pr
description: Create, update, check and merge this repository's pull requests through `.claude/bin/gh-repo`, stacked branches included. Use when the user asks to open a pull request, bring a branch up to date with main, look at CI or a failed run, or merge a pull request.
argument-hint: "[create | update | checks | merge] [branch or PR number]"
---

# Pull requests

How the repository's pull requests are handled: [ci.md](../../../docs/standards/ci.md), [README](../../../docs/standards/README.md#git) and [ai-development.md](../../../docs/standards/ai-development.md#github-access).

## Rules

- Every GitHub call goes through `.claude/bin/gh-repo`, from the repository root; never a bare `gh`. It finds the repository from `origin` and uses its own token.
- `git push` and every `gh-repo` write ask the user. Never look for a way around a prompt; if one is refused, stop and say what is missing.
- Titles, bodies and comments are in English.
- Merge only when the user asks for that pull request.

## Create

1. The `reviewer` agent has reviewed the branch ([ai-development.md](../../../docs/standards/ai-development.md)).
2. `git push -u origin <branch>`.
3. Title: Conventional Commits with one of the types and scopes in `.github/workflows/pr-title.yml`. It becomes the squash commit on `main`, so it says what the whole pull request does. Always pass `--title`; never `--fill`, which takes the branch name when there are several commits.
4. Body: the sections of `.github/pull_request_template.md`, with the Validar summary when there is one. Write it to a file in `$TMPDIR` and pass `--body-file`.
5. Base: `main`, or the branch below for a stacked pull request.
6. `.claude/bin/gh-repo pr create --base <base> --head <branch> --title "<title>" --body-file <file>`.

## Update a branch with main

A pull request whose base was squash-merged is retargeted to `main` by GitHub, and no required check runs until its branch gets a new commit ([ci.md](../../../docs/standards/ci.md#rules-for-every-workflow)). Bring `main` in with a merge, never a rebase:

1. `git fetch origin`.
2. If the branch contains the old base branch's tip `B` (`git merge-base --is-ancestor B <branch>`) and `main`'s squash commit has the same tree as `B` (`git diff --quiet B <squash commit>`), merge with `B` as the base, so git does not replay the base's changes against their squash:
   - `T=$(git merge-tree --write-tree --merge-base B <branch> origin/main)`.
   - `C=$(git commit-tree "$T" -p <branch> -p origin/main -m "Merge branch 'main' into <branch>")`.
   - Move the branch: `git merge --ff-only "$C"` if it is checked out, otherwise `git update-ref refs/heads/<branch> "$C" <old tip>`.
3. Otherwise, a normal `git merge origin/main`. Resolve real conflicts in a worktree (`git worktree add`) when the checkout cannot be switched.
4. Check what the merge brought in: lint the conflicting files, and run `uv lock --check` when `uv.lock` changed.
5. `git push origin <branch>`.

## Checks

- `.claude/bin/gh-repo pr checks <number>`. To wait, run it with `--watch` in the background, not a polling loop.
- A failed run: `.claude/bin/gh-repo run view <id> --log-failed | tail -n 40`, then name the cause before acting:
  - A GitHub fault (for example `Service Unavailable`, or runs queued for hours after an incident): re-run or cancel the run, or push the branch's next commit.
  - A real failure: fix it on the branch.

## Merge

When the user asks: `.claude/bin/gh-repo pr merge <number> --auto --squash`. GitHub merges once the required checks pass. Then update the next stacked pull request, if there is one.
