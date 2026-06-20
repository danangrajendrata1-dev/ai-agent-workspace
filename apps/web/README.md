# Personal AI Agent Workspace Frontend

Frontend for Personal AI Agent Workspace v2.1.

## Production Architecture

```txt
Vercel Next.js frontend
  -> Cloud Run FastAPI backend
  -> Neon PostgreSQL
```

## Stack

- Next.js App Router
- JavaScript only
- Tailwind CSS

## Current MVP Surfaces

- Landing page
- Login page with protected route flow
- Antique Ivory dashboard workspace
- Create Agent modal
- Pinned and active agents in localStorage
- Command draft mode, UI-only
- Safety Center read-only summaries
- Import Skill preview-only
- GitHub Skill Import preview may fetch text from GitHub, but it stays review-only and non-executable
- n8n workflow preview-only
- Settings preview-only
- Read-only agent, task, and approval detail pages

## Environment

Create `.env.local` from `.env.example` and set:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

In production, set `NEXT_PUBLIC_API_BASE_URL` to the deployed Cloud Run backend URL.

See [VERCEL.md](../../VERCEL.md) for the Vercel deployment checklist.

## Local Run

```powershell
cd apps/web
npm install
npm run dev
```

Optional checks:

```powershell
npm run lint
npm run build
```

## Safety Boundaries

- Runtime execution disabled in MVP
- No n8n execution in MVP
- No GitHub import execution in MVP
- GitHub Skill Import is not execution
- Current approve-skill review can save reviewed skill records into the registry, but it does not enable runtime execution
- No credential, API key, or secret save in MVP
- No model test or tool execution in MVP
- No TypeScript source for MVP
- Frontend stores only the access token for auth

## Notes

- `POST /agents` is used only for Create Agent Save.
- `GET /skills` and `GET /model-providers` are read-only.
- `GET /logs/activity`, `GET /logs/audit`, `GET /tasks`, and `GET /approvals/pending` are read-only summaries.
- See [VERCEL.md](../../VERCEL.md) for frontend deployment and smoke notes.
