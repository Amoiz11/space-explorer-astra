import os
import shutil
import datetime
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError
from backend.app.config import settings
from backend.app.database.session import engine, Base, SessionLocal
from backend.app.models.models import (
    CelestialBody,
    Mission,
    Explorer,
    DataSource,
    DataProduct,
    Location,
    Trajectory,
    Image,
    MissionEvent,
    HealthReport,
    CandidateLandingSite,
)


def _get_sqlite_filepath() -> str | None:
    """Extract SQLite database file path from DATABASE_URL if using SQLite."""
    if not settings.DATABASE_URL.startswith("sqlite"):
        return None
    raw_path = settings.DATABASE_URL.split("sqlite:///")[-1]
    return os.path.abspath(raw_path)


def _check_and_backup_stale_sqlite(db_file: str) -> bool:
    """
    In development mode with SQLite, inspect tables and columns.
    If a schema mismatch is detected (e.g. missing column from updated models),
    rename the old file to .bak and return True to signal recreation.
    """
    if settings.APP_ENV != "development" or not settings.DATABASE_URL.startswith("sqlite"):
        return False

    if not os.path.exists(db_file):
        return False

    mismatch = False
    try:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())

        for table_name, table in Base.metadata.tables.items():
            if table_name in existing_tables:
                existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
                model_cols = {col.name for col in table.columns}
                if not model_cols.issubset(existing_cols):
                    mismatch = True
                    break
    except Exception:
        mismatch = True

    if mismatch:
        engine.dispose()
        bak_file = f"{db_file}.bak"
        if os.path.exists(bak_file):
            try:
                os.remove(bak_file)
            except OSError:
                pass
        try:
            shutil.move(db_file, bak_file)
            print(f"[DB] SQLite schema mismatch detected in development. Stale database renamed to: {bak_file}")
            return True
        except Exception as e:
            print(f"[DB Warning] Could not rename stale database: {e}")

    return False


def seed_placeholder_data(db):
    """
    Seed baseline placeholder rows flagged with is_placeholder=True.
    Rule: Every record or source with is_placeholder=true must have label 'Unknown'.
    """
    # 1. Celestial Bodies
    bodies = [
        CelestialBody(
            id="mars",
            name="Mars",
            body_type="planet",
            reference_system="IAU_MARS_2000",
            is_placeholder=True,
        ),
        CelestialBody(
            id="moon",
            name="Moon",
            body_type="moon",
            reference_system="MOON_ME_DE421",
            is_placeholder=True,
        ),
    ]
    for b in bodies:
        if not db.query(CelestialBody).filter(CelestialBody.id == b.id).first():
            db.add(b)
    db.flush()

    # 2. Missions
    missions = [
        Mission(
            id="mars-2020",
            body_id="mars",
            name="Mars 2020",
            launch_date=datetime.datetime(2020, 7, 30, 11, 50, tzinfo=datetime.timezone.utc),
            landing_date=datetime.datetime(2021, 2, 18, 20, 55, tzinfo=datetime.timezone.utc),
            status="active",
            is_placeholder=True,
        ),
        Mission(
            id="msl-curiosity",
            body_id="mars",
            name="Mars Science Laboratory",
            launch_date=datetime.datetime(2011, 11, 26, 15, 2, tzinfo=datetime.timezone.utc),
            landing_date=datetime.datetime(2012, 8, 6, 5, 17, tzinfo=datetime.timezone.utc),
            status="active",
            is_placeholder=True,
        ),
        Mission(
            id="artemis-lunar",
            body_id="moon",
            name="Artemis Program",
            launch_date=datetime.datetime(2022, 11, 16, 6, 47, tzinfo=datetime.timezone.utc),
            status="active",
            is_placeholder=True,
        ),
        Mission(
            id="lro",
            body_id="moon",
            name="Lunar Reconnaissance Orbiter",
            launch_date=datetime.datetime(2009, 6, 18, 21, 32, 0, tzinfo=datetime.timezone.utc),
            landing_date=None,
            end_date=None,
            status="active",
            is_placeholder=False,
        ),
    ]
    for m in missions:
        if not db.query(Mission).filter(Mission.id == m.id).first():
            db.add(m)
    db.flush()

    # 3. Explorers
    explorers = [
        Explorer(
            id="perseverance",
            mission_id="mars-2020",
            name="Perseverance Rover",
            explorer_type="rover",
            current_status="active",
            is_placeholder=True,
        ),
        Explorer(
            id="curiosity",
            mission_id="msl-curiosity",
            name="Curiosity Rover",
            explorer_type="rover",
            current_status="active",
            is_placeholder=True,
        ),
        Explorer(
            id="lro",
            mission_id="lro",
            name="Lunar Reconnaissance Orbiter",
            explorer_type="orbiter",
            current_status="active",
            is_placeholder=False,
        ),
    ]
    for e in explorers:
        if not db.query(Explorer).filter(Explorer.id == e.id).first():
            db.add(e)
    db.flush()

    # 4. Data Sources & Products
    source = db.query(DataSource).filter(DataSource.id == "src-pds-places").first()
    if not source:
        source = DataSource(
            id="src-pds-places",
            name="NASA Planetary Data System (PDS) Geosciences Node",
            source_url="https://pds-geosciences.wustl.edu/missions/mars2020/index.htm",
            organization="NASA / JPL / Washington University in St. Louis",
            is_placeholder=True,
        )
        db.add(source)
        db.flush()

    prod_loc = db.query(DataProduct).filter(DataProduct.id == "urn:nasa:pds:mars2020_rover_places:site_0001").first()
    if not prod_loc:
        prod_loc = DataProduct(
            id="urn:nasa:pds:mars2020_rover_places:site_0001",
            source_id="src-pds-places",
            product_identifier="urn:nasa:pds:mars2020_rover_places:site_0001",
            version="11.0",
            checksum="a1b2c3d4e5f67890123456789abcdef0",
            observation_time=datetime.datetime(2021, 2, 18, 20, 55, tzinfo=datetime.timezone.utc),
            retrieved_at=datetime.datetime(2026, 11, 14, 12, 0, tzinfo=datetime.timezone.utc),
            coordinate_frame="IAU_MARS_2000",
            units="deg",
            processing_method="Rover localization and traverse mesh reconstruction (PLACES)",
            uncertainty={"radius_m": 5.0, "confidence_level": 0.95},
            label="Unknown",
            is_placeholder=True,
        )
        db.add(prod_loc)
        db.flush()

    prod_img = db.query(DataProduct).filter(DataProduct.id == "urn:nasa:pds:mars2020_hazcam:pia24428").first()
    if not prod_img:
        prod_img = DataProduct(
            id="urn:nasa:pds:mars2020_hazcam:pia24428",
            source_id="src-pds-places",
            product_identifier="urn:nasa:pds:mars2020_hazcam:pia24428",
            version="1.0",
            checksum="b2c3d4e5f6a17890123456789abcdef1",
            observation_time=datetime.datetime(2021, 2, 19, 14, 30, tzinfo=datetime.timezone.utc),
            retrieved_at=datetime.datetime(2026, 11, 14, 12, 0, tzinfo=datetime.timezone.utc),
            coordinate_frame="IAU_MARS_2000",
            units="pixels",
            processing_method="Mars 2020 Hazcam raw telemetry and radiometric calibration",
            uncertainty={"pixel_error": 1.2},
            label="Unknown",
            is_placeholder=True,
        )
        db.add(prod_img)
        db.flush()

    # 5. Locations (Perseverance placeholder locations following Section 5.1)
    if not db.query(Location).filter(Location.explorer_id == "perseverance").first():
        loc1 = Location(
            explorer_id="perseverance",
            observed_at=datetime.datetime(2021, 2, 18, 21, 0, tzinfo=datetime.timezone.utc),
            original_coordinates={"values": [18.4447, 77.4508], "units": "deg", "coordinate_frame": "IAU_MARS_2000"},
            coordinate_frame="IAU_MARS_2000",
            uncertainty={"radius_m": 5.0},
            product_id=prod_loc.id,
            position_method="localized",
            position_status="verified",
            label="Unknown",
            is_placeholder=True,
        )
        loc2 = Location(
            explorer_id="perseverance",
            observed_at=datetime.datetime(2021, 3, 5, 12, 0, tzinfo=datetime.timezone.utc),
            original_coordinates={"values": [18.4452, 77.4515], "units": "deg", "coordinate_frame": "IAU_MARS_2000"},
            coordinate_frame="IAU_MARS_2000",
            uncertainty={"radius_m": 4.5},
            product_id=prod_loc.id,
            position_method="localized",
            position_status="verified",
            label="Unknown",
            is_placeholder=True,
        )
        db.add_all([loc1, loc2])

    # 6. Trajectory for Perseverance
    if not db.query(Trajectory).filter(Trajectory.explorer_id == "perseverance").first():
        traj = Trajectory(
            explorer_id="perseverance",
            path_coordinates=[
                [18.4447, 77.4508],
                [18.4450, 77.4512],
                [18.4452, 77.4515],
            ],
            method="validated surface traverse segments",
            start_time=datetime.datetime(2021, 2, 18, 21, 0, tzinfo=datetime.timezone.utc),
            end_time=datetime.datetime(2021, 3, 5, 12, 0, tzinfo=datetime.timezone.utc),
            product_id=prod_loc.id,
            label="Unknown",
            is_placeholder=True,
        )
        db.add(traj)

    # 7. Images for Perseverance
    if not db.query(Image).filter(Image.explorer_id == "perseverance").first():
        img1 = Image(
            id="img-perseverance-sol001-hazcam",
            explorer_id="perseverance",
            captured_at=datetime.datetime(2021, 2, 19, 14, 30, tzinfo=datetime.timezone.utc),
            image_url="https://mars.nasa.gov/system/resources/detail_files/25612_PIA24428-web.jpg",
            camera="FRONT_HAZCAM_LEFT",
            product_id=prod_img.id,
            label="Unknown",
            is_placeholder=True,
        )
        db.add(img1)

    # 8. Events for Perseverance
    if not db.query(MissionEvent).filter(MissionEvent.explorer_id == "perseverance").first():
        ev1 = MissionEvent(
            explorer_id="perseverance",
            event_date=datetime.datetime(2021, 2, 18, 20, 55, tzinfo=datetime.timezone.utc),
            event_type="Landing",
            description="Perseverance landed successfully in Jezero Crater, Mars.",
            source_id=prod_loc.id,
            label="Unknown",
            is_placeholder=True,
        )
        db.add(ev1)

    # 9. Health Report for Perseverance
    if not db.query(HealthReport).filter(HealthReport.explorer_id == "perseverance").first():
        hr = HealthReport(
            explorer_id="perseverance",
            reported_at=datetime.datetime(2021, 2, 19, 10, 0, tzinfo=datetime.timezone.utc),
            condition="nominal",
            evidence="All primary avionics and communications operational after landing.",
            source_id=prod_loc.id,
            label="Unknown",
            is_placeholder=True,
        )
        db.add(hr)

    # 10. Candidate Landing Sites
    sites = [
        CandidateLandingSite(
            id="site-shackleton-01",
            name="Shackleton Rim Candidate Area",
            body_id="moon",
            coordinates={"values": [-89.9, 0.0], "units": "deg", "frame": "MOON_ME_DE421"},
            frame="MOON_ME_DE421",
            analysis_radius_m=1000.0,
            criteria={"slope_threshold_deg": 15.0, "threshold_label": "example threshold, not an official safety criterion"},
            notes="Placeholder candidate site for testing Backend B and Frontend integration.",
            is_placeholder=True,
        ),
        CandidateLandingSite(
            id="site-connecting-ridge-02",
            name="Connecting Ridge Candidate Area",
            body_id="moon",
            coordinates={"values": [-89.5, 120.0], "units": "deg", "frame": "MOON_ME_DE421"},
            frame="MOON_ME_DE421",
            analysis_radius_m=1500.0,
            criteria={"slope_threshold_deg": 15.0, "threshold_label": "example threshold, not an official safety criterion"},
            notes="Placeholder candidate site for testing terrain and illumination services.",
            is_placeholder=True,
        ),
    ]
    for s in sites:
        if not db.query(CandidateLandingSite).filter(CandidateLandingSite.id == s.id).first():
            db.add(s)

    db.commit()


def init_database():
    """Create all tables and seed data, handling SQLite schema drift in development."""
    db_file = _get_sqlite_filepath()
    if db_file:
        _check_and_backup_stale_sqlite(db_file)

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Ensure sol column exists in images table if created prior
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            cols = [r[1] for r in conn.execute(text("PRAGMA table_info(images);")).fetchall()]
            if cols and "sol" not in cols:
                conn.execute(text("ALTER TABLE images ADD COLUMN sol INTEGER;"))
                conn.commit()
    except Exception:
        pass

    db = SessionLocal()
    try:
        seed_placeholder_data(db)
    except OperationalError as oe:
        db.rollback()
        db.close()
        if db_file and settings.APP_ENV == "development" and settings.DATABASE_URL.startswith("sqlite"):
            engine.dispose()
            bak_file = f"{db_file}.bak"
            if os.path.exists(bak_file):
                try:
                    os.remove(bak_file)
                except OSError:
                    pass
            try:
                shutil.move(db_file, bak_file)
                print(f"[DB] OperationalError caught ({oe}). Recreating database from scratch and backed up to {bak_file}")
            except Exception as e:
                print(f"[DB Warning] Could not rename database on error: {e}")

            Base.metadata.create_all(bind=engine)
            retry_db = SessionLocal()
            try:
                seed_placeholder_data(retry_db)
            finally:
                retry_db.close()
        else:
            raise oe
    finally:
        try:
            db.close()
        except Exception:
            pass


if __name__ == "__main__":
    init_database()
    print("Database initialized and verified successfully.")
