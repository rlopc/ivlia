---
name: review-file
description: Explain and review one development tool or configuration file chosen by the user (workflows, justfile, linter, test or editor configuration) - what it does, in short junior-level terms, then whether it meets the Toolchain rules. Use when the user asks to explain or review such a file.
argument-hint: "[file]"
---

# Review a file

File: $ARGUMENTS (if empty, ask the user which file).

1. Explain only the file the user names: what it is, who uses it, when and how. Keep it short and simple, for a junior, and define any technical term in one line. Give more detail only if asked.
2. Review it against the "Toolchain rules" at the top of `docs/standards/repository.md` and the documentation rule in `docs/standards/README.md`. Check each claim: official docs first, then the repository itself (commands run read-only). Use the network only with the user's confirmation, and delegate reading sources to the `researcher` agent. Say which sources were read and how much of each.
3. Report the findings by importance, each with options and a recommendation first. Change nothing until the user decides.
4. When applying a change: Validar first, one branch per topic, docs updated with the code, `just check` green, and the `reviewer` agent before the user reviews the branch.
