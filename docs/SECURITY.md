# Security Rules v2.1 — Personal AI Agent Workspace

## 1. Purpose

This document defines the security rules for the Personal AI Agent Workspace. The system is designed as a private single-user workspace for creating, configuring, monitoring, and limiting AI agents.

Security is a core feature because agents may access model providers, memory, n8n workflows, GitHub, databases, messaging tools, and external APIs.

## 2. Security Principles

- Private by default: the workspace is for the owner only during MVP.
- Least privilege: every agent, tool, memory scope, and provider gets only the minimum access needed.
- Explicit approval: risky actions must never execute without owner approval.
- Traceability: every agent decision, tool call, approval, error, and model call must be logged.
- No hidden execution: imported GitHub tools and terminal commands are disabled by default.
- Stable stack: frontend uses JavaScript, backend uses Python. No TypeScript for MVP.
- Safe failure: if a provider, tool, or permission check fails, the task must stop safely.

## 3. Approved Technology Boundaries

| Area | Allowed | Security Note |
| --- | --- | --- |
| Frontend | JavaScript + Next.js | No TypeScript for MVP. Avoid unnecessary dependencies. |
| Backend | Python + FastAPI | Use route-service-repository structure and typed Pydantic schemas. |
| Database | PostgreSQL / Neon | Use migrations, indexes, constraints, and no plaintext secrets. |
| Automation | n8n | Use private webhooks, signed secrets, and approval for risky workflows. |
| Agent Runtime | Hermes | Runtime must obey workspace permissions and logging. |
| Model Gateway | OpenClaw private gateway | Subscription/OAuth route must be private and owner-only. |

## 4. Authentication and Session Rules

- MVP uses owner/admin login only.
- Use secure password hashing for stored passwords.
- Use JWT or secure session cookies with expiration.
- Logout must invalidate client session state.
- Important endpoints require authenticated owner access.
- Add rate limiting for login, model execution, GitHub import, approval, and tool execution endpoints.
- Never expose admin-only routes without backend authorization checks.

## 5. Secrets and Credential Rules

- API keys, OAuth tokens, database URLs, webhook secrets, GitHub tokens, and OpenClaw credentials must be stored in environment variables, secret manager, encrypted storage, or external secure service.
- Do not show secrets in the UI, logs, error messages, screenshots, or exported files.
- Mask secret-like values when displaying configuration.
- Never commit `.env` files or real credentials to GitHub.
- Use separate credentials for development and production.
- Rotate credentials if logs, repo history, or screenshots may have exposed them.
- `sensitive_config_reference` memory may store only a reference label, never the secret itself.

## 6. Model Provider Security

The workspace supports two model provider paths:

```txt
API Provider:
Workspace Backend -> OpenAI/Gemini/OpenRouter API

Subscription/OAuth Provider:
Workspace Backend -> OpenClaw Gateway -> ChatGPT/Codex OAuth
```

Rules:

- API providers require API keys and normal provider billing/free-tier limits.
- Subscription/OAuth provider through OpenClaw is for private owner use only.
- OpenClaw Gateway must not be exposed publicly without strong authentication and private network controls.
- Every model request must be logged with provider, model, agent, task_id, status, duration, and token/cost estimate when available.
- Every agent may support a fallback provider, but fallback must not bypass approval or permission rules.

## 7. Agent Permission Rules

Each agent must have an explicit security profile.

Required profile fields:

- Allowed tools.
- Blocked tools.
- Memory scope.
- Approval rules.
- Max steps.
- Max runtime.
- Max token/cost budget.
- Status.

Rules:

- Inactive agents cannot execute tasks.
- A tool is unavailable unless explicitly allowed.
- A blocked tool must never execute for that agent.
- Block rules override allow rules.
- High and critical tools require approval even when allowed.

## 8. Tool Risk Levels

| Risk Level | Examples | Default Behavior | Approval |
| --- | --- | --- | --- |
| Low | Summarize, translate text, classify intent, draft response | Can run automatically if allowed | Not required |
| Medium | Read database, read GitHub repo, call safe n8n workflow | Allowed only per agent permission | Optional or configurable |
| High | Send message/email, write database, create GitHub issue/PR, upload file, preview/register GitHub-imported tool | Must create approval request | Required |
| Critical | Deploy VPS, run terminal command, delete data, execute GitHub-imported tool | Disabled by default | Required + explicit enable + allowlist |

## 9. GitHub Imported Tool Risk Rule

To remove ambiguity:

- Previewing or registering an imported GitHub tool is high risk.
- Executing an imported GitHub tool is critical.
- Imported GitHub tool execution is disabled for MVP.
- Future execution requires sandboxing, allowlist, explicit owner enablement, approval, and full logging.

## 10. Approval Rules

The following actions must require approval before execution:

- Sending messages or emails.
- Writing, updating, or deleting important data.
- Creating pull requests or pushing code.
- Running terminal commands or deployment steps.
- Calling high-risk n8n workflows.
- Executing any imported tool from GitHub.
- Accessing sensitive memory outside the default scope.

Approval requests must show:

- Agent name.
- Requested action.
- Selected skill.
- Tool name.
- Tool input preview.
- Risk level.
- Reason.
- Approve/reject buttons.

## 11. GitHub Skill and Tool Import Rules

- GitHub skill import is allowed for MVP as text-based instruction import.
- Imported SKILL.md files must be previewed before saving to registry.
- Imported skills must be versioned and disabled/enabled by owner.
- GitHub tool import is preview/registry only for MVP.
- GitHub tool import must not execute automatically in MVP.
- Imported GitHub tool execution is critical and disabled.
- Repository URL, commit hash, imported files, reviewer, and activation status must be logged.
- Current GitHub import preview may fetch text from GitHub, and `approve-skill` may save reviewed skill records, but import is still not execution.

Phase 2 planning reference: see `docs/PHASE_2_SKILL_N8N_ARCHITECTURE.md`.
Future backend contract reference: see `docs/PHASE_2_FUTURE_BACKEND_CONTRACTS.md`.
Future data model reference: see `docs/PHASE_2_FUTURE_DATA_MODEL.md`.
Future frontend UX reference: see `docs/PHASE_2_FUTURE_FRONTEND_UX.md`.
Backend module plan reference: see `docs/PHASE_2_BACKEND_MODULE_PLAN.md`.

## 12. Memory Security Rules

Canonical memory types:

- `profile`
- `contact`
- `project`
- `agent_instruction`
- `task_history`
- `skill`
- `sensitive_config_reference`

Rules:

- Agents can only access memory categories assigned to them.
- Contact memory must not be exposed to coding or public-output agents unless explicitly allowed.
- Secrets must not be stored as normal memory.
- `sensitive_config_reference` stores reference labels only, not plaintext secrets.
- User must be able to edit or delete memory.
- Memory reads and writes must be logged.

## 13. n8n Integration Security

- Use private webhook URLs and shared secrets.
- Do not expose dangerous workflows without approval gates.
- Every n8n workflow call must include `request_id` and `agent_id`.
- High-risk workflows must wait for workspace approval before execution.
- n8n credentials must stay inside n8n or secure environment variables, not in agent memory.

## 14. GitHub and VPS Tool Security

- Read-only GitHub tools are preferred for MVP.
- Creating pull requests is allowed only after approval.
- Direct push to protected branches is forbidden for MVP.
- Terminal/VPS commands are disabled by default.
- If terminal tools are added later, they must use an allowlist and sandboxed environment.
- Deploy actions require explicit approval and detailed preview.

## 15. Logging and Debugging Rules

Every task must have `request_id` and `session_id` when available.

Canonical task lifecycle:

```txt
received
thinking
loading_memory
selecting_skill
selecting_tool
waiting_approval
running_tool
completed
failed
cancelled
```

Log these events when applicable:

- Task received.
- Agent selected.
- Memory loaded.
- Skill selected.
- Tool selected.
- Approval requested.
- Approval approved/rejected.
- Tool blocked.
- Tool executed.
- Model provider called.
- Task completed.
- Task failed.
- Task cancelled.

Rules:

- Log model provider usage without leaking prompts containing secrets.
- Log tool input/output with secret masking.
- Log approval decisions and reviewer identity.
- Provide debug filters by agent, skill, tool, provider, status, error, and date.

## 16. Deployment Security

- Frontend on Vercel must call only authenticated backend endpoints.
- Backend on Google Cloud Run must use environment variables for secrets.
- Neon database must use SSL connections.
- OpenClaw Gateway and n8n should be private or protected behind strong authentication.
- CORS must allow only approved frontend origins.
- Production logs must not reveal secrets or sensitive message content unnecessarily.

## 17. MVP Security Checklist

1. Admin login implemented.
2. Environment variables configured and `.env` ignored.
3. Agent permissions enforced in backend service layer.
4. Blocked tools enforced in backend service layer.
5. Approval required for high-risk and critical tools.
6. GitHub imported skills previewed before activation.
7. GitHub imported tools disabled for execution.
8. OpenClaw Gateway configured as private provider only.
9. n8n webhooks protected with secrets.
10. Activity logs and audit logs written for every important action.
11. Frontend uses JavaScript only.
12. Backend uses Python only.

## 18. Final Security Rule

Agent boleh berpikir, memilih skill, dan membuat rencana. Agent tidak boleh menjalankan aksi berisiko tanpa permission, approval, dan logging yang jelas.

## 19. Production Security Notes

- Frontend must call only the Cloud Run backend URL configured in `NEXT_PUBLIC_API_BASE_URL`.
- Backend `CORS_ORIGINS` must be a JSON array of approved frontend origins only.
- Do not store raw API keys, OAuth tokens, database URLs, or webhook secrets in browser storage.
- Do not expose raw provider secrets in UI, logs, smoke output, or exported docs.
- Read-only surfaces for logs, tasks, approvals, audit, and safety must fail closed.
- Deferred runtime features stay disabled until explicitly implemented and approved:
  - Real tool execution
  - Real n8n execution
  - Real OAuth execution
  - External model runtime from frontend
  - Hermes/OpenClaw runtime execution from frontend
