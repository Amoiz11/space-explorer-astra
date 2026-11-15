# Space Explorer — Lunar Landing Site Navigator

**NASA Space Apps 2026 — Team Astra Motion**

Space Explorer is a research-grade planetary exploration intelligence platform for Mars and the Moon. It integrates scientific archives (NASA PDS PLACES), geospatial layers for NASA-AMMOS MMGIS, historical position tracking, lunar landing site decision analysis, and a citation-grounded AI research assistant.

> [!IMPORTANT]
> This is a hackathon research tool. All positions are labelled "latest published" or "last recorded" from official NASA archives. No position is ever fabricated or extrapolated in real-time.

---

## Table of Contents

1. [Quick Start (Windows PowerShell)](#1-quick-start-windows-powershell)
2. [Environment Variables (.env)](#2-environment-variables-env)
3. [Running the Server](#3-running-the-server)
4. [Running Tests](#4-running-tests)
5. [PLACES Data Import](#5-places-data-import)
6. [Project Structure](#6-project-structure)
7. [AI Mission Assistant](#7-ai-mission-assistant)
8. [Switching to PostgreSQL](#8-switching-to-postgresql)
9. [Alembic Migrations](#9-alembic-migrations)
10. [Known Limitations](#10-known-limitations)
11. [What is Placeholder Data?](#11-what-is-placeholder-data)
12. [NASA Data Credits](#12-nasa-data-credits)

---

## 1. Quick Start (Windows PowerShell)

**Prerequisites:** Python 3.10+ must be installed and on PATH.

```powershell
# 1. Enter the project directory
cd "D:\Documents\NASA - Lunar Landing Site Navigator"

# 2. Allow script execution (only needed once per session)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 3. Create virtual environment and install dependencies
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

# 4. Configure environment (copy .env.example → .env, then edit)
Copy-Item .env.example .env
# Edit .env to set SECRET_KEY and optionally GROQ_API_KEY / GROQ_MODEL

# 5. Start the server (auto-seeds the database on first run)
.\run.ps1
```

The API is available at:
- **Health:** http://localhost:8000/health
- **OpenAPI Docs:** http://localhost:8000/docs
- **Locations:** http://localhost:8000/api/v1/rovers/perseverance/locations?limit=10

---

## 2. Environment Variables (.env)

Copy `.env.example` to `.env`. Never commit `.env` to version control.

```env
# Application
APP_NAME="Space Explorer API"
APP_ENV=development
DEBUG=True
API_V1_PREFIX=/api/v1
HOST=0.0.0.0
PORT=8000

# Security — replace with a 64+ char random string in production
SECRET_KEY=change-this-in-production-super-secret-key-space-explorer

# Database — SQLite for local dev; switch to PostgreSQL for production
DATABASE_URL=sqlite:///./space_explorer.db
# DATABASE_URL=postgresql://user:password@host:5432/space_explorer

# CORS — comma-separated list of allowed frontend origins
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173

# AI Assistant — set LLM_PROVIDER=groq to enable LLM generation
LLM_PROVIDER=none
GROQ_API_KEY=
GROQ_MODEL=
GROQ_BASE_URL=https://api.groq.com/openai/v1
LLM_TIMEOUT_SECONDS=15.0
```

---

## 3. Running the Server

```powershell
.\run.ps1
```

`run.ps1` will:
1. Create `.venv` and install `backend/requirements.txt` if not already done.
2. Launch `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload`.
3. Auto-create database tables and seed baseline records on first startup.

To run directly with Uvicorn:
```powershell
.\.venv\Scripts\python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 4. Running Tests

```powershell
.\test.ps1
```

`test.ps1` runs `pytest backend/tests` using an isolated **temporary SQLite database** (never the real `space_explorer.db`) and a mocked LLM client. The real Groq API is never called during tests.

Expected output: **71 passed** in approximately 1.5 seconds.

```powershell
# Run with verbose output
.\test.ps1 -v

# Run a specific test file
.\test.ps1 backend/tests/test_map_layers.py
```

---

## 5. PLACES Data Import

The [NASA PDS PLACES archive](https://pds-geosciences.wustl.edu/missions/mars2020/places.htm) provides Mars 2020 (Perseverance) rover localization products derived from onboard odometry, visual odometry, and traverse mesh reconstruction.

**Run the import pipeline:**

```powershell
# Import first 500 records (recommended for local dev)
.\.venv\Scripts\python -m data_pipeline.pipelines.places_import --limit 500

# Skip re-downloading if the raw CSV is already in storage/raw/
.\.venv\Scripts\python -m data_pipeline.pipelines.places_import --limit 500 --skip-download

# Keep previously imported rows (no delete before import)
.\.venv\Scripts\python -m data_pipeline.pipelines.places_import --limit 500 --no-reset
```

---

## 5b. Rover Camera Images Import (FR-15 to FR-18)

The [NASA Mars 2020 Mission Raw Images Archive](https://mars.nasa.gov/mars2020/multimedia/raw-images/) provides real, public instrument camera images and telemetry from Perseverance.

**Run the images import pipeline:**

```powershell
# Import up to 100 images spread across multiple sols and instruments
.\.venv\Scripts\python -m data_pipeline.pipelines.images_import --rover perseverance --limit 100
```

- Idempotent and retryable; duplicates skipped by product identifier.
- Image records include sol, UTC captured timestamp, camera instrument (e.g. Navcam, Mastcam-Z, SuperCam), and official NASA archive hotlinks (`label: "Verified"`, `is_placeholder: false`).
- Configured via optional `NASA_API_KEY` (falls back to `DEMO_KEY` if unset).

---

## 6. Project Structure

```text
NASA - Lunar Landing Site Navigator/
├── .env                     # Local secrets (git-ignored)
├── .env.example             # Template — safe to commit
├── .gitignore               # Ignores .env, *.db, storage/, kernels/
├── alembic.ini              # Alembic configuration (points to backend/migrations/)
├── run.ps1                  # Start the FastAPI server
├── test.ps1                 # Run pytest (isolated temp DB, mocked LLM)
├── README.md                # This file
│
├── backend/
│   ├── requirements.txt     # Python dependencies
│   ├── migrations/          # Alembic migration files
│   │   ├── env.py           # Configured for SQLite batch + PostgreSQL
│   │   └── versions/        # Migration scripts (currently empty — see §9)
│   └── app/
│       ├── main.py          # FastAPI app, CORS, lifespan, startup log
│       ├── config.py        # Pydantic settings — loads .env from project root
│       ├── api/
│       │   ├── router.py    # Master /api/v1 router
│       │   └── v1/          # Endpoint modules (bodies, missions, rovers,
│       │                    #   locations, lunar_sites, map_layers, assistant…)
│       ├── models/          # SQLAlchemy ORM models
│       ├── schemas/         # Pydantic v2 request/response schemas
│       ├── services/        # Business logic
│       ├── repositories/    # Database query layer
│       ├── database/        # Engine, session, init_db seeder
│       └── utils/           # Error handlers, helpers
│   └── tests/               # Pytest suite (71 tests)
│       ├── conftest.py      # Isolated temp DB fixture + mocked LLM
│       ├── test_api.py
│       ├── test_assistant.py
│       ├── test_data_pipeline.py
│       ├── test_health.py
│       └── test_map_layers.py
│
├── data_pipeline/
│   ├── collectors/          # PDS download (places_collector.py)
│   ├── parsers/             # CSV parsing (places_parser.py)
│   ├── processors/          # Coordinate processing (places_processor.py)
│   ├── validators/          # Schema validation (places_validator.py)
│   ├── loaders/             # DB insertion (places_loader.py)
│   ├── exporters/           # GeoJSON export (geojson_exporter.py)
│   └── pipelines/           # Orchestration (places_import.py)
│
├── ai/
│   ├── retrieval.py         # Keyword retrieval over DB + knowledge docs
│   ├── llm_provider.py      # LLM abstraction (Groq provider, NoneProvider)
│   ├── mission_assistant.py # Hybrid assistant: retrieval + LLM + template
│   └── knowledge/           # Approved reference documents (data dictionary,
│                            #   scientific accuracy rules, lunar disclaimers)
│
├── mmgis/
│   ├── README.md            # How to point MMGIS at GeoJSON URLs
│   └── config/              # Draft MMGIS config files (mars.json, moon.json)
│
├── docs/
│   ├── api_contract.md      # Full REST API contract with request/response shapes
│   ├── backend_a_status.md  # Phase 8 acceptance checklist & security review
│   ├── deployment_notes.md  # Production deployment guide
│   └── Space_Explorer_BackendA_Plan.pdf
│
└── storage/                 # Raw archives & kernels (git-ignored)
    ├── raw/                 # Downloaded PDS CSV files
    ├── processed/
    ├── images/
    ├── kernels/             # SPICE kernels (never committed)
    └── exports/
```

---

## 7. AI Mission Assistant

The assistant (`POST /api/v1/assistant/query`) operates in **Hybrid Mode**:

1. **Keyword Retrieval** — searches DB records (bodies, missions, explorers, locations, candidate sites) and approved documents in `ai/knowledge/`.
2. **LLM Generation** — if Groq is configured, generates a natural-language answer strictly bounded by retrieved `<EVIDENCE>`.
3. **Template Fallback** — deterministic answer built from evidence when LLM is unconfigured, times out, or produces forbidden phrases.

**Configuring Groq:**
```env
LLM_PROVIDER=groq
GROQ_API_KEY=<your-groq-api-key>
GROQ_MODEL=<your-model-id>
GROQ_BASE_URL=https://api.groq.com/openai/v1
LLM_TIMEOUT_SECONDS=15.0
```

The response includes `answer_mode` (`"llm"` or `"template"`) and `llm_fallback_reason` (null when LLM succeeded, otherwise one of: `provider_none`, `missing_api_key`, `missing_model`, `http_error_<status>`, `timeout`, `network_error`, `empty_response`, `rejected_by_postcheck`, `no_evidence`).

**Safety rules (always enforced):**
- Never fabricates positions or invents data not in the evidence.
- Forbidden phrases (`"live location"`, `"live GPS"`, `"safe landing site"`) cause automatic fallback.
- API key is never logged or returned in any response.

---

## 8. Switching to PostgreSQL

The models and migrations are designed to be database-agnostic. To use PostgreSQL + PostGIS:

1. Update `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/space_explorer
   ```
2. Enable the PostGIS extension in your database:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```
3. Run Alembic migrations (after generating them — see §9):
   ```powershell
   .\.venv\Scripts\alembic upgrade head
   ```

---

## 9. Alembic Migrations

Alembic is installed and `backend/migrations/env.py` is fully configured for both SQLite (batch mode) and PostgreSQL. However, **no migration scripts have been generated yet** — `backend/migrations/versions/` contains only `.gitkeep`.

Currently, tables are created automatically at startup via `Base.metadata.create_all()`.

To generate the initial migration snapshot (needed before switching to PostgreSQL):
```powershell
.\.venv\Scripts\alembic revision --autogenerate -m "Initial schema"
.\.venv\Scripts\alembic upgrade head
```

---

## 10. Known Limitations

| Limitation | Detail |
|---|---|
| **No authentication** | Write endpoints on `/api/v1/lunar/sites` (POST/PUT/DELETE) are unprotected. Auth is deferred. |
| **No real-time telemetry** | All positions come from the NASA PDS PLACES archive (published products). No live feed. |
| **No SPICE kernels bundled** | `observed_at` timestamps in GeoJSON features are `null` — SPICE kernel conversion requires a local kernel set not included in the repo. |
| **No Alembic migration scripts** | Tables are created from SQLAlchemy models on startup. Run `alembic revision --autogenerate` before PostgreSQL migration. |
| **Docker not tested on dev machine** | Dockerfile and docker-compose.yml are written but not verified (Docker daemon not installed). |
| **SQLite on ephemeral hosts** | On cloud platforms with ephemeral filesystems, the SQLite `.db` file is lost on restart. Use `DATABASE_URL` with a managed PostgreSQL instance. |
| **Lunar candidate sites are placeholders** | The 2 seeded lunar sites (`site-shackleton-01`, `site-haworth-01`) are planning-support zones for demonstration. They are marked `is_placeholder: true` and do not constitute certified or recommended landing targets. |
| **Mars body-fixed frame name** | The PLACES SIS does not state the Mars body-fixed frame name. The coordinate frame is described as stated in the label. |

---

## 11. What is Placeholder Data?

Records where `is_placeholder: true` are **demonstration records seeded at startup**. They are not derived from official measurement products and must not be used for scientific analysis.

| Record Type | Placeholder Reason |
|---|---|
| Celestial bodies (mars, moon) | Seeded from mission catalog summaries, not a PDS measurement product. |
| Missions (mars-2020, artemis) | Seeded from public mission metadata. |
| Rovers (perseverance, curiosity) | Seeded from public explorer metadata. |
| Lunar candidate sites | 2 planning-support zones for Backend B / Frontend integration testing. |
| Images, events, health | Demonstrative records; no live image archive is ingested. |

**PLACES localization rows (500 records) are real data** from `best_interp.csv` and carry `is_placeholder: false` with `label: "Estimated"` per the PLACES archive documentation.

---

## 12. NASA Data Credits

This project uses publicly available data products from NASA archives:

- **NASA Planetary Data System (PDS) — Geosciences Node**  
  Mars 2020 Rover PLACES Localization Products (`best_interp.csv`)  
  Archive: https://pds-geosciences.wustl.edu/missions/mars2020/places.htm  
  Organization: NASA / Jet Propulsion Laboratory / Washington University in St. Louis

- **NASA-AMMOS MMGIS (Multi-Mission Geographic Information System)**  
  Map layer configuration format reference  
  https://github.com/NASA-AMMOS/MMGIS

- **LRO LOLA (Lunar Reconnaissance Orbiter — Lunar Orbiter Laser Altimeter)**  
  Referenced in SRS for planned lunar DEM terrain analysis (Backend B scope)  
  https://imbrium.mit.edu/

> All data used in this project is from public NASA archives. This software is a research and educational tool developed for the NASA Space Apps 2026 hackathon. It is not an official NASA product.
