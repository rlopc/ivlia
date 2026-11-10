# ivlia

100 % local personal AI assistant to manage knowledge of any type (Apple M2 Max, 64 GB). It is designed and will be built here with Claude Code, in small slices the user can supervise, with production-level practices from day one.

## Where things are

- The design lives in `docs/` (Spanish). Start at `docs/00-indice.md`; it links to the 10 topic documents.
- Read only the document for the area you are working on. Do not load all of them.

## Current state

- **Fase 0** in progress: follow `docs/plan/phase-0.md`. Steps 1 (repository and `just`) and 2 (backend) are done; step 3 (CLI) is in progress, with its PR in review; next step: frontend.
- The backend is the Python package in `backend/`, CLI included: [backend](docs/standards/backend.md), [API](docs/standards/api.md). Decisions: [decision map](docs/decisions/README.md).
- Set up with `mise trust`, `mise install` and `just setup`; run every local check with `just check`.
- How the project is built and checked: the standards document, `docs/standards/README.md`.
- `.claude/` holds the `researcher` agent and `research` skill (with a bash guard hook), the `validar` skill, the `reviewer` agent, the ruff hook after Python edits, the rules per zone (`.claude/rules/`) and the OpenSpec skills and commands (generated: regenerate with `openspec update`, never edit them by hand).

## How to work with the user

- Talk to the user in Spanish. Code, comments, commits, PRs and repository documentation are in English (the existing `docs/` and `.claude/` are in Spanish and will be translated later; the Spanish versions are then removed).
- Be brief and simple. Answer only what is asked. No apologies, no filler.
- Ask at most one question per turn, with 2-4 options and your recommendation first. The user usually answers with a letter or "ok".
- If the user says they do not understand, explain it again more simply.
- Do not write unconfirmed facts into documents. Check current documentation and versions instead of relying on memory.

## Rules

- Fase 0 is built **without** spec-driven development; OpenSpec is used from slice 2 ([ai-development](docs/standards/ai-development.md)).
- Before each step run Validar with the `validar` skill, and before the user reviews a branch run the `reviewer` agent ([ai-development](docs/standards/ai-development.md)).
- Git, PRs, the documentation rule and the versions policy: [standards index](docs/standards/README.md).
- Tools, hooks and generated files: [repository](docs/standards/repository.md). Threat model: [security](docs/standards/security.md).

## Do not do without being asked

- Push, delete files, use the network or handle secrets without the user's confirmation. Installing dependencies from the lockfile is allowed; adding or upgrading dependencies is not.
- Read or write outside this repository. Real user data (notes, memory, secrets) never enters it.
- Change decisions already in the design without discussing it first. When a problem conflicts with the design, compare keeping the design and finding a solution within it against changing the design, and recommend one with its reasons. Open decisions are listed in `docs/10-plan-y-pendientes.md`; raise them with the user when their moment comes.
