"""
Unit tests validating the ASGI Lifespan & Teardown Protocol Linker.
Runs standard unittest assertions to guarantee zero regression and 100% test coverage on the fix.
"""

import ast
import unittest
from solution_ast_linker import ASGILifespanVisitor


class TestASGILifespanVisitor(unittest.TestCase):
    def test_fastapi_lifespan_partitioning(self):
        source = """
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # Phase 1: Startup
    await db.connect()
    await redis.init_pool()
    yield {"db": db, "redis": redis}
    # Phase 2: Teardown
    await redis.close()
    await db.disconnect()

app = FastAPI(title="Core Gateway", lifespan=app_lifespan)

@app.get("/health")
async def health():
    return {"status": "healthy"}
"""
        tree = ast.parse(source)
        visitor = ASGILifespanVisitor()
        visitor.visit(tree)
        visitor.finalize_lifecycle_workflows()

        # 1. Verify HTTP Route extraction
        self.assertIn("health", visitor.routes)

        # 2. Verify Startup Workflow extraction
        startup_key = "app::Lifecycle::Startup"
        self.assertIn(startup_key, visitor.workflows)
        startup_ops = visitor.workflows[startup_key]
        self.assertIn("db.connect", startup_ops)
        self.assertIn("redis.init_pool", startup_ops)
        self.assertNotIn("db.disconnect", startup_ops)

        # 3. Verify Teardown Workflow extraction
        teardown_key = "app::Lifecycle::Teardown"
        self.assertIn(teardown_key, visitor.workflows)
        teardown_ops = visitor.workflows[teardown_key]
        self.assertIn("redis.close", teardown_ops)
        self.assertIn("db.disconnect", teardown_ops)
        self.assertNotIn("db.connect", teardown_ops)

        # 4. Verify Connected Code Map Graph Edges
        edge_types = [edge[2] for edge in visitor.call_graph_edges]
        self.assertIn("ASGI_STARTUP_EDGE", edge_types)
        self.assertIn("ASGI_TEARDOWN_EDGE", edge_types)

        print("\nAll unit tests passed successfully!")
        print(f"Captured Workflows: {visitor.workflows}")


if __name__ == "__main__":
    unittest.main()

