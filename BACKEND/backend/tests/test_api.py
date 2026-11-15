import pytest


def test_health(client):
    """Verify /health endpoint returns system status and configuration."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data
    assert "version" in data
    assert "environment" in data
    assert "database" in data
    assert data["is_placeholder"] is False


def test_bodies(client):
    """Verify /api/v1/bodies lists celestial bodies and supports detail lookup."""
    response = client.get("/api/v1/bodies")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 2
    body_ids = [b["id"] for b in data["items"]]
    assert "mars" in body_ids
    assert "moon" in body_ids

    # Detail endpoint
    detail_res = client.get("/api/v1/bodies/mars")
    assert detail_res.status_code == 200
    assert detail_res.json()["name"] == "Mars"

    # 404 for unknown body
    not_found_res = client.get("/api/v1/bodies/jupiter-not-yet")
    assert not_found_res.status_code == 404
    assert not_found_res.json()["status_code"] == 404


def test_lunar_sites_crud(client):
    """Verify full CRUD lifecycle on /api/v1/lunar/sites (list, create, update, delete)."""
    # 1. List sites
    list_res = client.get("/api/v1/lunar/sites")
    assert list_res.status_code == 200
    assert isinstance(list_res.json(), list)

    # 2. Create site
    test_site_payload = {
        "id": "site-test-malapert-01",
        "name": "Malapert Mountain Test Site",
        "body_id": "moon",
        "coordinates": {
            "values": [-86.04, 357.3],
            "units": "deg",
            "frame": "MOON_ME_DE421"
        },
        "frame": "MOON_ME_DE421",
        "analysis_radius_m": 1200.0,
        "notes": "Pytest candidate site creation",
        "is_placeholder": True
    }
    create_res = client.post("/api/v1/lunar/sites", json=test_site_payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["id"] == "site-test-malapert-01"
    assert created_data["analysis_radius_m"] == 1200.0

    # 3. Update site
    update_payload = {
        "analysis_radius_m": 1800.0,
        "notes": "Updated radius via pytest"
    }
    update_res = client.put("/api/v1/lunar/sites/site-test-malapert-01", json=update_payload)
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["analysis_radius_m"] == 1800.0
    assert updated_data["notes"] == "Updated radius via pytest"

    # 4. Delete site
    delete_res = client.delete("/api/v1/lunar/sites/site-test-malapert-01")
    assert delete_res.status_code == 204

    # 5. Confirm deletion
    get_deleted = client.get("/api/v1/lunar/sites/site-test-malapert-01")
    assert get_deleted.status_code == 404


def test_perseverance_latest_location(client):
    """Verify latest documented location for Perseverance and non-fabrication for Curiosity."""
    # Documented location exists
    response = client.get("/api/v1/rovers/perseverance/latest-location")
    assert response.status_code == 200
    data = response.json()
    assert data["explorer_id"] == "perseverance"
    assert data["coordinates"] is not None
    assert data["coordinates"]["coordinate_frame"] == "IAU_MARS_2000"
    assert data["coordinates"]["units"] == "deg"
    assert data["position_method"] == "localized"
    assert data["source_product_id"] == "urn:nasa:pds:mars2020_rover_places:site_0001"

    # Missing location for Curiosity is NEVER fabricated
    curiosity_res = client.get("/api/v1/rovers/curiosity/latest-location")
    assert curiosity_res.status_code == 200
    curiosity_data = curiosity_res.json()
    assert curiosity_data["explorer_id"] == "curiosity"
    assert curiosity_data["position_status"] == "unknown"
    assert curiosity_data["coordinates"] is None
    assert curiosity_data["position_method"] == "unknown"


def test_sources_provenance(client):
    """Verify /sources/{product_id} returns full provenance and 404 for unknown products."""
    product_id = "urn:nasa:pds:mars2020_rover_places:site_0001"
    response = client.get(f"/api/v1/sources/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == product_id
    assert data["product_identifier"] == product_id
    assert data["version"] == "11.0"
    assert data["checksum"] == "a1b2c3d4e5f67890123456789abcdef0"
    assert data["label"] == "Unknown"
    assert data["is_placeholder"] is True
    assert data["coordinate_frame"] == "IAU_MARS_2000"
    assert data["units"] == "deg"
    assert "source" in data
    assert data["source"]["id"] == "src-pds-places"

    # 404 for unknown product id
    unknown_res = client.get("/api/v1/sources/non-existent-product-id-12345")
    assert unknown_res.status_code == 404
    error_data = unknown_res.json()
    assert error_data["status_code"] == 404
    assert "not found" in error_data["detail"].lower()


def test_placeholder_records_unknown_label_rule(client):
    """
    CRITICAL RULE TEST: Every record or source with is_placeholder=true
    must have label 'Unknown', NEVER 'Verified', 'Historical' or 'Estimated'.
    """
    # 1. Source Provenance
    src_res = client.get("/api/v1/sources/urn:nasa:pds:mars2020_rover_places:site_0001")
    assert src_res.status_code == 200
    src_data = src_res.json()
    if src_data["is_placeholder"]:
        assert src_data["label"] == "Unknown"

    # 2. Location
    loc_res = client.get("/api/v1/rovers/perseverance/latest-location")
    assert loc_res.status_code == 200
    loc_data = loc_res.json()
    if loc_data["is_placeholder"]:
        assert loc_data["label"] == "Unknown"

    # 3. Trajectory
    traj_res = client.get("/api/v1/rovers/perseverance/trajectory")
    assert traj_res.status_code == 200
    traj_data = traj_res.json()
    if traj_data["is_placeholder"]:
        assert traj_data["label"] == "Unknown"

    # 4. Images
    img_res = client.get("/api/v1/rovers/perseverance/images")
    assert img_res.status_code == 200
    for img in img_res.json()["items"]:
        if img["is_placeholder"]:
            assert img["label"] == "Unknown"

    # 5. Events
    ev_res = client.get("/api/v1/rovers/perseverance/events")
    assert ev_res.status_code == 200
    for ev in ev_res.json()["items"]:
        if ev["is_placeholder"]:
            assert ev["label"] == "Unknown"

    # 6. Health
    health_res = client.get("/api/v1/rovers/perseverance/health")
    assert health_res.status_code == 200
    health_data = health_res.json()
    if health_data["is_placeholder"]:
        assert health_data["label"] == "Unknown"

    # 7. Analytics
    analytics_res = client.get("/api/v1/rovers/perseverance/analytics")
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    if analytics_data["is_placeholder"]:
        assert analytics_data["label"] == "Unknown"

    # 8. Missions
    missions_res = client.get("/api/v1/missions")
    assert missions_res.status_code == 200
    for m in missions_res.json()["items"]:
        if m["is_placeholder"]:
            assert m["label"] == "Unknown"

    # 9. Rovers
    rovers_res = client.get("/api/v1/rovers")
    assert rovers_res.status_code == 200
    for r in rovers_res.json()["items"]:
        if r["is_placeholder"]:
            assert r["label"] == "Unknown"


def test_missions_detail_and_not_found(client):
    """Verify GET /api/v1/missions/{mission_id} and 404 behavior."""
    res = client.get("/api/v1/missions/mars-2020")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "mars-2020"
    assert data["name"] == "Mars 2020"

    nf = client.get("/api/v1/missions/unknown-mission")
    assert nf.status_code == 404


def test_rovers_detail_and_not_found(client):
    """Verify GET /api/v1/rovers/{rover_id} and 404 behavior."""
    res = client.get("/api/v1/rovers/perseverance")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "perseverance"
    assert data["explorer_type"] == "rover"

    nf = client.get("/api/v1/rovers/unknown-rover")
    assert nf.status_code == 404


def test_rover_locations_list(client):
    """Verify GET /api/v1/rovers/{rover_id}/locations returns paginated locations."""
    res = client.get("/api/v1/rovers/perseverance/locations?limit=10&offset=0")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


def test_rover_analytics_and_timeline(client):
    """Verify GET analytics and timeline for rover."""
    analytics_res = client.get("/api/v1/rovers/perseverance/analytics")
    assert analytics_res.status_code == 200
    adata = analytics_res.json()
    assert adata["explorer_id"] == "perseverance"
    assert "distance_km" in adata

    timeline_res = client.get("/api/v1/rovers/perseverance/timeline?limit=10")
    assert timeline_res.status_code == 200
    tdata = timeline_res.json()
    assert tdata["explorer_id"] == "perseverance"
    assert "timeline" in tdata


def test_lunar_site_detail(client):
    """Verify GET /api/v1/lunar/sites/{site_id} returns site detail."""
    res = client.get("/api/v1/lunar/sites/site-shackleton-01")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "site-shackleton-01"
    assert data["body_id"] == "moon"


def test_auth_and_admin_stubs(client):
    """Verify placeholder responses for auth and admin stubs."""
    login_res = client.post("/api/v1/auth/login")
    assert login_res.status_code == 200
    assert login_res.json()["is_placeholder"] is True

    me_res = client.get("/api/v1/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["is_placeholder"] is True

    admin_res = client.get("/api/v1/admin/status")
    assert admin_res.status_code == 200
    assert admin_res.json()["is_placeholder"] is True

