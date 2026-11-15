# Space Explorer Backend Deployment Guide
NASA Space Apps 2026 — Team Astra Motion  
Document: `docs/deployment_notes.md`  
Reference: `docs/Space_Explorer_BackendA_Plan.pdf` (Section 14)

---

## 1. Overview & Architecture

Space Explorer Backend A is built with Python 3.10+, FastAPI, and SQLAlchemy. It can run in containerized environments (Docker / OCI) or on generic cloud hosting platforms (e.g. AWS ECS/App Runner, GCP Cloud Run, Render, Railway, DigitalOcean App Platform, Fly.io, or VPS).

The production architecture consists of:
- **FastAPI Application**: Web process managed by an ASGI server (Uvicorn / Gunicorn).
- **Database**: PostgreSQL with PostGIS extension (or SQLite with persistent volume).
- **Static & GeoJSON Exporters**: Output layers for NASA-AMMOS MMGIS.
- **AI Mission Assistant**: Integration with OpenAI-compatible LLM endpoints (Groq).

> **Note on Cloud Quotas & Limits:** Cloud hosting resource allocations, bandwidth allowances, and persistent volume limits vary across hosting environments. Verify host environment settings and persistent disk capabilities before deployment.

---

## 2. Environment Variables Configuration

Set all environment variables in the hosting provider's management console or secret store. **Never commit `.env` to the source repository.**

| Variable | Required | Production Recommendation | Description |
|---|:---:|---|---|
| `DATABASE_URL` | **Yes** | `postgresql://...` or `sqlite:///./space_explorer.db` | Connection URI for the database. |
| `CORS_ORIGINS` | **Yes** | `https://your-frontend-domain.com` | Comma-separated list of allowed frontend origins. |
| `ADMIN_KEY` | Optional | Random 32+ char secret string | When set, write operations (POST, PUT, DELETE) on candidate landing sites require `x-admin-key: <ADMIN_KEY>`. GET stays public. Unset in local dev. |
| `GROQ_API_KEY` | Optional | Valid API key | Groq API key for AI Mission Assistant. When unset, template-based fallback responses are used. |
| `GROQ_MODEL` | Optional | `llama-3.3-70b-versatile` | Groq model identifier for AI Mission Assistant queries. |
| `NASA_API_KEY` | Optional | NASA Open API key | NASA Open API key for higher rate limits on APOD/imagery. Falls back to DEMO_KEY when omitted. |
| `BOOTSTRAP_ON_START` | Optional | `false` (or `true` on initial setup) | Set to `true` to run `scripts/bootstrap.py` on container startup (copies seed DB, downloads missing kernels/DEM, regenerates rasters). |
| `APP_NAME` | No | `"Space Explorer API"` | Name displayed in docs and health metadata. |
| `APP_ENV` | Yes | `production` | Environment mode (`development`, `staging`, `production`). |
| `DEBUG` | Yes | `False` | Disables debug logs and traceback exposure. |
| `API_V1_PREFIX` | No | `/api/v1` | URL routing prefix for API endpoints. |
| `HOST` | Yes | `0.0.0.0` | Bind host address. |
| `PORT` | Yes | `8000` (or host `$PORT`) | Server listening port. |
| `SECRET_KEY` | **Yes** | 64+ char random hex | Cryptographic secret for signing tokens and internal checks. |
| `LLM_PROVIDER` | No | `groq` or `none` | AI provider (`groq` for LLM, `none` for deterministic template). |

---

## 3. Database Strategy: SQLite vs. Hosted PostgreSQL + PostGIS

### The SQLite Tradeoff
- **Local Dev / Small VPS**: SQLite works with zero configuration for local development or single-node VPS setups where the filesystem is backed by persistent block storage.
- **Ephemeral Containers & Serverless Caution**: On platforms with ephemeral filesystems (e.g., standard serverless containers or instances that re-create storage on every deployment/restart), an SQLite `.db` file **will be deleted upon container restart or redeploy**.
- **Mitigation if using SQLite in Containers**:
  - The database seeding and the PLACES import pipeline must run during the Docker build step (baking the `.db` file into the immutable container image), OR
  - Run via an entrypoint startup script prior to launching Uvicorn (`python -m data_pipeline.pipelines.places_import --limit 500`).

### Production Recommendation: Hosted PostgreSQL + PostGIS
For multi-replica deployments, scalability, and geospatial indexing:
1. Provision a managed PostgreSQL instance with PostGIS enabled:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```
2. Update the `DATABASE_URL` environment variable:
   ```env
   DATABASE_URL=postgresql://<db_user>:<db_password>@<db_host>:<db_port>/<db_name>
   ```
3. Run Alembic migrations and seed data on initial deployment:
   ```bash
   alembic upgrade head
   python -m data_pipeline.pipelines.places_import --limit 500
   ```

---

## 4. CORS & Security Hardening

1. **Frontend CORS Configuration:**
   Configure `CORS_ORIGINS` with the exact HTTPS domain of the deployed frontend:
   ```env
   CORS_ORIGINS=https://explorer.example.com,https://staging.explorer.example.com
   ```
   Never use wildcard `*` with credentials enabled in production.

2. **HTTPS & TLS Termination:**
   All production traffic must be served over HTTPS. Terminate TLS at the cloud load balancer, Cloudflare proxy, or reverse proxy (Nginx / Caddy).

3. **Secure HTTP Headers:**
   Configure the reverse proxy or ASGI middleware to add security headers:
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Referrer-Policy: strict-origin-when-cross-origin`

4. **Secrets Management:**
   - Store API keys (`GROQ_API_KEY`) and `SECRET_KEY` exclusively in host-level secret managers (e.g. AWS Secrets Manager, GCP Secret Manager, Render/Railway secret variables).
   - Verify `.env` is absent from version control.

---

## 5. Startup & Health Checks

Configure the container or service orchestrator with the following operational checks:

- **Liveness / Readiness Probe**:
  - Method: `GET`
  - Path: `/health`
  - Expected Status: `200 OK`
  - Response:
    ```json
    {
      "status": "ok",
      "app": "Space Explorer API",
      "version": "0.1.0",
      "environment": "production",
      "database": "postgresql",
      "is_placeholder": false
    }
    ```

- **Production Run Command**:
  Run Uvicorn without `--reload`, binding to `0.0.0.0`, with the port taken from the `PORT` environment variable (falling back to 8000):
  ```bash
  uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
  ```
  Or using Python module syntax:
  ```bash
  python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
  ```

---

## 6. Click-by-Click Deployment Guides

### Deploying the Backend on Render

1. **Sign in to Render:**
   Navigate to the Render dashboard and click **New +** -> **Web Service**.
2. **Connect Repository:**
   Select your GitHub repository (`space-explorer1`) and click **Connect**.
   *(Note: Alternatively, you can use the Blueprint feature which will automatically detect `render.yaml` at the root).*
3. **Configure Service Settings:**
   - **Name:** `space-explorer-backend` (or your choice)
   - **Region:** Choose a region close to your users (e.g. Frankfurt, Oregon, Ohio)
   - **Branch:** `main`
   - **Root Directory:** `BACKEND`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
4. **Configure Health Check Path:**
   - Expand **Advanced** settings.
   - Set **Health Check Path** to `/health`.
5. **Set Environment Variables:**
   Under the **Environment Variables** tab, add:
   - `PYTHON_VERSION`: `3.10.11`
   - `BOOTSTRAP_ON_START`: `true`
   - `CORS_ORIGINS`: `https://your-frontend-app.vercel.app,http://localhost:5173` *(update with your Vercel domain once deployed)*
   - `ADMIN_KEY`: `<generate-a-secure-secret-key>`
   - `GROQ_API_KEY`: `<your-groq-api-key>` *(optional, enables LLM assistant)*
   - `GROQ_MODEL`: `llama-3.3-70b-versatile` *(optional)*
   - `NASA_API_KEY`: `<your-nasa-open-api-key>` *(optional)*
6. **Deploy:**
   Click **Create Web Service**. Wait for the build and initial health check to succeed.
   Copy your service URL (e.g., `https://space-explorer-backend.onrender.com`).

---

### Deploying the Frontend on Vercel

1. **Sign in to Vercel:**
   Go to the Vercel dashboard and click **Add New...** -> **Project**.
2. **Import Git Repository:**
   Find and import the `space-explorer1` repository.
3. **Configure Project:**
   - **Project Name:** `space-explorer-frontend` (or your choice)
   - **Framework Preset:** `Vite`
   - **Root Directory:** Click **Edit** and select `frontend`.
   - **Build Command:** `npm run build` (default)
   - **Output Directory:** `dist` (default)
   - **Install Command:** `npm install` (default)
4. **Set Environment Variables:**
   Under **Environment Variables**, add:
   - `VITE_API_BASE_URL`: `https://space-explorer-backend.onrender.com` *(paste your backend Render URL without trailing slash)*
5. **Deploy:**
   Click **Deploy**.
   Vercel will build the frontend and serve it globally with SPA routing configured via `frontend/vercel.json`.
6. **Update Backend CORS:**
   Copy the assigned Vercel URL (e.g., `https://space-explorer-frontend.vercel.app`) and update the `CORS_ORIGINS` variable in your Render dashboard so the backend permits requests from your frontend domain.

---

## 7. Backup & Disaster Recovery Note

- **PostgreSQL**: Configure automated daily snapshots with point-in-time recovery (PITR) through your cloud database provider.
- **PLACES Raw Data**: The PDS raw CSV files can be downloaded from the NASA PDS Geosciences Node at any time. Keep raw archives cached in an S3-compatible object bucket if air-gapped rebuilding is needed.
- **SQLite Fallback**: If running SQLite on a persistent volume, configure Litestream or scheduled cron snapshots to upload `space_explorer.db` to object storage.
