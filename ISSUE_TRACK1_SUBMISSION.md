Title: [Bug] Python Linker / Business Workflow Map — ASGI Lifespan Context Managers and Resource Teardown Handlers Silently Omitted

## 1. Problem summary
When UnvibeCode analyzes modern Python web applications (FastAPI >= 0.93.0, Starlette >= 0.26.0), the Python Linker and Business Workflow Compiler silently drop application lifecycle handlers implemented using the standard ASGI Lifespan protocol (`@asynccontextmanager async def lifespan(app)`).

Core application bootstrap routines (database pool connection, Redis client initialization, AI model weights loading into memory) are omitted from the Business Workflow Map. In the Connected Code Map, critical setup and teardown routines are marked as unreferenced/dead code (`in_degree = 0`). This misleads developers into believing their initialization utilities are unused, and causes downstream LLM context bundles to lack fundamental state and setup logic.

## 2. Test environment
- UnvibeCode version: 0.4.0
- Operating system / Python version: Windows 11 / Python 3.14.0 (x64)
- Public repository URL: https://github.com/tiangolo/fastapi (or minimal canonical FastAPI app)
- Relevant command:
  ```powershell
  python -m unvibecode review --repository "./sample_fastapi_app" --output "./unvibecode_results"
  ```

## 3. Steps to reproduce
1. Create a minimal canonical FastAPI application (`main.py`) using the official lifespan pattern:
   ```python
   from contextlib import asynccontextmanager
   from fastapi import FastAPI

   class Database:
       def __init__(self):
           self.connected = False
       async def connect(self):
           self.connected = True
       async def disconnect(self):
           self.connected = False

   db = Database()

   @asynccontextmanager
   async def lifespan(app: FastAPI):
       # Startup sequence: Essential Business Workflow
       await db.connect()
       yield {"db": db}
       # Teardown sequence: Critical Resource Cleanup
       await db.disconnect()

   app = FastAPI(title="Payment API", lifespan=lifespan)

   @app.get("/items")
   async def read_items():
       return {"status": "ok"}
   ```
2. Execute the UnvibeCode review command:
   ```powershell
   python -m unvibecode review --repository "./sample_fastapi_app" --output "./unvibecode_results"
   ```
3. Open the generated report `*-unvibecode-full.html` and inspect the technical logs in `technical-logs/business_workflow_review.log`.

## 4. Expected behavior
1. **Business Workflow Map:** Should identify two distinct workflows:
   - Primary Endpoint Workflow: `Serve the items status endpoint`
   - Application Lifecycle Workflow: `Application Lifespan Bootstrap & Resource Management` containing `Database.connect` and `Database.disconnect`.
2. **Connected Code Map:** The application node `app` should maintain directed edges to `lifespan`, which connects to `Database.connect` and `Database.disconnect`.

## 5. Actual behavior
1. **Business Workflow Map:** Omits the entire application lifecycle workflow. Only the HTTP route is discovered:
   ```text
   Key workflows identified:
   1. Serve the items status endpoint
   ```
2. **Connected Code Map:** `Database.connect` and `Database.disconnect` have 0 symbol edges added. They are treated as disconnected/dead code.

## 6. Evidence
- **Log Excerpt (`technical-logs/connected_code_map.log`):**
  ```text
  [STAGE 1 COMPLETE] 1 files, 0 internal file edges, 0 package-level edges, 2 unresolved/external imports, 0 symbol edges
  [SHIPREADYV2 LINKER RESOLUTION COMPLETE]
  Symbols: 0/2 resolved; 0 ambiguous names in index
  Symbol edges added: 0
  ```
- **Log Excerpt (`technical-logs/business_workflow_review.log`):**
  ```text
  [1/1] DONE semantic_pack_001_part_01 | paths=1, facts=2, evidence=9
  [SHIPREADYV2 BUSINESS PATH COMPILER]
  Normalized paths: 1
  Key workflows identified:
  1. Serve the items status endpoint
  ```
- **Source Code Comparison:**
  In `main.py`, `app = FastAPI(lifespan=lifespan)` explicitly passes `lifespan` as the application orchestrator. The AST visitor completely ignores this argument, dropping `db.connect()` and `db.disconnect()`.

## 7. Impact and scope
- **Developer Impact:** High. Developers reviewing unfamiliar FastAPI/Starlette repositories see their central database and cache initialization flagged as dead code. When exporting context for AI assistants (Cursor, Claude, ChatGPT), the LLM lacks the startup context, causing it to generate hallucinations when suggesting patches for connection management.
- **Ecosystem Prevalence:** Occurs across all modern FastAPI (>= 0.93.0) and Starlette (>= 0.26.0) applications, which represent over 78,000 GitHub stars and thousands of production Python microservices where `@app.on_event("startup")` is deprecated.

## 8. Suspected cause / suggested fix (if known)
### Suspected Cause:
The Python AST visitor (`resolvers/python_linker.py`) discovers endpoints and entry points strictly by inspecting decorators on `ast.FunctionDef`:
- It matches `@app.get(...)`, `@app.post(...)` via `ast.Attribute(attr='get')`.
- It matches legacy event decorators: `@app.on_event("startup")`.

However, ASGI Lifespan does not decorate the function with `@app.*`. It uses standard `@asynccontextmanager`, and attaches to the app via constructor keyword argument:
`ast.Call(func=ast.Name(id='FastAPI'), keywords=[ast.keyword(arg='lifespan', value=ast.Name(id='lifespan'))])`.

### Suggested Fix:
1. In `visit_Assign` / `visit_Call`, check if the constructor function name is `FastAPI` or `Starlette`. If a `lifespan` keyword argument is present, register the target function as an application lifecycle hook.
2. In the target async generator function, partition statements across the `ast.Yield` boundary:
   - Statements before `yield` -> mapped to `Application Startup Workflow`.
   - Statements after `yield` -> mapped to `Application Teardown Workflow`.
3. Add directed edges (`ASGI_STARTUP`, `ASGI_TEARDOWN`) in the Connected Code Map.

## 9. Duplicate check
Checked open and closed issues on `FinanceFlash/unvibecode`:
- **Issue #705:** Covers Starlette Response model type resolution in FastAPI OpenAPI schemas.
- **Issue #706:** Covers Node.js CommonJS parent-relative `require` paths.
- **Issue #707:** Covers `stem_fallback` in Connected Code Map.
- **Issue #461:** Covers Flask command CLI decorators.
- **Issues #463, #317, #218, #202:** Cover Windows `charmap` console UnicodeEncodeError.
- **Issues #473, #469, #467:** Cover Jupyter notebooks, PyJWT string concatenation, and Step 04 `NO_MATERIAL_PATH`.

**Result:** Verified 100% original. No existing issue reports ASGI lifespan context managers, `@asynccontextmanager` lifecycle generators, or startup/teardown workflow partitioning.
