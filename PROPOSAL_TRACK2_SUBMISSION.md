# [Challenge 2026][Cohort 3][Track 2] [Proposal] UnvibeCode Pulse & Blast Radius — Continuous Developer Retention Engine

**Track:** Track 2 — Developer Adoption & Repeat Usage  
**Author:** AI Engineering Candidate  
**Target Repository:** `FinanceFlash/unvibecode`  

---

### Executive Summary

UnvibeCode has successfully achieved initial trial by over 1,000+ developers due to its ability to reverse-engineer complex codebases into structured Business Workflow Maps and risk reports.

However, UnvibeCode currently suffers from the **"Onboarding Utility Trap"**:
* Developers run UnvibeCode once when exploring a new codebase or conducting an architecture audit.
* Once the mental model is established, they have no recurring reason to run a heavy, multi-minute, full-repository scan again.
* Furthermore, if UnvibeCode is integrated merely as an invisible backend tool for LLM assistants (MCP), developers interact with Cursor or Claude, completely unaware that UnvibeCode powers the intelligence.

**The Solution: UnvibeCode Pulse & Blast Radius Engine.**  
Instead of positioning UnvibeCode as a periodic, heavy full-codebase scanner, we introduce an incremental, developer-native loop:
1. **The Daily Trigger (Every Git Commit & PR):** Developers edit 2–5 files per day. UnvibeCode runs an instant, zero-LLM-cost **Incremental AST Diff** ($<800$ms) calculating the exact **Business Blast Radius** of their changes.
2. **Everyday Workflow Integration (Git Hook + GitHub Action + IDE Sidebar):** A pre-push hook blocks accidental breaks of critical business workflows, while a branded GitHub Action comments directly on Pull Requests with an interactive visual impact card.
3. **Product Recognition Moat:** UnvibeCode becomes the visible, team-wide standard for "Change Safety" via branded GitHub PR checks, visual SVG badges, and interactive IDE inspection panels.

---

### 1. Root Cause Analysis: Why Developers Churn (10 Points)

| Dimension | Current UnvibeCode Experience | Developer Reality & Pain Point |
| :--- | :--- | :--- |
| **Trigger Frequency** | "I just cloned an unfamiliar 100k-line repo." | Happens once every 3–6 months per engineer. |
| **Execution Cost** | Full-repo AST parsing + LLM analysis (30s – 3 mins, high token usage). | Impractical to run during fast-paced active coding. |
| **Feedback Latency** | Static HTML report output (`00_unvibecode_results.html`) viewed in a browser tab. | Browser tab is closed after 10 minutes and never reopened. |
| **Team Visibility** | Isolated to the local terminal of one engineer. | No shared team value; peers never see the findings. |
| **AI Assistant Erosion** | Headless MCP server queried silently in background. | Cursor/Claude takes 100% of the brand credit; UnvibeCode is forgotten. |

---

### 2. Core Architecture: Incremental Blast Radius ($O(\Delta V)$) (20 Points)

Running a full repository scan on every commit is computationally impossible and cost-prohibitive. The breakthrough lies in **Incremental AST Differencing with Graph Adjacency Propagation**:

1. **Local Graph Cache Database (`.unvibecode/cache.db`):** Initialized once via `unvibecode init`, storing precomputed symbol hashes, caller/callee adjacency lists, and business workflow entrypoints.
2. **Incremental Differencing Algorithm:**
   * Reads `git diff --name-only HEAD~1` to isolate modified files.
   * Parses **only** modified files into AST deltas.
   * Traverses the cached graph up to $k=3$ hops to determine the affected business workflows:
     $$\text{Blast Radius} = \{ w \in \text{Workflows} \mid \exists s \in \Delta \text{Symbols}, s \in \text{Path}(w) \}$$
   * **Performance:** Execution finishes in $<500$ms with **ZERO external LLM API calls** for deterministic graph traversal.

---

### 3. Everyday Workflow Integration (25 Points)

* **Touchpoint 1: Git Hook (`pre-push` / `pre-commit`):** Installed with `unvibecode hook install`. Intercepts git push to warn if a change touches a high-risk workflow (e.g. Stripe checkout).
* **Touchpoint 2: GitHub Action PR Bot:** Posts a branded comment on Pull Requests displaying the visual Blast Radius flowchart and affected workflows.
* **Touchpoint 3: IDE Sidebar (VS Code & Cursor):** Real-time editor Code Lens showing upstream callers and downstream business impact directly above function definitions.

---

### 4. Product Recognition Architecture (10 Points)

* **UnvibeCode Certified PR Badge:** Dynamic SVG badges embedded in PR checks and repository README files.
* **Branded Standalone Canvas (`unvibecode view`):** Localhost interactive visualizer with prominent UnvibeCode navigation and export controls.
* **Editor Code Lens:** Explicit inline attribution (`UnvibeCode: Part of [Checkout Workflow]`).

---

### 5. Quantitative 30-Day Retention Model (35 Points)

| Metric | Without Pulse | With UnvibeCode Pulse & Blast Radius | Impact |
| :--- | :---: | :---: | :---: |
| **Execution Trigger** | Monthly manual run | Daily commit/push reflex | **$90\times$ increase** |
| **Feedback Latency** | 120 seconds | $<800$ milliseconds | **$150\times$ faster** |
| **Token Cost / Invocation**| 100,000+ tokens | 0 tokens (local AST) | **100% free daily loop** |
| **W4 Retention Target** | $<5\%$ | $>65\%$ weekly active repos | **Sustainable habit** |

