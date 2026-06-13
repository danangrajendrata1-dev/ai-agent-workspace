# AGENTS.md — Personal AI Agent Workspace

This file defines the working rules for AI coding agents, contributors, and automation tools in this repository.

The project is a private Personal AI Agent Workspace for creating, configuring, monitoring, and limiting AI agents. The system includes agent management, skill/tool registry, GitHub skill import, GitHub tool preview, model provider routing, OpenClaw subscription/OAuth provider support, n8n workflow execution, approval center, activity logs, and memory management.

---

## 1. Core Project Rules

1. Build incrementally and safely.
2. Do not perform large refactors without explicit approval.
3. Do not change architecture, database schema, auth, security rules, or deployment assumptions without approval.
4. Prioritize clean code, maintainability, debugging, and security.
5. Always preserve the private single-user MVP scope unless told otherwise.
6. All risky agent actions must require permission, approval, and logging.

---

## 2. Language Rules

This project uses only two main programming languages:

- Frontend: JavaScript
- Backend: Python

Rules:

- Do not use TypeScript for MVP.
- Do not introduce Go, Rust, Java, PHP, Ruby, C#, or other application languages without explicit approval.
- CSS, HTML, YAML, Dockerfile, Shell, or PowerShell may exist only as supporting files/config/scripts.
- Core frontend logic must remain JavaScript.
- Core backend, agent API, and tool logic must remain Python.

---

## 3. Approved Stack

Frontend:

- Next.js
- JavaScript
- Tailwind CSS

Backend:

- FastAPI
- Python
- SQLAlchemy
- Alembic
- Pydantic

Database:

- PostgreSQL / Neon

Supporting services:

- n8n as workflow executor
- Hermes as agent runtime
- OpenClaw as private model gateway/subscription OAuth route
- Redis/worker may be added later only when needed

Deployment target:

- Frontend: Vercel
- Backend: Google Cloud Run
- Database: Neon
- n8n/OpenClaw: private service/VPS/local private gateway

---

## 4. Architecture Rules

Use a clean modular architecture.

Backend flow:

```txt
route -> service -> repository -> database
```

Responsibilities:

- Routes handle HTTP request/response only.
- Schemas validate request and response data.
- Services contain business logic.
- Repositories contain database queries.
- Models define SQLAlchemy database tables.
- Core contains config, auth, security, permissions, and shared dependencies.
- Utils contain reusable helpers only.

Do not put business logic directly in routes.
Do not duplicate permission checks in random places.
Centralize security-sensitive checks in services/core helpers.

---

## 5. Frontend Rules

Frontend must use JavaScript with Next.js.

Rules:

- No TypeScript for MVP.
- Keep components small and readable.
- Separate page components, reusable components, and API client functions.
- Keep UI responsive for desktop, tablet, and mobile.
- Do not expose secrets in frontend code.
- Do not hardcode production API keys, tokens, or private URLs.
- Use clear loading, empty, error, and success states.
- Approval and monitoring screens must clearly show what the agent is doing.

Recommended frontend structure:

```txt
apps/web/
  app/
  components/
  lib/
  services/
  styles/
```

---

## 6. Backend Rules

Backend must use Python with FastAPI.

Rules:

- Use Pydantic schemas for all request/response validation.
- Use SQLAlchemy models and repositories for database access.
- Use Alembic for migrations.
- Use clear error handling.
- Use environment variables for configuration.
- Do not leak secrets in API responses or logs.
- Add tests for important business logic when possible.

Recommended backend structure:

```txt
apps/api/
  app/
    main.py
    core/
    models/
    schemas/
    services/
    repositories/
    routes/
    agents/
    tools/
    memory/
    integrations/
    utils/
  alembic/
  tests/
```

---

## 7. Agent System Rules

Agents must never be treated as fully trusted.

Each agent must have:

- Name
- Role
- System instruction
- Default model provider
- Assigned skills
- Allowed tools
- Blocked tools
- Memory access scope
- Approval rules
- Max execution steps
- Max runtime
- Max token/cost limit

Agents may:

- Think and plan.
- Select skills.
- Request tools.
- Ask for approval.
- Produce final responses.

Agents must not:

- Execute risky tools without approval.
- Read memory outside their allowed scope.
- Access secrets directly.
- Run imported GitHub tools automatically.
- Deploy, delete, push, or send messages without explicit approval.

---

## 8. Skill Rules

Skill means instruction/SOP for an agent.

Skills may come from:

- Manual workspace input
- GitHub import
- Internal templates

A skill should define:

- Name
- Description
- When to use
- Steps
- Allowed tools
- Output format
- Risk level
- Approval requirements

GitHub imported skills must be previewed before activation.
Do not auto-activate imported skills without owner review.

---

## 9. Tool Rules

Tool means an executable capability.

Examples:

- run_n8n_workflow
- send_telegram_message
- send_email
- github_read_repo
- github_create_pull_request
- read_database
- write_database
- translate_text
- transcribe_audio
- upload_file

Every tool must have:

- Name
- Description
- Input schema
- Output schema
- Risk level
- Approval requirement
- Timeout
- Allowed/blocked agent rules
- Enabled/disabled state

Risk levels:

- Low: summarize, translate, draft, classify
- Medium: read database, read GitHub, safe n8n workflow
- High: send message, write database, create PR, upload file, preview/register GitHub-imported tool
- Critical: terminal command, deploy, delete data, execute imported GitHub tool

High and critical tools require approval.
Critical tools are disabled by default.

---

## 10. Tool Permission Rules

MVP uses explicit tool permissions.

- No assignment means the tool is not available to the agent.
- `permission_mode = allow` means the agent may request the tool.
- `permission_mode = block` means the agent must never use the tool.
- Block wins over allow.
- High and critical tools still require approval even when allowed.
- Critical tools are disabled by default.

---

## 11. GitHub Import Rules

The workspace may import skills/tools from GitHub repositories.

MVP rules:

- GitHub skill import is allowed.
- Preview SKILL.md before saving.
- Save imported skill to registry with source and version.
- Assign imported skill to selected agents only.
- GitHub tool import is preview/registry only for MVP.
- Do not execute imported tools from GitHub in MVP.

Risk clarification:

- Previewing or registering an imported GitHub tool is high risk.
- Executing an imported GitHub tool is critical.
- Imported GitHub tool execution remains disabled for MVP unless a safe sandbox is explicitly implemented and approved in a future phase.

---

## 12. Model Provider Rules

The workspace supports two provider paths.

1. API providers:

- OpenAI API
- Gemini API
- OpenRouter
- Other API providers approved later

2. Subscription/OAuth provider:

- OpenClaw Gateway using owner ChatGPT/Codex OAuth subscription

Rules:

- API keys must be stored securely.
- OpenClaw Gateway must remain private and owner-only.
- Do not expose OpenClaw Gateway as a public API.
- Every model call must be logged with provider, model, agent, task, status, and timing.
- Provider fallback must not bypass approval or permissions.

---

## 13. Memory Rules

Memory must be permission-scoped.

Canonical memory types:

- `profile`
- `contact`
- `project`
- `agent_instruction`
- `task_history`
- `skill`
- `sensitive_config_reference`

Rules:

- Agents can only read allowed memory scopes.
- Secrets must not be stored as normal memory.
- `sensitive_config_reference` stores reference labels only, not plaintext secrets.
- User must be able to edit and delete memory.
- Memory reads/writes must be logged.
- Sensitive contact memory must not be exposed to unrelated agents.

---

## 14. Approval Rules

Approval is required before:

- Sending messages
- Sending emails
- Writing/updating/deleting important data
- Creating pull requests
- Pushing code
- Deploying to VPS/cloud
- Running terminal commands
- Calling risky n8n workflows
- Executing GitHub-imported tools

Approval request must show:

- Agent name
- Requested action
- Skill used
- Tool requested
- Input preview
- Risk level
- Reason
- Approve/reject options

---

## 15. Logging and Debugging Rules

Every agent task must have a trace.

Trace format:

```txt
input -> selected agent -> model provider -> memory -> skill -> tool -> approval -> execution -> output
```

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

Log these fields when applicable:

- request_id
- session_id
- agent_id
- model_provider_id
- selected_skill
- selected_tool
- tool_input
- tool_output
- approval_status
- error_message
- status
- created_at
- completed_at

Do not log plaintext secrets.
Mask sensitive values.

---

## 16. Security Rules

- Use authentication for all workspace pages and APIs.
- Store secrets in environment variables or secret manager.
- Do not commit `.env` files.
- Do not expose API keys to frontend.
- Use CORS allowlist.
- Protect n8n webhooks with secrets.
- Keep OpenClaw Gateway private.
- Validate all input with schemas.
- Add rate limiting to sensitive endpoints.
- Use audit logs for security-sensitive actions.
- No terminal command execution without explicit approval and allowlist.

---

## 17. Documentation Workflow

Before implementation, keep these documents aligned:

1. PRD
2. Technical Design
3. Database Schema
4. Security Rules
5. AGENTS.md
6. README

If one document changes architecture, stack, security rules, or database schema, update the related documents too.

---

## 18. Testing Rules

Minimum tests should cover:

- Auth and permission checks
- Agent CRUD
- Skill assignment
- Tool permission validation
- Blocked tool enforcement
- Approval flow
- GitHub skill import parsing
- Model provider config validation
- Memory scope enforcement

Do not claim a feature is complete if it has not been manually tested or covered by a reasonable test.

---

## 19. Change Control Rules

Ask for approval before:

- Changing database schema
- Adding a new language or framework
- Adding a new external service
- Adding terminal/VPS execution
- Changing auth/session behavior
- Making a large refactor
- Enabling GitHub imported tool execution
- Changing deployment target

---

## 20. Final Rule

The workspace is a control center for agents. Agents may think and plan, but risky actions must go through permission checks, approval, and logs.
