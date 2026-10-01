# Repository workflow

- Work on the existing `main` branch. The user explicitly requested one main branch on 2026-10-01. Do not create topic branches or extra worktrees unless the user explicitly changes this instruction.
- Before integrating history, verify ancestry and preserve uncommitted work. Delete only branches whose complete history is already reachable from main; never use force deletion to hide unmerged work.
- Commit the completed, relevant work to main. Do not silently include unrelated drafts, running experiment artifacts, databases, or model weights.
- Remote publication is distinct from local integration. Respect any approval-review rejection and disclose a blocked push; do not bypass it or claim local commits were pushed.
