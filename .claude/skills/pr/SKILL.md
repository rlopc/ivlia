---
name: pr
description: Create, update, check and merge this repository's pull requests through `.claude/bin/gh-repo.sh`, stacked branches included. Use when the user asks to open a pull request, bring a branch up to date with main, look at CI or a failed run, or merge a pull request.
argument-hint: "[create | update | checks | merge] [branch or PR number]"
---

# Pull requests

How the repository's pull requests are handled: [ci.md](../../../docs/standards/ci.md), [README](../../../docs/standards/README.md#git) and [ai-development.md](../../../docs/standards/ai-development.md#github-access).

## Rules

- Every GitHub call goes through `.claude/bin/gh-repo.sh`, from the repository root; never a bare `gh`. It finds the repository from `origin` and uses its own token.
- Run `gh-repo.sh` and `git push` alone: no pipe, `&&` or redirection. They leave the sandbox only when the whole command matches, so a chained call stays inside and fails. `gh-repo.sh` accepts only the subcommands it lists.
- `git push` and every `gh-repo.sh` write ask the user. Never look for a way around a prompt; if one is refused, stop and say what is missing.
- Titles, bodies and comments are in English.
- Merge only when the user asks for that pull request.

## Create

1. The `reviewer` agent has reviewed the branch ([ai-development.md](../../../docs/standards/ai-development.md)).
2. `git push -u origin <branch>`.
3. Title: Conventional Commits with one of the types and scopes in `.github/workflows/pr-title.yml`. It becomes the squash commit on `main`, so it says what the whole pull request does. Always pass `--title`; never `--fill`, which takes the branch name when there are several commits.
4. Body: the sections of `.github/pull_request_template.md`, with the Validar summary when there is one. Write it to a file in `$TMPDIR` and pass `--body-file`.
5. Base: `main`, or the branch below for a stacked pull request.
6. `.claude/bin/gh-repo.sh pr create --base <base> --head <branch> --title "<title>" --body-file <file>`.

## Update a branch with main

A pull request whose base was squash-merged is retargeted to `main` by GitHub, and no required check runs until its branch gets a new commit ([ci.md](../../../docs/standards/ci.md#rules-for-every-workflow)). Bring `main` in with a merge, never a rebase:

1. `git fetch origin`.
2. Find `B`, the base pull request's last commit: `.claude/bin/gh-repo.sh pr view <base PR> --json headRefOid` (its branch may be deleted). If the branch contains it (`git merge-base --is-ancestor B <branch>`) and `main`'s squash commit has the same tree as `B` (`git diff --quiet B <squash commit>`), merge with `B` as the base, so git does not replay the base's changes against their squash:
   - In one command, since shell variables do not survive between calls: `T=$(git merge-tree --write-tree --merge-base B <branch> origin/main) && C=$(git commit-tree "$T" -p <branch> -p origin/main -m "Merge branch 'main' into <branch>") && git update-ref refs/heads/<branch> "$C" <old tip>`. `merge-tree` exits with 1 on a conflict, which stops the chain: then go to step 3.
   - If the branch is checked out, end the chain with `git merge --ff-only "$C"` instead of `git update-ref`.
3. Otherwise, a normal `git merge origin/main`, or resolve real conflicts in a worktree (`git worktree add`).
4. The sandbox protects `.claude/bin/`: a checkout or merge in the current checkout that changes those files fails. Use a worktree, or ask the user.
5. Check what the merge brought in: lint the conflicting files, and run `uv lock --check` when `uv.lock` changed.
6. `git push origin <branch>`.

## Checks

- `.claude/bin/gh-repo.sh pr checks <number>`. To wait, run it with `--watch` in the background, not a polling loop.
- A failed run: `.claude/bin/gh-repo.sh run view <id> --log-failed` (read the end of its output), then name the cause before acting:
  - A GitHub fault (for example `Service Unavailable`, or runs queued for hours after an incident): re-run (`run rerun`) or cancel (`run cancel`) the run, or push the branch's next commit.
  - A real failure: fix it on the branch.

## Merge

When the user asks: `.claude/bin/gh-repo.sh pr merge <number> --auto --squash`. GitHub merges once the required checks pass. Then update the next stacked pull request, if there is one.
