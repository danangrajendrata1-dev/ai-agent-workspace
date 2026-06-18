# Personal AI Agent Workspace v2.1

Private single-user workspace for creating and managing AI agents.

## Current Frontend Status

- Next.js App Router
- JavaScript only
- Tailwind CSS
- Antique Ivory workspace UI
- Login + protected dashboard
- Create Agent save flow
- Pinned and active agents in localStorage
- Draft-only command input
- Read-only Safety Center summaries
- Runtime boundary freeze documentation
- Import Skill preview-only
- GitHub Skill Import preview may fetch text from GitHub, but it stays review-only and non-executable
- n8n workflow preview-only
- Settings preview-only
- Runtime execution disabled

## Environment

Frontend requires:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Safety Boundaries

- No runtime execution in MVP
- No n8n execution in MVP
- No GitHub import execution in MVP
- GitHub Skill Import is not execution
- Current approve-skill review can save reviewed skill records into the registry, but it does not enable runtime execution
- No credential, API key, or secret save in MVP
- No model test or tool execution in MVP
- No TypeScript source for MVP

## Docs

- `AGENTS.md`
- `docs/PRD.md`
- `docs/TECHNICAL.md`
- `docs/DATABASE.md`
- `docs/SECURITY.md`
- `docs/CONSISTENCY_FIXES.md`
- `docs/CODEX_STEP_BY_STEP_PERSONAL_AI_AGENT_WORKSPACE.md`
- `apps/web/README.md`
- `apps/api/README.md`

Phase 2 documentation planning is temporarily frozen after Step 65. Future documentation updates should be tied to real implementation changes, safety findings, or user-approved scope changes.
