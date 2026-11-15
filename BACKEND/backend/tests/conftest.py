import os
import pytest

TEST_DB_FILE = os.path.abspath("test_space_explorer.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"

from backend.app.config import settings
settings.DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.database.init_db import init_database
from backend.app.database.session import engine


def _remove_test_db():
    engine.dispose()
    for ext in ["", "-wal", "-shm", "-journal"]:
        p = TEST_DB_FILE + ext
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass


def pytest_configure(config):
    """Run database init on isolated test database before any tests."""
    _remove_test_db()
    init_database()


def pytest_unconfigure(config):
    """Clean up isolated test database after all tests complete."""
    _remove_test_db()


@pytest.fixture(scope="session")
def client():
    """Session-scoped TestClient with lifespan disabled (init_database called above)."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
