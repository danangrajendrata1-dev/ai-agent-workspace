# Vercel Deployment Guide

This document covers the frontend deployment surface for Personal AI Agent Workspace v2.1.

## Production Architecture

```txt
Vercel Next.js frontend
  -> Cloud Run FastAPI backend
  -> Neon PostgreSQL
```

## Frontend Environment

Set this in Vercel:

- `NEXT_PUBLIC_API_BASE_URL`

Rules:

- Point it at the deployed Cloud Run backend URL.
- Do not hardcode local-only URLs for production.
- Do not expose backend secrets in the frontend.
- Use only the backend base URL, not a model key, token, or webhook URL.

## Vercel Checklist

- Confirm the project uses the `apps/web` frontend.
- Confirm `NEXT_PUBLIC_API_BASE_URL` points to the Cloud Run backend.
- Confirm the backend URL is reachable from the deployed frontend.
- Confirm the login page loads without missing env warnings.
- Confirm the dashboard can make API calls to the backend.
- Confirm no secret values are present in Vercel env settings.
- Confirm the production build succeeds before release.
- Confirm read-only safety panels render without mutation buttons for blocked paths.

## Production Smoke Checklist

- Open the Vercel URL.
- Confirm the landing page or login page renders.
- Confirm the frontend can reach the backend health endpoint through the configured API base URL.
- Confirm authenticated navigation still works.
- Confirm browser console shows no missing env errors.
- Confirm logs, tasks, approvals, and safety surfaces show loading/empty/error state correctly.

## Rollback Checklist

- Keep the last known good Vercel deployment available.
- Roll back to the previous deployment if the new release breaks auth or API calls.
- Recheck the `NEXT_PUBLIC_API_BASE_URL` value after rollback.
- Run the smoke checklist again after rollback.
- Keep the previous Cloud Run backend revision available too if the frontend rollback is paired with backend env changes.
