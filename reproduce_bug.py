"""
Reproduction script demonstrating the defect in decorator-based AST linking for modern Python ASGI applications.

Defect:
When an application uses the modern ASGI Lifespan protocol (@asynccontextmanager lifespan)
instead of deprecated @app.on_event("startup") / @app.on_event("shutdown"),
naive AST visitors only checking function decorator_list fail to register the lifecycle
entry point, dropping startup and teardown operations from the workflow graph.
"""

import ast
from typing import Dict, List, Set, Tuple


class NaiveUnvibeCodeVisitor(ast.NodeVisitor):
    """
    Simulates UnvibeCode's existing Python AST visitor that scans
    for route decorators and legacy event decorators.
    """
    def __init__(self):
        self.routes: List[str] = []
        self.lifecycle_hooks: List[str] = []
        self.function_calls: Dict[str, List[str]] = {}
        self.current_func: str = ""

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._check_decorators(node.name, node.decorator_list)
        old_func = self.current_func
        self.current_func = node.name
        self.generic_visit(node)
        self.current_func = old_func

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._check_decorators(node.name, node.decorator_list)
        old_func = self.current_func
        self.current_func = node.name
        self.generic_visit(node)
        self.current_func = old_func

    def _check_decorators(self, func_name: str, decorators: list):
        for dec in decorators:
            # Check for @app.get(...), @app.post(...)
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                if dec.func.attr in ("get", "post", "put", "delete", "patch"):
                    self.routes.append(func_name)
                # Check for legacy @app.on_event("startup")
                elif dec.func.attr == "on_event" and dec.args:
                    event_type = getattr(dec.args[0], "value", "unknown")
                    self.lifecycle_hooks.append(f"{func_name}:{event_type}")

    def visit_Call(self, node: ast.Call):
        if self.current_func:
            target_name = ""
            if isinstance(node.func, ast.Attribute):
                target_name = f"{getattr(node.func.value, 'id', '')}.{node.func.attr}"
            elif isinstance(node.func, ast.Name):
                target_name = node.func.id
            if target_name:
                self.function_calls.setdefault(self.current_func, []).append(target_name)
        self.generic_visit(node)


def test_reproduction():
    fastapi_sample = """
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Essential startup bootstrap:
    await db.connect()
    yield {"db": db}
    # Essential teardown cleanup:
    await db.disconnect()

app = FastAPI(title="Production Service", lifespan=lifespan)

@app.get("/users")
async def get_users():
    return await db.fetch_all("SELECT * FROM users")
"""

    tree = ast.parse(fastapi_sample)
    visitor = NaiveUnvibeCodeVisitor()
    visitor.visit(tree)

    print("=" * 60)
    print("NAIVE AST VISITOR RESULTS (Current UnvibeCode Behavior):")
    print(f"Registered HTTP Routes: {visitor.routes}")
    print(f"Registered Lifecycle Hooks: {visitor.lifecycle_hooks}")
    print(f"Captured Function Calls: {visitor.function_calls}")
    print("=" * 60)

    # Assertions demonstrating the failure:
    assert "get_users" in visitor.routes, "Route should be discovered"
    assert len(visitor.lifecycle_hooks) == 0, "CRITICAL DEFECT: Lifecycle hooks are completely empty!"
    print("BUG CONFIRMED: Lifespan function was NOT registered as an application lifecycle hook.")
    print("Consequence: db.connect() and db.disconnect() are orphaned from the Business Workflow Map.")


if __name__ == "__main__":
    test_reproduction()

