# Cloud Run Deployment Guide

This repository includes a manual deployment path for the FastAPI backend.
Nothing in the container starts a migration, approval, n8n workflow, tool execution, or test run automatically.

## Production Architecture

```txt
Vercel Next.js frontend
  -> Cloud Run FastAPI backend
  -> Neon PostgreSQL
```

## Prerequisites

- Google Cloud project
- `gcloud` CLI installed and authenticated
- Cloud Run API enabled
- Artifact Registry API enabled
- Cloud Build API enabled
- `DATABASE_URL` ready for Neon
- `PROVIDER_API_KEY_ENCRYPTION_KEY` ready
- `JWT_SECRET_KEY` ready
- `AGENT_AVATAR_GCS_BUCKET` ready

## Required Environment Variables

Set these for Cloud Run:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `CORS_ORIGINS`
- `PROVIDER_API_KEY_ENCRYPTION_KEY`
- `AGENT_AVATAR_STORAGE_BACKEND`
- `AGENT_AVATAR_GCS_BUCKET`
- `AGENT_AVATAR_GCS_PREFIX`
- `AGENT_AVATAR_MAX_BYTES`
- `AGENT_AVATAR_ALLOWED_MIME_TYPES`
- `PORT` is injected by Cloud Run

Important note:

- `CORS_ORIGINS` must be a JSON array.
- Use frontend origins only.
- Do not include trailing slashes.
- Do not use `BACKEND_CORS_ORIGINS`.
- Keep the deployed CORS value aligned with the frontend URL.
- Set `DATABASE_URL` to the Neon production database.
- Set `JWT_SECRET_KEY` to a production-grade secret.
- Set `PROVIDER_API_KEY_ENCRYPTION_KEY` before using provider key vault endpoints.
- Set `AGENT_AVATAR_STORAGE_BACKEND=gcs` and `AGENT_AVATAR_GCS_BUCKET` for production avatar persistence.
- Keep avatar uploads private. Frontend never uploads directly to GCS.

## Security Notes

- Use Google Secret Manager for secrets.
- Do not put real secrets in the Dockerfile.
- Do not commit `.env`.
- Do not bake secrets into the image.

## Manual Migration Note

Migrations are not run automatically in container startup.

Run Alembic manually with a controlled command/environment:

```powershell
.venv\Scripts\python.exe -m alembic upgrade head
```

Keep production migration execution explicit and controlled. Do not hide it in the container `CMD`.

Recommended release order:

1. Deploy backend image to Cloud Run.
2. Run Alembic against Neon.
3. Confirm `GET /health` returns `200 OK`.
4. Update Vercel frontend env if backend URL changed.
5. Run smoke checklist.

## Local Docker Example

Build locally:

```powershell
docker build -t personal-ai-agent-api ./apps/api
```

Run locally:

```powershell
docker run --rm -p 8080:8080 --env-file ./apps/api/.env personal-ai-agent-api
```

Note:

- The local `--env-file` example is for development only.
- Do not casually reuse production secrets in local Docker runs.

## Artifact Registry and Cloud Run Example

Use placeholders only:

- `PROJECT_ID=your-project-id`
- `REGION=asia-southeast2`
- `REPOSITORY=personal-ai-agent`
- `IMAGE=personal-ai-agent-api`
- `SERVICE=personal-ai-agent-api`

Example commands:

```powershell
gcloud config set project PROJECT_ID
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
gcloud artifacts repositories create REPOSITORY --repository-format=docker --location=REGION
gcloud builds submit ./apps/api --tag REGION-docker.pkg.dev/PROJECT_ID/REPOSITORY/IMAGE:latest
gcloud run deploy SERVICE --image REGION-docker.pkg.dev/PROJECT_ID/REPOSITORY/IMAGE:latest --region REGION --platform managed --allow-unauthenticated
```

If you set environment variables directly, use placeholders and avoid shell history for secrets when possible:

```powershell
gcloud run services update SERVICE --region REGION --set-env-vars DATABASE_URL=YOUR_DATABASE_URL
```

Prefer Secret Manager or another managed secret source instead of inline secret values.

## Health Check

After deploy, open:

```text
https://SERVICE-xxxxx-REGION.a.run.app/health
```

The exact generated URL will differ, so do not assume a fixed suffix.

Health check is the first smoke gate.

## CORS Note

- After the frontend Vercel URL is known, set `CORS_ORIGINS` to that frontend URL as a JSON array.
- For local testing, keep localhost origins only in local environment values.

## Cloud Run Checklist

- Confirm the Cloud Run service points at the correct container image.
- Confirm `DATABASE_URL` uses the Neon production database.
- Confirm `JWT_SECRET_KEY` is a production-grade secret.
- Confirm `PROVIDER_API_KEY_ENCRYPTION_KEY` is present and stable.
- Confirm `CORS_ORIGINS` contains only the production frontend origin.
- Confirm the origin value has no trailing slash.
- Confirm the service has the correct `PORT` handling from Cloud Run.
- Confirm the backend health endpoint returns `200 OK`.
- Confirm no secret is printed in build output or logs.
- Confirm read-only endpoints keep logs, tasks, approvals, and audit data safe.

## Neon Migration Checklist

- Back up the target database state before release.
- Run Alembic migrations against the Neon database before switching traffic.
- Verify the migration chain is current.
- Confirm schema changes match the deployed backend version.
- Re-check the app after migration for missing tables or broken constraints.
- Keep a restore point before traffic switch.
- Roll back the database if the smoke gate fails after migration.

## Production Smoke Checklist

- Open the deployed frontend and confirm the login page loads.
- Confirm the frontend can call the Cloud Run backend URL.
- Confirm `GET /health` returns success.
- Confirm auth still works with the production environment.
- Confirm no console error about missing environment variables.
- Confirm the backend accepts the configured CORS origin.
- Confirm logs, tasks, approvals, and audit endpoints stay read-only.
- Confirm deferred execution paths stay disabled.

## Rollback Checklist

- Keep the previous backend image available.
- Keep the previous Neon snapshot or restore point available.
- Revert the Cloud Run revision to the last known good build if the new one fails.
- Revert frontend env only if the backend URL changes.
- Re-run the smoke checklist after rollback.
- Keep the previous Cloud Run revision available until the new release is proven.
- Keep a Neon backup or restore point before promotion.

## Deferred Features

These features stay deferred unless a later safe implementation approves them:

- Real tool execution
- Real n8n execution
- Real OAuth execution
- External model runtime from frontend
- Hermes/OpenClaw runtime execution from frontend
