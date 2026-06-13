# Personal AI Agent Workspace Docs v2.1

This folder contains consistency-fixed Markdown documentation for the Personal AI Agent Workspace.

Use these files in the repository:

```txt
AGENTS.md
docs/PRD.md
docs/TECHNICAL.md
docs/DATABASE.md
docs/SECURITY.md
docs/CONSISTENCY_FIXES.md
```

Main v2.1 fixes:

- Removed undefined `skill_sources` and `tool_sources` references.
- Unified `skills.status` and `tools.status` as `active`, `inactive`, `disabled`.
- Unified task lifecycle statuses.
- Unified memory categories.
- Added explicit `agent_tools.permission_mode` for allowed/blocked tools.
- Clarified GitHub imported tool risk: preview/register = high risk, execution = critical and disabled for MVP.

Project rules remain:

- Frontend: Next.js + JavaScript + Tailwind CSS.
- Backend: FastAPI + Python.
- No TypeScript for MVP.
- Private single-user MVP.
- Sensitive actions require approval and logging.
