# UnvibeCode Engineering Challenge 2026 (Cohort 3) — Final Submission Package

This directory contains the complete, tested, and validated submission package for the **Alphashots.ai UnvibeCode Engineering Challenge 2026**.

## Directory Contents

| File | Purpose | Status |
| :--- | :--- | :---: |
| `reproduce_bug.py` | Minimal Reproducible Example demonstrating the AST Lifespan bug | **Verified** |
| `solution_ast_linker.py` | Production patch adding ASGI Lifespan & Teardown partitioning | **Verified** |
| `test_solution.py` | Automated unit test suite with 100% pass rate | **Passing** |
| `ISSUE_TRACK1_SUBMISSION.md` | Ready-to-post GitHub Issue text for Track 1 | **Ready** |
| `PULL_REQUEST_TRACK1.md` | Ready-to-post Pull Request description for Track 1 | **Ready** |
| `PROPOSAL_TRACK2_SUBMISSION.md` | Complete 100-point Proposal for Track 2 | **Ready** |

---

## How to Test Locally

Run the reproduction script:
```powershell
python reproduce_bug.py
```
*(Demonstrates how current decorator visitors miss `lifespan` and drop startup/shutdown calls).*

Run the unit test verifying the fix:
```powershell
python test_solution.py
```
*(Confirms `app::Lifecycle::Startup` and `app::Lifecycle::Teardown` are properly extracted without regression).*

---

## How to Submit on GitHub & Form

### Track 1 Submission (GitHub Issue / PR):
1. Navigate to: `https://github.com/FinanceFlash/unvibecode/issues/new`
2. Title:
   ```text
   [Challenge 2026][Cohort 3][Track 1] [Bug] Python Linker: ASGI Lifespan Context Managers and Resource Teardown Handlers Silently Omitted from Workflow Map
   ```
3. Copy the markdown content from `ISSUE_TRACK1_SUBMISSION.md` and paste it as the issue description.
4. (Optional Pull Request): Fork the repository, create branch `fix/asgi-lifespan-linker`, apply the changes from `solution_ast_linker.py`, and submit a PR using `PULL_REQUEST_TRACK1.md`.

### Track 2 Submission (Proposal):
1. Title:
   ```text
   [Challenge 2026][Cohort 3][Track 2] [Proposal] UnvibeCode Pulse & Blast Radius — Continuous Developer Retention Engine
   ```
2. Copy the content of `PROPOSAL_TRACK2_SUBMISSION.md` into the official challenge submission form or GitHub Issue discussion.

