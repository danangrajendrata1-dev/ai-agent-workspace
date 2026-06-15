# Cloud Run Deployment Guide

This repository now includes a Docker deployment foundation for the FastAPI backend.
Deployment is still manual. Nothing in the container starts a migration or a test run automatically.

## Prerequisites

- Google Cloud project
- `gcloud` CLI installed and authenticated
- Cloud Run API enabled
- Artifact Registry API enabled
- Cloud Build API enabled
- `DATABASE_URL` ready for Neon
- `PROVIDER_API_KEY_ENCRYPTION_KEY` ready
- `JWT_SECRET_KEY` ready

## Required Environment Variables

Set these for Cloud Run:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `CORS_ORIGINS`
- `PROVIDER_API_KEY_ENCRYPTION_KEY`
- `PORT` is injected by Cloud Run

Important note:

- The current backend config reads `BACKEND_CORS_ORIGINS`.
- Keep the deployed CORS value aligned with the frontend URL.
- If you use `CORS_ORIGINS` in your deployment notes, make sure the app is configured with the matching runtime variable it expects.

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

## CORS Note

- After the frontend Vercel URL is known, set the backend CORS origin to that frontend URL.
- For local testing, keep localhost origins only in local environment values.
