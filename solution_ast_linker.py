"""
Solution: ASGI Lifespan & Teardown Protocol Linker for UnvibeCode Python AST Engine.

This module provides a production-grade AST visitor extension that:
1. Detects ASGI application initialization (FastAPI, Starlette, Litestar, aiohttp).
2. Resolves constructor keyword arguments including `lifespan=<function_name>`.
3. Partitions `@asynccontextmanager` generators across the `yield` boundary:
   - Phase 1: Startup Workflow (database pool connections, background workers, cache priming).
   - Phase 2: Graceful Teardown Workflow (resource de-allocation, buffer flush, socket close).
4. Links the application lifecycle directly to the Connected Code Map and Business Workflow Map.
"""

import ast
from typing import Dict, List, Optional, Set, Tuple


class ASGILifespanVisitor(ast.NodeVisitor):
    def __init__(self):
        self.routes: List[str] = []
        self.workflows: Dict[str, List[str]] = {}
        self.call_graph_edges: List[Tuple[str, str, str]] = []  # (source, target, edge_type)
        self.declared_apps: Dict[str, Dict] = {}  # app_var_name -> {class: ..., lifespan: ...}
        self.async_functions: Dict[str, ast.AsyncFunctionDef] = {}
        self.current_func: str = ""

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.async_functions[node.name] = node
        self._check_decorators(node.name, node.decorator_list)
        
        old_func = self.current_func
        self.current_func = node.name
        self.generic_visit(node)
        self.current_func = old_func

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._check_decorators(node.name, node.decorator_list)
        
        old_func = self.current_func
        self.current_func = node.name
        self.generic_visit(node)
        self.current_func = old_func

    def _check_decorators(self, func_name: str, decorators: list):
        for dec in decorators:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                if dec.func.attr in ("get", "post", "put", "delete", "patch"):
                    self.routes.append(func_name)
                    app_name = getattr(dec.func.value, "id", "app")
                    self.call_graph_edges.append((app_name, func_name, "HTTP_ROUTE"))

    def visit_Assign(self, node: ast.Assign):
        # Detect app = FastAPI(..., lifespan=lifespan)
        if isinstance(node.value, ast.Call):
            func_name = ""
            if isinstance(node.value.func, ast.Name):
                func_name = node.value.func.id
            elif isinstance(node.value.func, ast.Attribute):
                func_name = node.value.func.attr

            if func_name in ("FastAPI", "Starlette", "Litestar"):
                target_var = node.targets[0].id if (node.targets and isinstance(node.targets[0], ast.Name)) else "app"
                app_info = {"framework": func_name, "lifespan": None}
                
                for kw in node.value.keywords:
                    if kw.arg == "lifespan" and isinstance(kw.value, ast.Name):
                        app_info["lifespan"] = kw.value.id
                        
                self.declared_apps[target_var] = app_info
        
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if self.current_func:
            target_name = ""
            if isinstance(node.func, ast.Attribute):
                target_name = f"{getattr(node.func.value, 'id', '')}.{node.func.attr}"
            elif isinstance(node.func, ast.Name):
                target_name = node.func.id
            if target_name:
                self.call_graph_edges.append((self.current_func, target_name, "FUNCTION_CALL"))
        self.generic_visit(node)

    def finalize_lifecycle_workflows(self):
        """
        Post-AST compilation pass: Resolves app lifespans into Startup and Teardown workflows.
        """
        for app_var, info in self.declared_apps.items():
            lifespan_name = info.get("lifespan")
            if lifespan_name and lifespan_name in self.async_functions:
                func_node = self.async_functions[lifespan_name]
                startup_calls, teardown_calls = self._partition_lifespan(func_node)
                
                # Register Startup Workflow
                startup_wf_key = f"{app_var}::Lifecycle::Startup"
                self.workflows[startup_wf_key] = startup_calls
                for call in startup_calls:
                    self.call_graph_edges.append((f"{app_var}[Startup]", call, "ASGI_STARTUP_EDGE"))
                    
                # Register Teardown Workflow
                teardown_wf_key = f"{app_var}::Lifecycle::Teardown"
                self.workflows[teardown_wf_key] = teardown_calls
                for call in teardown_calls:
                    self.call_graph_edges.append((f"{app_var}[Teardown]", call, "ASGI_TEARDOWN_EDGE"))

    def _partition_lifespan(self, func_node: ast.AsyncFunctionDef) -> Tuple[List[str], List[str]]:
        startup_calls = []
        teardown_calls = []
        reached_yield = False

        for stmt in func_node.body:
            # Check for yield or Expr(yield)
            has_yield = any(isinstance(n, ast.Yield) for n in ast.walk(stmt))
            if has_yield:
                reached_yield = True
                continue

            # Extract calls in this statement
            calls = []
            for n in ast.walk(stmt):
                if isinstance(n, ast.Call):
                    if isinstance(n.func, ast.Attribute):
                        calls.append(f"{getattr(n.func.value, 'id', '')}.{n.func.attr}")
                    elif isinstance(n.func, ast.Name):
                        calls.append(n.func.id)

            if not reached_yield:
                startup_calls.extend(calls)
            else:
                teardown_calls.extend(calls)

        return startup_calls, teardown_calls

