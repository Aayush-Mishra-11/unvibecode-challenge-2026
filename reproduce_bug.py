# Minimal script to reproduce how decorator-only AST parsing misses
# FastAPI / Starlette lifespan handlers.

import ast

class UnvibeCodeASTSimulator(ast.NodeVisitor):
    def __init__(self):
        self.routes = []
        self.lifecycle_hooks = []
        self.recorded_calls = []

    def visit_AsyncFunctionDef(self, node):
        self._check_decorators(node.name, node.decorator_list)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self._check_decorators(node.name, node.decorator_list)
        self.generic_visit(node)

    def _check_decorators(self, func_name, decorators):
        for dec in decorators:
            # Check @app.get, @app.post, etc.
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                if dec.func.attr in ("get", "post", "put", "delete"):
                    self.routes.append(func_name)
                # Check legacy @app.on_event("startup")
                elif dec.func.attr == "on_event" and dec.args:
                    self.lifecycle_hooks.append(f"{func_name}:{dec.args[0].value}")

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            val = getattr(node.func.value, "id", "")
            self.recorded_calls.append(f"{val}.{node.func.attr}")
        elif isinstance(node.func, ast.Name):
            self.recorded_calls.append(node.func.id)
        self.generic_visit(node)


def main():
    sample_code = """
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield {"db": db}
    await db.disconnect()

app = FastAPI(title="SampleApp", lifespan=lifespan)

@app.get("/items")
async def get_items():
    return {"status": "ok"}
"""

    tree = ast.parse(sample_code)
    visitor = UnvibeCodeASTSimulator()
    visitor.visit(tree)

    print("--- AST Visitor Analysis Results ---")
    print(f"Discovered Routes: {visitor.routes}")
    print(f"Discovered Lifecycle Hooks: {visitor.lifecycle_hooks}")
    print(f"Recorded Function Calls: {visitor.recorded_calls}")
    print("------------------------------------")

    # The issue: get_items is found, but lifespan is never tagged as a lifecycle hook
    if "get_items" in visitor.routes and len(visitor.lifecycle_hooks) == 0:
        print("[FAIL] Defect reproduced: lifespan() was not registered as an application lifecycle hook.")
        print("db.connect() and db.disconnect() end up orphaned in the Connected Code Map.")
    else:
        print("[PASS] Lifespan was detected.")


if __name__ == "__main__":
    main()
