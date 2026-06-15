# Personal AI Agent Workspace API

Initial FastAPI backend foundation for Personal AI Agent Workspace v2.1.

## Setup

```powershell
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Cloud Run Deployment

See [CLOUD_RUN.md](./CLOUD_RUN.md) for the manual Google Cloud Run deployment package, including Docker build instructions, required environment variables, and migration guidance.

## Available Endpoint

- `GET /health`

## Current GitHub Import Behavior

The current backend already exposes GitHub import review endpoints under `/github-imports`.

Important notes:

- GitHub Skill Import preview may fetch file text from GitHub, but it does not execute the content.
- `POST /github-imports/skills/preview` creates a preview record only.
- `POST /github-imports/{import_id}/approve-skill` saves reviewed skill content into the skill registry and marks the import as imported.
- `POST /github-imports/{import_id}/reject` and `POST /github-imports/{import_id}/disable` only update review state.
- No runtime execution, n8n execution, external model call, Hermes call, or OpenClaw call happens during GitHub import review.
- The future Phase 2 planning docs describe next contracts only and must not be confused with this current MVP behavior.

## Provider API Key Vault

The model provider key vault stores encrypted API keys only. Set this environment variable before using the save/delete API:

- `PROVIDER_API_KEY_ENCRYPTION_KEY`

It must be a valid Fernet key. The backend never returns raw API keys, and it does not use the stored keys for model calls yet.

## Create Local Owner Account

The backend already provides a safe local bootstrap route:

- `POST /auth/bootstrap-owner`

Important notes:

- This is for private local development setup only.
- It works only when no active owner user exists yet.
- It is not a public signup flow.
- It never returns `password_hash`.
- Do not put real credentials in source code, README, or `.env.example`.

Example PowerShell flow with placeholder values only:

```powershell
$payload = @{
  email = "owner@example.com"
  password = "change-me-local-only"
  display_name = "Owner"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/auth/bootstrap-owner" `
  -ContentType "application/json" `
  -Body $payload
```

After bootstrap succeeds once, login from frontend or API using the same local values:

```powershell
$loginPayload = @{
  email = "owner@example.com"
  password = "change-me-local-only"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/auth/login" `
  -ContentType "application/json" `
  -Body $loginPayload
```

If an active owner already exists, the bootstrap route should return a safe error and must not overwrite the account automatically.

## Smoke Tests

Lightweight backend smoke tests live in `tests/` and cover:

- `GET /health`
- OpenAPI schema loading from `/openapi.json`
- route registration for core API paths
- safety boundary checks for blocked dangerous route names

These smoke tests intentionally do not:

- connect to a real PostgreSQL database
- run Alembic migrations
- execute tools, n8n workflows, GitHub imported tools, or terminal commands
- call external model providers, Hermes, or OpenClaw
- perform real auth flows against a live database

Run them with:

```powershell
cd apps/api
.venv\Scripts\activate
pytest
```
