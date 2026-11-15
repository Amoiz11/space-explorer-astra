"""
test_admin_key.py — Tests for ADMIN_KEY write-protection on /api/v1/lunar/sites.

Rules:
- When ADMIN_KEY is not set (or empty): POST/PUT/DELETE succeed without any header (local dev)
- When ADMIN_KEY is set: POST/PUT/DELETE require x-admin-key header matching the value → 401 otherwise
- GET is always public regardless of ADMIN_KEY

Uses sync TestClient + isolated temp DB (from conftest.py).
No network calls.
"""

import os
import pytest
from starlette.testclient import TestClient


SITE_PAYLOAD = {
    "id": "site-adminkey-test-01",
    "name": "Admin Key Test Site",
    "body_id": "moon",
    "coordinates": {
        "values": [-89.5, 0.0],
        "units": "deg",
        "frame": "MOON_ME_DE421"
    },
    "frame": "MOON_ME_DE421",
    "is_placeholder": True,
    "notes": "Temporary site for admin key tests",
}

SITE_ID = SITE_PAYLOAD["id"]


# ---------------------------------------------------------------------------
# Helper: ensure ADMIN_KEY is clean before/after each test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_admin_key():
    """Remove ADMIN_KEY from environment before each test; restore after."""
    original = os.environ.pop("ADMIN_KEY", None)
    yield
    if original is None:
        os.environ.pop("ADMIN_KEY", None)
    else:
        os.environ["ADMIN_KEY"] = original


@pytest.fixture(autouse=True)
def cleanup_test_site(client):
    """Delete the test site after each test (best-effort)."""
    yield
    try:
        client.delete(f"/api/v1/lunar/sites/{SITE_ID}")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 1. No ADMIN_KEY set → all verbs succeed without any header
# ---------------------------------------------------------------------------

def test_no_admin_key_post_allowed(client):
    """POST succeeds when ADMIN_KEY env var is not set."""
    assert "ADMIN_KEY" not in os.environ
    res = client.post("/api/v1/lunar/sites", json=SITE_PAYLOAD)
    assert res.status_code in (201, 409), f"Expected 201/409, got {res.status_code}: {res.text}"


def test_no_admin_key_get_always_public(client):
    """GET /api/v1/lunar/sites is public when ADMIN_KEY is not set."""
    assert "ADMIN_KEY" not in os.environ
    res = client.get("/api/v1/lunar/sites")
    assert res.status_code == 200


# ---------------------------------------------------------------------------
# 2. ADMIN_KEY set → POST without header → 401
# ---------------------------------------------------------------------------

def test_admin_key_set_post_without_header_returns_401(client, monkeypatch):
    """When ADMIN_KEY is configured, POST without x-admin-key → 401."""
    monkeypatch.setenv("ADMIN_KEY", "supersecret")
    res = client.post("/api/v1/lunar/sites", json=SITE_PAYLOAD)
    assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"


def test_admin_key_set_put_without_header_returns_401(client, monkeypatch):
    """When ADMIN_KEY is configured, PUT without x-admin-key → 401."""
    monkeypatch.setenv("ADMIN_KEY", "supersecret")
    res = client.put(f"/api/v1/lunar/sites/{SITE_ID}", json={"name": "New Name"})
    assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"


def test_admin_key_set_delete_without_header_returns_401(client, monkeypatch):
    """When ADMIN_KEY is configured, DELETE without x-admin-key → 401."""
    monkeypatch.setenv("ADMIN_KEY", "supersecret")
    res = client.delete(f"/api/v1/lunar/sites/{SITE_ID}")
    assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"


# ---------------------------------------------------------------------------
# 3. ADMIN_KEY set → with correct header → succeeds
# ---------------------------------------------------------------------------

def test_admin_key_set_post_with_correct_header_succeeds(client, monkeypatch):
    """When ADMIN_KEY is configured, POST with correct x-admin-key → 201 or 409."""
    monkeypatch.setenv("ADMIN_KEY", "supersecret")
    res = client.post(
        "/api/v1/lunar/sites",
        json=SITE_PAYLOAD,
        headers={"x-admin-key": "supersecret"},
    )
    assert res.status_code in (201, 409), f"Expected 201/409, got {res.status_code}: {res.text}"


def test_admin_key_set_post_with_wrong_key_returns_401(client, monkeypatch):
    """POST with a wrong x-admin-key value → 401."""
    monkeypatch.setenv("ADMIN_KEY", "supersecret")
    res = client.post(
        "/api/v1/lunar/sites",
        json=SITE_PAYLOAD,
        headers={"x-admin-key": "wrongkey"},
    )
    assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"


# ---------------------------------------------------------------------------
# 4. GET is always public (even when ADMIN_KEY is set)
# ---------------------------------------------------------------------------

def test_get_always_public_when_admin_key_set(client, monkeypatch):
    """GET /api/v1/lunar/sites is public regardless of ADMIN_KEY."""
    monkeypatch.setenv("ADMIN_KEY", "supersecret")
    res = client.get("/api/v1/lunar/sites")
    assert res.status_code == 200


def test_get_site_detail_always_public_when_admin_key_set(client, monkeypatch):
    """GET /api/v1/lunar/sites/{id} is public regardless of ADMIN_KEY."""
    monkeypatch.setenv("ADMIN_KEY", "supersecret")
    res = client.get("/api/v1/lunar/sites/site-shackleton-01")
    assert res.status_code == 200


# ---------------------------------------------------------------------------
# 5. Calculation POSTs stay public (not affected by ADMIN_KEY)
# ---------------------------------------------------------------------------

def test_compare_post_stays_public_when_admin_key_set(client, monkeypatch):
    """POST /api/v1/lunar/compare is a calculation endpoint and must stay public."""
    monkeypatch.setenv("ADMIN_KEY", "supersecret")
    res = client.post(
        "/api/v1/lunar/compare",
        json={"site_ids": ["site-shackleton-01"]},
    )
    # 200 (success) or 422 (validation) or 404 — all fine; 401 is NOT acceptable
    assert res.status_code != 401, f"compare endpoint must be public, got 401: {res.text}"
