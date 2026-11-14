# UnvibeCode Engineering Challenge 2026 (Cohort 3)

Submission workspace for the Alphashots.ai UnvibeCode Challenge by Aayush Mishra ([@Aayush-Mishra-11](https://github.com/Aayush-Mishra-11)).

## Overview of Contents

- `ISSUE_TRACK1_SUBMISSION.md`: Detailed bug report documenting how UnvibeCode's Python AST linker currently drops ASGI lifespan context managers (`@asynccontextmanager lifespan`) and teardown routines.
- `PROPOSAL_TRACK2_SUBMISSION.md`: Product proposal for driving daily repeat developer usage using an incremental `unvibecode diff` pre-push check and a branded GitHub PR Action.
- `reproduce_bug.py`: Standalone reproduction script simulating the AST visitor to show how `lifespan()` is missed.
- `solution_ast_linker.py`: Working AST visitor patch that detects `FastAPI(lifespan=...)` and partitions the generator statements across `yield` into startup and teardown workflows.
- `test_solution.py`: Unit tests validating the fix against FastAPI apps.

## Running the Verification Scripts

To run the bug reproduction:
```powershell
python reproduce_bug.py
```

To run the unit tests for the fix:
```powershell
python test_solution.py
```
