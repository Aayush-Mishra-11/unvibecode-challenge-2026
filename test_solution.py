# Tests for ASGI lifespan visitor resolution
import ast
import unittest
from solution_ast_linker import ASGILifespanVisitor

class TestASGILifespanResolution(unittest.TestCase):
    def test_fastapi_lifespan_startup_and_teardown(self):
        code = """
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup operations
    await db.connect()
    await redis.init()
    yield
    # Teardown operations
    await redis.close()
    await db.disconnect()

app = FastAPI(title="MyApp", lifespan=lifespan)

@app.get("/items")
async def get_items():
    return {"status": "ok"}
"""
        tree = ast.parse(code)
        visitor = ASGILifespanVisitor()
        visitor.visit(tree)
        visitor.resolve_lifespans()

        # 1. Routes recognized
        self.assertIn("get_items", visitor.routes)

        # 2. Startup workflow captured
        self.assertIn("app::Startup", visitor.workflows)
        startup = visitor.workflows["app::Startup"]
        self.assertIn("db.connect", startup)
        self.assertIn("redis.init", startup)
        self.assertNotIn("db.disconnect", startup)

        # 3. Teardown workflow captured
        self.assertIn("app::Teardown", visitor.workflows)
        teardown = visitor.workflows["app::Teardown"]
        self.assertIn("redis.close", teardown)
        self.assertIn("db.disconnect", teardown)
        self.assertNotIn("db.connect", teardown)

        # 4. Graph edges created
        edge_types = [e[2] for e in visitor.graph_edges]
        self.assertIn("ASGI_STARTUP", edge_types)
        self.assertIn("ASGI_TEARDOWN", edge_types)

    def test_starlette_lifespan(self):
        code = """
from contextlib import asynccontextmanager
from starlette.applications import Starlette

@asynccontextmanager
async def app_lifespan(app):
    await pool.init()
    yield
    await pool.close()

app = Starlette(lifespan=app_lifespan)
"""
        tree = ast.parse(code)
        visitor = ASGILifespanVisitor()
        visitor.visit(tree)
        visitor.resolve_lifespans()

        self.assertIn("app::Startup", visitor.workflows)
        self.assertIn("pool.init", visitor.workflows["app::Startup"])
        self.assertIn("app::Teardown", visitor.workflows)
        self.assertIn("pool.close", visitor.workflows["app::Teardown"])

    def test_app_without_lifespan(self):
        code = """
from fastapi import FastAPI

app = FastAPI(title="SimpleApp")

@app.get("/ping")
async def ping():
    return {"pong": True}
"""
        tree = ast.parse(code)
        visitor = ASGILifespanVisitor()
        visitor.visit(tree)
        visitor.resolve_lifespans()

        self.assertIn("ping", visitor.routes)
        self.assertEqual(len(visitor.workflows), 0)

if __name__ == "__main__":
    unittest.main()
