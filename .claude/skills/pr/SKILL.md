---
name: pr
description: Create, update, check and merge this repository's pull requests through GitHub's MCP server, stacked branches included. Use when the user asks to open a pull request, bring a branch up to date with main, look at CI or a failed run, or merge a pull request.
argument-hint: "[create | update | checks | merge] [branch or PR number]"
---

# Pull requests

How the repository's pull requests are handled: [ci.md](../../../docs/standards/ci.md), [README](../../../docs/standards/README.md#git) and [ai-development.md](../../../docs/standards/ai-development.md#github-access).

## Rules

- GitHub is reached only through the `github` MCP server's tools (`mcp__github__*`); `owner` and `repo` come from `git remote get-url origin`. Never `gh` or `curl`.
- Reads run without asking; every write tool asks the user. Never look for a way around a prompt; if one is refused, stop and say what is missing.
- Claude does not push: when a branch needs pushing, give the user the exact command (`git push -u origin <branch>`) and wait.
- Titles, bodies and comments are in English.
- Merge only when the user asks for that pull request.

## Create

1. The `reviewer` agent has reviewed the branch ([ai-development.md](../../../docs/standards/ai-development.md)).
2. The user pushes the branch.
3. Title: Conventional Commits with one of the types and scopes in `.github/workflows/pr-title.yml`. It becomes the squash commit on `main`, so it says what the whole pull request does.
4. Body: the sections of `.github/pull_request_template.md`, with the Validar summary when there is one.
5. Base: `main`, or the branch below for a stacked pull request.
6. `create_pull_request` with that title, body, base and head.

## Update a branch with main

A pull request whose base was squash-merged is retargeted to `main` by GitHub, and no required check runs until its branch gets a new commit ([ci.md](../../../docs/standards/ci.md#rules-for-every-workflow)).

1. Try `update_pull_request_branch`: GitHub merges `main` into the branch and the checks run.
2. If it reports a conflict, merge locally, never with a rebase:
   1. The user runs `git fetch origin`.
   2. Find `B`, the base pull request's last commit (`pull_request_read`, method `get`, its head SHA). If the branch contains it (`git merge-base --is-ancestor B <branch>`) and `main`'s squash commit has the same tree as `B` (`git diff --quiet B <squash commit>`), merge with `B` as the base, so git does not replay the base's changes against their squash. In one command, since shell variables do not survive between calls: `T=$(git merge-tree --write-tree --merge-base B <branch> origin/main) && C=$(git commit-tree "$T" -p <branch> -p origin/main -m "Merge branch 'main' into <branch>") && git update-ref refs/heads/<branch> "$C" <old tip>`; end it with `git merge --ff-only "$C"` instead when the branch is checked out. `merge-tree` exits with 1 on a conflict, which stops the chain.
   3. Otherwise, or on a conflict, a normal `git merge origin/main`, resolving real conflicts in a worktree (`git worktree add`) when the checkout cannot be switched.
   4. Check what the merge brought in: lint the conflicting files, and run `uv lock --check` when `uv.lock` changed.
   5. The user pushes the branch.

## Checks

- `pull_request_read` with method `get_check_runs`.
- A failed run: `get_job_logs` for the failed job, then name the cause before acting:
  - A GitHub fault (for example `Service Unavailable`, or runs queued for hours after an incident): re-run or cancel it with `actions_run_trigger`.
  - A real failure: fix it on the branch.

## Merge

When the user asks: `merge_pull_request` with the squash method. The ruleset on `main` refuses the merge until the required checks pass. Then update the next stacked pull request, if there is one.
