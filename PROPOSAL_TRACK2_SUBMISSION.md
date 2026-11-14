# Track 2 Proposal: UnvibeCode Blast Radius & PR Impact Engine
**Submitted by:** Aayush Mishra (GitHub: @Aayush-Mishra-11)

---

### 1. Recommended Approach: UnvibeCode Blast Radius (Pre-Push & PR Action)

My recommendation is to turn UnvibeCode from a heavy, one-time full codebase scanner into an everyday **"Blast Radius" check on Git commits and Pull Requests**.

When I ran UnvibeCode on my local repository, generating the full report was great for the initial walkthrough. But once I understood the structure, I had no reason to run a full 2-minute review again while actively writing code. 

Instead of waiting for a developer to clone a new repository every 6 months, UnvibeCode should run automatically when developers make daily changes:
- **Local Hook:** A lightweight `unvibecode diff` command (run via a git `pre-push` hook) that takes only the modified files from `git diff`, checks the AST against a locally cached graph, and instantly shows which business workflows are touched in under 1 second.
- **Branded GitHub PR Action:** A GitHub Action that comments on open PRs with an interactive visual impact summary: *"UnvibeCode Blast Radius: 2 business workflows affected, 0 breaking risks detected"*.

---

### 2. Supporting Points

1. **Fits the natural daily habit loop without performance friction:**
   Running a full repository analysis on every commit is impossible—it takes 30 to 120 seconds and uses too many tokens. By computing the AST diff only on the 2–3 files the developer just edited, the check finishes in under 800ms with zero LLM API calls for the deterministic graph traversal. Developers get instant feedback before pushing code: *"Did my change to `auth.py` accidentally affect the checkout workflow 3 modules away?"*

2. **Solves the brand recognition problem (avoids the invisible MCP trap):**
   If UnvibeCode only works as a hidden MCP server inside Cursor or Claude, developers will give all the credit to Cursor and forget UnvibeCode exists. By putting a distinct UnvibeCode comment and SVG status check right on the GitHub Pull Request, every engineer and reviewer on the team sees the UnvibeCode name and interactive diagram every single day during code reviews.

3. **Creates a continuous reason to return:**
   Full repository onboarding only happens once. But writing code, reviewing pull requests, and checking for breaking changes happens 5 to 10 times a day. Tying UnvibeCode's graph intelligence to PR impact analysis turns it from a "one-time audit utility" into a daily code-safety companion.

---

### 3. Implementation Plan

1. **Build first:** Implement a `.unvibecode/cache.db` local graph cache and an `unvibecode diff` CLI command that parses `git diff --name-only` to identify affected downstream workflows in <1 second.
2. **Where to integrate:** Package it into a one-command git hook (`unvibecode hook install`) and a reusable GitHub Action (`unvibecode/blast-radius-action`) that posts PR impact comments.
3. **How to test repeat usage:** Track weekly active repositories in CI running the action on PRs, and measure whether developers click the workflow links in PR comments or fix flagged workflow breaks before merging.
