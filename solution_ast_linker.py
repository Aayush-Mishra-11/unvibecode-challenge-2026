# AST visitor extension to handle ASGI lifespan context managers
# Supports FastAPI and Starlette apps

import ast

class ASGILifespanVisitor(ast.NodeVisitor):
    def __init__(self):
        self.routes = []
        self.workflows = {}
        self.graph_edges = []
        self.app_instances = {}
        self.async_functions = {}
        self.current_scope = ""

    def visit_AsyncFunctionDef(self, node):
        self.async_functions[node.name] = node
        self._check_route_decorators(node.name, node.decorator_list)
        old_scope = self.current_scope
        self.current_scope = node.name
        self.generic_visit(node)
        self.current_scope = old_scope

    def visit_FunctionDef(self, node):
        self._check_route_decorators(node.name, node.decorator_list)
        old_scope = self.current_scope
        self.current_scope = node.name
        self.generic_visit(node)
        self.current_scope = old_scope

    def _check_route_decorators(self, func_name, decorators):
        for dec in decorators:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                if dec.func.attr in ("get", "post", "put", "delete", "patch"):
                    self.routes.append(func_name)
                    app_name = getattr(dec.func.value, "id", "app")
                    self.graph_edges.append((app_name, func_name, "ROUTE"))

    def visit_Assign(self, node):
        # Look for app = FastAPI(..., lifespan=lifespan)
        if isinstance(node.value, ast.Call):
            func_name = ""
            if isinstance(node.value.func, ast.Name):
                func_name = node.value.func.id
            elif isinstance(node.value.func, ast.Attribute):
                func_name = node.value.func.attr

            if func_name in ("FastAPI", "Starlette"):
                var_name = node.targets[0].id if (node.targets and isinstance(node.targets[0], ast.Name)) else "app"
                lifespan_handler = None
                for kw in node.value.keywords:
                    if kw.arg == "lifespan" and isinstance(kw.value, ast.Name):
                        lifespan_handler = kw.value.id
                
                self.app_instances[var_name] = {
                    "framework": func_name,
                    "lifespan": lifespan_handler
                }

        self.generic_visit(node)

    def visit_Call(self, node):
        if self.current_scope:
            target = ""
            if isinstance(node.func, ast.Attribute):
                target = f"{getattr(node.func.value, 'id', '')}.{node.func.attr}"
            elif isinstance(node.func, ast.Name):
                target = node.func.id
            if target:
                self.graph_edges.append((self.current_scope, target, "CALL"))
        self.generic_visit(node)

    def resolve_lifespans(self):
        """
        After the AST pass, split the lifespan generator statements across the yield node
        into startup and teardown phases.
        """
        for app_name, info in self.app_instances.items():
            handler_name = info.get("lifespan")
            if handler_name and handler_name in self.async_functions:
                func_node = self.async_functions[handler_name]
                startup_ops, teardown_ops = self._split_by_yield(func_node)

                # Link Startup Workflow
                startup_key = f"{app_name}::Startup"
                self.workflows[startup_key] = startup_ops
                for call in startup_ops:
                    self.graph_edges.append((f"{app_name}[Startup]", call, "ASGI_STARTUP"))

                # Link Teardown Workflow
                teardown_key = f"{app_name}::Teardown"
                self.workflows[teardown_key] = teardown_ops
                for call in teardown_ops:
                    self.graph_edges.append((f"{app_name}[Teardown]", call, "ASGI_TEARDOWN"))

    def _split_by_yield(self, func_node):
        startup_calls = []
        teardown_calls = []
        passed_yield = False

        for stmt in func_node.body:
            has_yield = any(isinstance(n, ast.Yield) for n in ast.walk(stmt))
            if has_yield:
                passed_yield = True
                continue

            calls = []
            for n in ast.walk(stmt):
                if isinstance(n, ast.Call):
                    if isinstance(n.func, ast.Attribute):
                        calls.append(f"{getattr(n.func.value, 'id', '')}.{n.func.attr}")
                    elif isinstance(n.func, ast.Name):
                        calls.append(n.func.id)

            if not passed_yield:
                startup_calls.extend(calls)
            else:
                teardown_calls.extend(calls)

        return startup_calls, teardown_calls
