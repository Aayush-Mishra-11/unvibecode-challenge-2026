# Tests for ASGI lifespan visitor resolution
import ast
import unittest
from solution_ast_linker import ASGILifespanVisitor

class TestASGILifespanResolution(unittest.TestCase):
    def test_lifespan_startup_and_teardown(self):
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

        # 1. Routes still recognized
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

if __name__ == "__main__":
    unittest.main()
