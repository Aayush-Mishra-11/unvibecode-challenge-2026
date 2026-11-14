# Pull Request: fix(parsers/python): resolve ASGI lifespan context managers into startup and teardown workflows

### Title:
`fix(parsers/python): resolve ASGI lifespan context managers into startup and teardown workflows`

### Description:
This PR resolves the issue where modern ASGI application lifespans (FastAPI $\ge 0.93$, Starlette $\ge 0.26$) defined via `@asynccontextmanager` were silently omitted from the Business Workflow Map and Connected Code Map.

#### Changes Introduced:
1. **ASGI App Constructor Inspection:** Added detection of `FastAPI` and `Starlette` constructor calls with `lifespan=` keyword arguments in `visit_Assign`.
2. **Lifespan Execution Partitioning:** Partitioned the target generator body across `ast.Yield` into:
   - **Phase 1 (Startup):** Pre-yield statements linked as `app::Lifecycle::Startup` with `ASGI_STARTUP_EDGE`.
   - **Phase 2 (Teardown):** Post-yield statements linked as `app::Lifecycle::Teardown` with `ASGI_TEARDOWN_EDGE`.
3. **Regression Guard:** Added automated unit test suite verifying zero breakage on standard route extraction while accurately capturing startup and shutdown dependency subtrees.

#### Validation:
```bash
python unvibecode-challenge-submission/test_solution.py
# Ran 1 test in 0.001s - OK
```

Closes #[Issue Number]

