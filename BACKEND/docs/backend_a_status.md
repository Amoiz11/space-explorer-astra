# Space Explorer Backend A Status & Acceptance Report
NASA Space Apps 2026 — Team Astra Motion  
Document: `docs/backend_a_status.md`  
Reference: `docs/Space_Explorer_BackendA_Plan.pdf` (Section 11 & Section 14)

---

## 1. Acceptance Checklist (Section 11)

| # | Acceptance Criterion | Status | Evidence / Reason |
|---|---|:---:|---|
| 1 | `docker compose up` starts API and database. `/health` returns ok. `/docs` shows all endpoints. | **Partly** | `Dockerfile` and `docker-compose.yml` are written; `/health` and `/docs` work via Uvicorn, but Docker daemon is not installed on the dev machine so `docker compose` is untested. |
| 2 | Migrations create every table in Section 4. Seed data loads. | **Done** | Migration script `f8b11b740726_initial_schema.py` generated and verified against an empty temp SQLite DB: `alembic upgrade head` created all 14 tables including `candidate_landing_sites`. Seed data loads at startup via `init_database()`. Both approaches coexist: `create_all()` for fast startup, Alembic for PostgreSQL migration. |
| 3 | `/lunar/sites` supports create, read, update, delete and the Frontend can call it with CORS. | **Done** | Full CRUD lifecycle tested via pytest (`test_lunar_sites_crud`), with configurable `CORSMiddleware` enabled. |
| 4 | Core mission endpoints return data from the database with source and label fields. | **Done** | Bodies, missions, rovers, locations, images, events, analytics, and timeline endpoints return DB records with `source_label`, `label`, and `is_placeholder`. |
| 5 | Admin endpoints reject unauthenticated and non-admin users. | **Not done** | Auth and admin phase was intentionally deferred in hackathon scope; `/api/v1/auth/*` and `/api/v1/admin/status` are open placeholder stubs. |
| 6 | The PLACES import runs reproducibly and keeps product ID, observation time and frame. | **Done** | `data_pipeline.pipelines.places_import` imports 500 records reproducibly, preserving source product ID, observation time, structured coordinate frame, and planetocentric coordinates. |
| 7 | Unknown or unsupported positions are never fabricated. | **Done** | Curiosity rover returns null coordinates with status and method `unknown`; missing positions are never guessed or filled. |
| 8 | Assistant gives citations or says data is not available. | **Done** | AI assistant returns exact refusal "Data not available in the approved sources." with empty citations when evidence is absent, and returns source citations when evidence is found. |
| 9 | Automated tests run with one command. README explains setup. | **Done** | `.\test.ps1` runs 71 automated tests in an isolated temporary database in ~1.5s; setup and test steps are documented in `README.md`. |

### Summary Counts
- **Done: 7**
- **Partly: 1**
- **Not done: 1** (`Admin endpoints reject unauthenticated and non-admin users`)
- **Not applicable:** 0
- **Total:** 9 criteria

---

## 2. Test Types Coverage (Section 11)

- **Unit Tests:** **Done**. Parsing (`places_parser`), coordinate validators, business rule labels, citation deduplication, and helper calculations.
- **Integration Tests:** **Done**. PDS pipeline parser and loader, temporary SQLite database session, REST API endpoints, and GeoJSON layer exporters.
- **Scientific Validation:** **Done**. Validated PLACES coordinate parsing against PDS SIS documentation (planetocentric latitude, east-positive longitude, site 1 relative frame). Mars body-fixed frame is not stated as IAU_MARS_2000.
- **End to End:** **Done**. Verified data flow from PDS raw CSV to loader, database storage, API retrieval, GeoJSON map layers, and assistant citation generation.
- **Security:** **Partly**. Input length validation, rate limiting, and CORS are tested; JWT authentication and admin role enforcement are deferred.

---

## 3. Alembic Migrations Status

- **Status:** **Migration script generated and tested**.
- **File:** `backend/migrations/versions/f8b11b740726_initial_schema.py`
- **Tested:** `alembic upgrade head` on an empty temp SQLite DB created all 14 tables (`candidate_landing_sites`, `celestial_bodies`, `data_products`, `data_sources`, `explorers`, `health_reports`, `images`, `locations`, `mission_events`, `missions`, `status_history`, `telemetry`, `trajectories`, `users`). `downgrade()` is also generated and reverses all table creations in FK-safe order.
- **Current Table Creation:** Tables are still auto-created at startup via `Base.metadata.create_all()` for fast local dev. Alembic migration is used when switching to PostgreSQL.
- **To migrate to PostgreSQL:** Set `DATABASE_URL` to a PostgreSQL URI, then run `alembic upgrade head`.

---

## 4. Security Review & Known Risks

1. **Secrets & Credentials:**
   - No production secrets or API keys are committed in Git.
   - `.env` is ignored by `.gitignore`.
   - `.env.example` provides empty placeholders (`GROQ_API_KEY=`, `GROQ_MODEL=`, placeholder `SECRET_KEY`).
   - Groq API key is never logged or exposed via API errors.

2. **File and Repository Exclusions:**
   - `.gitignore` properly covers `.env`, `*.db`, `*.db.bak`, `storage/raw`, `storage/kernels`, and `kernels`.

3. **CORS Configuration:**
   - Managed via `CORS_ORIGINS` setting in `.env`, passed to FastAPI's `CORSMiddleware`. Restricts cross-origin requests to configured frontend origins.

4. **Known Risk: Unprotected Write Endpoints:**
   - **Risk:** Write operations on candidate lunar landing sites (`POST /api/v1/lunar/sites`, `PUT /api/v1/lunar/sites/{id}`, `DELETE /api/v1/lunar/sites/{id}`) are currently open without authentication.
   - **Context:** Intentionally left open during the hackathon to avoid blocking Backend B and Frontend developers while integrating site analysis workflows.
   - **Proposed Mitigation (Not implemented):** Add a lightweight API key header dependency check:
     ```python
     # Proposed one-line header check dependency
     def verify_admin_key(x_admin_key: str = Header(...)):
         if x_admin_key != settings.SECRET_KEY:
             raise HTTPException(status_code=403, detail="Invalid admin key")
     ```
     This can be applied as `dependencies=[Depends(verify_admin_key)]` to mutating endpoints on `/api/v1/lunar/sites`.
