# ivlia

100 % local personal AI assistant to manage knowledge of any type (Apple M2 Max, 64 GB). It is designed and will be built here with Claude Code, in small slices the user can supervise, with production-level practices from day one.

## Where things are

- The design lives in `docs/` (Spanish). Start at `docs/00-indice.md`; it links to the 10 topic documents.
- Read only the document for the area you are working on. Do not load all of them.

## Current state

- Design only. No code, no git repository, no `justfile` yet.
- Next step: **Fase 0**, the full development environment (see `docs/09-ia-en-el-desarrollo.md`, "Modo de trabajo de la fase 0", and `docs/10-plan-y-pendientes.md`). Follow `docs/plan/phase-0.md`.
- `.claude/` already holds a `researcher` agent and a `research` skill (with a bash guard hook) that predate this project. Leave them untouched unless asked.

## How to work with the user

- Talk to the user in Spanish. Code, comments, commits, PRs and repository documentation are in English (the existing `docs/` and `.claude/` are in Spanish and will be translated later; the Spanish versions are then removed).
- Be brief and simple. Answer only what is asked. No apologies, no filler.
- Ask at most one question per turn, with 2-4 options and your recommendation first. The user usually answers with a letter or "ok".
- If the user says they do not understand, explain it again more simply.
- Do not write unconfirmed facts into documents. Check current documentation and versions instead of relying on memory.

## Rules for Fase 0

These rules summarize `docs/08` and `docs/09` until the standards document exists. In the first PR, replace them with links to it.

- Fase 0 is built **without** spec-driven development (no OpenSpec cycle). OpenSpec is installed and configured in Fase 0 and used from slice 2.
- Work in small PRs, one per step: repo and `just`, backend, CLI, frontend, CI, release.
- Before each step, run a **Validar** step: a read-only subagent checks current official docs, versions and best practices for the tools involved and compares them with the design and the repo. It returns a short report (confirmed / changed / risks). The user sees it before you start.
- Each PR leaves `main` working, with `just check` green. The user reviews every PR.
- Git: short branches, squash into `main`, PR title `<type>(<area>): <summary>` (Conventional Commits; areas: backend, frontend, cli, docs, ci, repo, deps).
- The standards document is created in the first PR, and every later PR that changes tools or practices updates it. ADRs and the decision map start with the first decision that needs them (the LangGraph ADR, in the backend step).

## Do not do without being asked

- Push, delete files, use the network or handle secrets without the user's confirmation. Installing dependencies from the lockfile is allowed; adding or upgrading dependencies is not.
- Read or write outside this repository. Real user data (notes, memory, secrets) never enters it.
- Change decisions already in the design without discussing it first. When a problem conflicts with the design, compare keeping the design and finding a solution within it against changing the design, and recommend one with its reasons. Open decisions are listed in `docs/10-plan-y-pendientes.md`; raise them with the user when their moment comes.
