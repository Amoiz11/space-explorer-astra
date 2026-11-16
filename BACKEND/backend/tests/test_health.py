import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data
    assert data["is_placeholder"] is False
    assert "bootstrap_status" in data
    assert "assistant_provider" in data
    assert data["assistant_provider"] in ("configured", "missing")


def test_health_bootstrap_status_states():
    """Verify /health stays 200 across running, done, and failed states."""
    from backend.app.core import bootstrap_state

    # 1. Done state
    bootstrap_state.set_done()
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["bootstrap_status"] == "done"

    # 2. Running state
    bootstrap_state.set_running()
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["bootstrap_status"] == "running"

    # 3. Failed state
    bootstrap_state.set_failed("SPICE kernel download timeout")
    res = client.get("/health")
    assert res.status_code == 200
    assert "failed: SPICE kernel download timeout" in res.json()["bootstrap_status"]

    # Restore done state
    bootstrap_state.set_done()


def test_endpoints_return_503_warming_up_during_bootstrap():
    """When bootstrap is running, data endpoints return 503 with 'warming up' message."""
    from backend.app.core import bootstrap_state

    bootstrap_state.set_running()
    try:
        # Endpoint needing DEM
        res = client.get("/api/v1/lunar/sites/site-shackleton-01/terrain")
        assert res.status_code == 503
        assert "warming up" in res.json()["detail"].lower()

        # Endpoint needing kernels / comparison
        res2 = client.post("/api/v1/lunar/compare", json={"site_ids": ["site-shackleton-01"]})
        assert res2.status_code == 503
        assert "warming up" in res2.json()["detail"].lower()

        # Non-DEM/kernel metadata endpoint stays accessible (e.g. site list from DB)
        res3 = client.get("/api/v1/lunar/sites")
        assert res3.status_code == 200
    finally:
        bootstrap_state.set_done()

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "/docs" in data["docs"]
    assert "/health" in data["health"]

def test_api_v1_status():
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["api_version"] == "v1"
