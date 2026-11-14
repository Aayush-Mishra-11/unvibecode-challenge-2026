Title: [Bug] Python Linker — ASGI Lifespan handlers and teardown logic omitted from workflow map

## 1. Problem summary
When running UnvibeCode review on modern FastAPI and Starlette projects, the tool does not detect application startup and shutdown handlers defined using the standard `@asynccontextmanager` lifespan pattern (`FastAPI(lifespan=...)`).

Because of this, core initialization routines (such as database connection pools, Redis clients, and background tasks) are completely missing from the Business Workflow Map. In the Connected Code Map, functions like `connect()` and `disconnect()` end up showing 0 incoming edges as if they are unused dead code. This is confusing when exploring an unfamiliar codebase, and any exported LLM context ends up missing how the database/app state is actually initialized.

## 2. Test environment
- UnvibeCode version: 0.4.0
- Operating system / Python version: Windows 11 / Python 3.14.0
- Public repository URL and commit or release: https://github.com/tiangolo/fastapi (also reproduced on canonical FastAPI 0.115 structure)
- Relevant command:
  ```powershell
  python -m unvibecode review --repository "./sample_fastapi_app" --output "./unvibecode_results"
  ```

## 3. Steps to reproduce
1. Create a test folder with a standard FastAPI app (`main.py`):
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
       # Startup
       await db.connect()
       yield {"db": db}
       # Teardown
       await db.disconnect()

   app = FastAPI(title="Sample Service", lifespan=lifespan)

   @app.get("/items")
   async def get_items():
       return {"status": "ok"}
   ```
2. Run the review command:
   ```powershell
   python -m unvibecode review --repository "./sample_fastapi_app" --output "./unvibecode_results"
   ```
3. Open the generated `*-unvibecode-full.html` and check `technical-logs/business_workflow_review.log`.

## 4. Expected behavior
- The Business Workflow Map should detect an application lifecycle / bootstrap workflow containing `Database.connect` and `Database.disconnect`.
- The Connected Code Map should connect the `app` instance to `lifespan`, linking callers to `connect()` and `disconnect()`.

## 5. Actual behavior
- The Business Workflow Map only picks up the route handler:
  ```text
  Key workflows identified:
  1. Serve the items status endpoint
  ```
  The startup and teardown sequence is completely omitted.
- In `connected_code_map.log`, `Database.connect` and `Database.disconnect` have 0 symbol edges added and appear unreferenced.

## 6. Evidence
- From `technical-logs/connected_code_map.log`:
  ```text
  [STAGE 1 COMPLETE] 1 files, 0 internal file edges, 0 package-level edges, 2 unresolved/external imports, 0 symbol edges
  [SHIPREADYV2 LINKER RESOLUTION COMPLETE]
  Symbols: 0/2 resolved; 0 ambiguous names in index
  Symbol edges added: 0
  ```
- From `technical-logs/business_workflow_review.log`:
  ```text
  [1/1] DONE semantic_pack_001_part_01 | paths=1, facts=2, evidence=9
  [SHIPREADYV2 BUSINESS PATH COMPILER]
  Normalized paths: 1
  Key workflows identified:
  1. Serve the items status endpoint
  ```
- Source comparison: In `main.py`, `app = FastAPI(lifespan=lifespan)` explicitly connects the lifespan function to the app. The AST visitor misses this keyword argument and never registers the lifecycle edges.

## 7. Impact and scope
- Who is affected: Any developer using UnvibeCode on modern FastAPI (>= 0.93.0) or Starlette (>= 0.26.0) applications.
- Why it matters: In modern FastAPI services, `@app.on_event("startup")` has been deprecated for a long time. Almost all modern production codebases use `@asynccontextmanager` lifespans for database pooling, caching, and model loading. When UnvibeCode marks these methods as unreferenced, it degrades confidence in the code map and starves downstream LLMs of application bootstrap context.

## 8. Suspected cause / suggested fix (if known)
### Suspected Cause:
Looking at the AST visitor pattern, route and event discovery seems to check decorators on `FunctionDef`:
- It matches `@app.get` / `@app.post` by checking `decorator.func.attr`.
- It matches deprecated `@app.on_event("startup")`.

With ASGI lifespans:
1. The function uses `@asynccontextmanager`, not an `@app` attribute.
2. The function is passed as a keyword argument to the constructor: `FastAPI(lifespan=lifespan)`.
3. Startup and shutdown are separated by `yield`.

### Suggested Fix:
1. In the AST visitor (`visit_Assign` or `visit_Call`), detect when `FastAPI(...)` or `Starlette(...)` is initialized with a `lifespan` keyword argument.
2. Resolve that function and split its body across the `ast.Yield` node:
   - Code before `yield` -> Startup workflow.
   - Code after `yield` -> Teardown workflow.
3. Add edges connecting the application node to both branches in the graph.

## 9. Duplicate check
I searched existing issues and pull requests before submitting:
- Issue #705 deals with Starlette `Response` import mapping to FastAPI OpenAPI model.
- Issue #706 deals with Node.js CommonJS `require` relative paths.
- Issue #707 deals with `stem_fallback` in Connected Code Map.
- Issue #461 deals with Flask command decorators.
- Issues #463 and #317 deal with Windows console encoding.
- Issues #473 and #469 deal with Jupyter notebooks and PyJWT text concatenation.

None of the existing issues cover ASGI Lifespan context managers or startup/teardown AST linking.
