"""
Unit tests for Rover Images Import Pipeline (FR-15 to FR-18).
Uses tiny synthetic fixtures (marked fixture, not calling external network).
"""

import pytest
from datetime import datetime, timezone
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.models.models import Image, DataSource, DataProduct
from data_pipeline.parsers.images_parser import ImagesParser
from data_pipeline.validators.images_validator import ImagesValidator
from data_pipeline.loaders.images_loader import ImagesLoader

# --- SYNTHETIC FIXTURE DATA (NOT REAL DATA) ---
MOCK_RAW_FEED = {
    "images": [
        {
            "imageid": "TEST_MOCK_SOL001_CAM01",
            "sol": 10,
            "camera": {"instrument": "NAVCAM_LEFT"},
            "date_taken_utc": "2021-03-01T10:00:00.000",
            "image_files": {
                "medium": "https://mars.nasa.gov/mars2020-raw-images/pub/ods/surface/sol/00010/test1.jpg"
            },
            "caption": "Synthetic test image 1",
            "credit": "NASA/JPL-Caltech",
        },
        {
            "imageid": "TEST_MOCK_SOL002_CAM02",
            "sol": 50,
            "camera": {"instrument": "MCZ_RIGHT"},
            "date_taken_utc": "2021-04-10T14:30:00.000",
            "image_files": {
                "large": "https://mars.nasa.gov/mars2020-raw-images/pub/ods/surface/sol/00050/test2.jpg"
            },
            "caption": "Synthetic test image 2",
            "credit": "NASA/JPL-Caltech",
        },
        {
            # Invalid: insecure http URL and non-NASA domain
            "imageid": "TEST_INVALID_URL",
            "sol": 50,
            "camera": {"instrument": "SUPERCAM"},
            "date_taken_utc": "2021-04-10T14:30:00.000",
            "image_files": {
                "medium": "http://evil.com/fake.jpg"
            },
        },
        {
            # Invalid: missing captured_at
            "imageid": "TEST_INVALID_DATE",
            "sol": 50,
            "camera": {"instrument": "SUPERCAM"},
            "date_taken_utc": None,
            "image_files": {
                "medium": "https://mars.nasa.gov/test.jpg"
            },
        },
    ]
}


def test_images_parser():
    """Verify that ImagesParser extracts valid records from raw JSON format."""
    parser = ImagesParser()
    records = parser.parse_data(MOCK_RAW_FEED)
    assert len(records) == 4
    r1 = records[0]
    assert r1["id"] == "TEST_MOCK_SOL001_CAM01"
    assert r1["sol"] == 10
    assert r1["camera"] == "NAVCAM_LEFT"
    assert r1["image_url"] == "https://mars.nasa.gov/mars2020-raw-images/pub/ods/surface/sol/00010/test1.jpg"
    assert isinstance(r1["captured_at"], datetime)


def test_images_validator():
    """Verify that ImagesValidator rejects non-HTTPS or non-NASA URLs and missing timestamps."""
    parser = ImagesParser()
    records = parser.parse_data(MOCK_RAW_FEED)
    validator = ImagesValidator()
    valid, rejected = validator.validate_batch(records)

    assert len(valid) == 2
    assert len(rejected) == 2
    assert valid[0]["id"] == "TEST_MOCK_SOL001_CAM01"
    assert valid[1]["id"] == "TEST_MOCK_SOL002_CAM02"

    # Verify rejection reasons
    reasons0 = rejected[0]["reasons"]
    assert any("https" in r for r in reasons0)
    assert any("approved NASA domain" in r for r in reasons0)


def test_images_loader_idempotent_and_duplicates():
    """Verify that ImagesLoader loads records, sets Verified label, and skips duplicates."""
    db = SessionLocal()
    try:
        parser = ImagesParser()
        records = parser.parse_data(MOCK_RAW_FEED)
        validator = ImagesValidator()
        valid, _ = validator.validate_batch(records)

        loader = ImagesLoader(db)
        res1 = loader.load_images(valid, rover_id="perseverance")
        assert res1["loaded"] == 2
        assert res1["duplicates_skipped"] == 0
        assert "NAVCAM_LEFT" in res1["cameras_found"]
        assert "MCZ_RIGHT" in res1["cameras_found"]

        # Run again with same records -> must detect and skip duplicates
        res2 = loader.load_images(valid, rover_id="perseverance")
        assert res2["loaded"] == 0
        assert res2["duplicates_skipped"] == 2

        # Verify DB records
        img1 = db.query(Image).filter(Image.id == "img-m2020-TEST_MOCK_SOL001_CAM01").first()
        assert img1 is not None
        assert img1.label == "Verified"
        assert img1.is_placeholder is False
        assert img1.sol == 10

        # Verify DataProduct provenance
        dp1 = db.query(DataProduct).filter(DataProduct.id == img1.product_id).first()
        assert dp1 is not None
        assert dp1.label == "Verified"
        assert dp1.is_placeholder is False
    finally:
        # Clean up test rows
        db.query(Image).filter(Image.id.like("img-m2020-TEST_%")).delete()
        db.query(DataProduct).filter(DataProduct.id.like("%TEST_%")).delete()
        db.commit()
        db.close()


def test_images_api_filters_and_pagination(client):
    """Verify that GET /api/v1/rovers/{rover_id}/images supports camera, sol filters and pagination."""
    db = SessionLocal()
    try:
        # Insert 3 test images
        img_a = Image(
            id="img-test-api-a",
            explorer_id="perseverance",
            captured_at=datetime(2021, 3, 1, 12, 0, tzinfo=timezone.utc),
            sol=15,
            image_url="https://mars.nasa.gov/test_a.jpg",
            camera="TEST_CAM_A",
            label="Verified",
            is_placeholder=False,
        )
        img_b = Image(
            id="img-test-api-b",
            explorer_id="perseverance",
            captured_at=datetime(2021, 3, 2, 12, 0, tzinfo=timezone.utc),
            sol=16,
            image_url="https://mars.nasa.gov/test_b.jpg",
            camera="TEST_CAM_B",
            label="Verified",
            is_placeholder=False,
        )
        img_c = Image(
            id="img-test-api-c",
            explorer_id="perseverance",
            captured_at=datetime(2021, 3, 3, 12, 0, tzinfo=timezone.utc),
            sol=15,
            image_url="https://mars.nasa.gov/test_c.jpg",
            camera="TEST_CAM_A",
            label="Verified",
            is_placeholder=False,
        )
        db.add_all([img_a, img_b, img_c])
        db.commit()

        # 1. Filter by camera
        r_cam = client.get("/api/v1/rovers/perseverance/images?camera=TEST_CAM_A")
        assert r_cam.status_code == 200
        cam_data = r_cam.json()
        assert all(item["camera"] == "TEST_CAM_A" for item in cam_data["items"])
        assert any(item["id"] == "img-test-api-a" for item in cam_data["items"])
        assert not any(item["id"] == "img-test-api-b" for item in cam_data["items"])

        # 2. Filter by sol
        r_sol = client.get("/api/v1/rovers/perseverance/images?sol=16")
        assert r_sol.status_code == 200
        sol_data = r_sol.json()
        assert len(sol_data["items"]) == 1
        assert sol_data["items"][0]["id"] == "img-test-api-b"
        assert sol_data["items"][0]["sol"] == 16

        # 3. Pagination limit/offset
        r_page = client.get("/api/v1/rovers/perseverance/images?camera=TEST_CAM_A&limit=1&offset=0")
        assert r_page.status_code == 200
        page_data = r_page.json()
        assert len(page_data["items"]) == 1
        assert page_data["limit"] == 1
        assert page_data["total"] >= 2
    finally:
        db.query(Image).filter(Image.id.like("img-test-api-%")).delete()
        db.commit()
        db.close()
