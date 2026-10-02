# Repository workflow

- Work on the existing `main` branch. The user explicitly requested one main branch on 2026-10-01. Do not create topic branches or extra worktrees unless the user explicitly changes this instruction.
- Before integrating history, verify ancestry and preserve uncommitted work. Delete only branches whose complete history is already reachable from main; never use force deletion to hide unmerged work.
- Commit the completed, relevant work to main. Do not silently include unrelated drafts, running experiment artifacts, databases, or model weights.
- Remote publication is distinct from local integration. Respect any approval-review rejection and disclose a blocked push; do not bypass it or claim local commits were pushed.

- Canonical remote: https://github.com/Seongmiin2/PhysicalAI_masterdegree.git. The local folder name Thesis-Orchestrator is retained for running-process compatibility; do not create a second repository or nested export checkout.
- PhysicalAI source is in physical_ai/src. Use project-relative data paths. Consolidation completed on 2026-10-01: physical_ai/data and physical_ai/checkpoints are real directories inside this project. The old PhysicalAI_mini folder was archived outside the workspace. Never move open experiment data.
