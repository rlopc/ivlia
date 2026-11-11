---
name: review-file
description: Explain and review one repository file chosen by the user - what it does, in short junior-level terms, then whether it meets the Toolchain rules. Use when the user asks to explain or review a file.
---

# Review a file

1. Explain only the file the user names: what it is, who uses it, when and how. Keep it short and simple, for a junior, and define any technical term in one line. Give more detail only if asked.
2. Review it against the "Toolchain rules" at the top of `docs/standards/repository.md` and the documentation rule in `docs/standards/README.md`. Check each claim: official docs first, then the repository itself (commands run read-only). Say which sources were read and how much of each.
3. Report the findings by importance, each with options and a recommendation first. Change nothing until the user decides.
4. When applying a change: one branch per topic, docs updated with the code, the checks run, and the `reviewer` agent before the user reviews the branch.
