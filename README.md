# Personal AI Agent Workspace v2.1

Private single-user workspace for creating and managing AI agents.

## Production Architecture

```txt
Vercel Next.js frontend
  -> Cloud Run FastAPI backend
  -> Neon PostgreSQL
```

## Production Docs

- [Cloud Run backend deployment](./apps/api/CLOUD_RUN.md)
- [Vercel frontend deployment](./VERCEL.md)
- [Technical design](./docs/TECHNICAL.md)
- [Security rules](./docs/SECURITY.md)
- [Production smoke checklist](./docs/QA_PRODUCTION_SMOKE.md)
- [Regression matrix](./docs/QA_REGRESSION_MATRIX.md)

## Current Product Shape

- Next.js App Router
- JavaScript only
- Tailwind CSS
- Login + protected dashboard
- Create Agent save flow
- Agent, skill, provider, n8n, activity, approval, and safety shell panels
- Read-only Safety Center summaries
- Import Skill preview-only
- GitHub Skill Import preview may fetch text from GitHub, but it stays review-only and non-executable
- n8n workflow preview-only
- Settings preview-only
- Runtime execution disabled

## Environment

Frontend requires:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-cloud-run-service-xxxxx-REGION.a.run.app
```

Backend requires:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/personal_ai_agent_workspace
JWT_SECRET_KEY=change-me-in-development
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
PROVIDER_API_KEY_ENCRYPTION_KEY=
AGENT_AVATAR_STORAGE_BACKEND=local
AGENT_AVATAR_LOCAL_DIR=var/uploads/agent-avatars
AGENT_AVATAR_MAX_BYTES=2097152
```

Rules:

- `CORS_ORIGINS` must be a JSON array.
- Do not include trailing slashes in origin values.
- Do not use `BACKEND_CORS_ORIGINS`.
- Frontend production env must point `NEXT_PUBLIC_API_BASE_URL` at the deployed Cloud Run backend URL.

## Safety Boundaries

- No runtime execution in MVP
- No n8n execution in MVP
- No GitHub import execution in MVP
- GitHub Skill Import is not execution
- Current approve-skill review can save reviewed skill records into the registry, but it does not enable runtime execution
- No credential, API key, or secret save in MVP
- No model test or tool execution in MVP
- No TypeScript source for MVP

## Production Checklist

1. Deploy backend to Cloud Run.
2. Run Alembic on Neon before traffic switch.
3. Set Vercel `NEXT_PUBLIC_API_BASE_URL` to backend URL.
4. Set backend `CORS_ORIGINS` to the Vercel origin.
5. Run smoke test.
6. Keep previous backend revision and previous frontend deployment ready for rollback.

## Deferred Features

- Real tool execution
- Real n8n execution unless safely implemented and approved
- Real OAuth execution unless fully implemented
- External model runtime from frontend
- Hermes/OpenClaw runtime execution from frontend

## Notes

- `docs/TECHNICAL.md` stays source of truth for architecture.
- `docs/SECURITY.md` stays source of truth for security boundaries.
- `docs/QA_PRODUCTION_SMOKE.md` stays source of truth for release gate smoke.
