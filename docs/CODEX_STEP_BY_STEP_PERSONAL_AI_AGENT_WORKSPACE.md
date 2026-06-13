# Codex Step-by-Step Instructions - Personal AI Agent Workspace v2.1

Use this file as the implementation guide for Codex. Do not ask Codex to build everything at once. Run one step at a time, review the diff, test manually, then continue to the next step.

## Project Context

Project: Personal AI Agent Workspace v2.1

This is a private single-user AI Agent Workspace for creating, configuring, monitoring, and limiting AI agents. The workspace is used to create agents, manage instructions, assign skills and tools, configure model providers, monitor agent activity, approve sensitive actions, and store memory and logs.

Do not redesign the project from scratch. Follow the existing project documents:

- `AGENTS.md`
- `docs/PRD.md`
- `docs/TECHNICAL.md`
- `docs/DATABASE.md`
- `docs/SECURITY.md`
- `docs/CONSISTENCY_FIXES.md`

## Master Rules for Codex

1. Frontend must use Next.js + JavaScript + Tailwind CSS.
2. Do not use TypeScript for MVP.
3. Backend must use FastAPI + Python.
4. Database must use PostgreSQL with SQLAlchemy and Alembic.
5. Do not introduce Go, Rust, Java, PHP, Ruby, C#, or other core application languages.
6. Backend must follow `route -> service -> repository -> database`.
7. Do not put business logic directly inside routes.
8. Do not perform large refactors without approval.
9. Do not change architecture, database schema, auth rules, deployment target, or security rules without approval.
10. Do not expose secrets in frontend, logs, API responses, screenshots, or exported files.
11. GitHub imported tools must remain disabled for execution in MVP.
12. Sensitive actions must require approval and logging.
13. OpenClaw Gateway must remain private and owner-only.
14. Every important task and action must support `request_id`, structured logs, and execution trace.
15. Treat these values as canonical for MVP:
    - Task status: `received`, `thinking`, `loading_memory`, `selecting_skill`, `selecting_tool`, `waiting_approval`, `running_tool`, `completed`, `failed`, `cancelled`
    - Memory types: `profile`, `contact`, `project`, `agent_instruction`, `task_history`, `skill`, `sensitive_config_reference`
    - Skill status: `active`, `inactive`, `disabled`
    - Tool status: `active`, `inactive`, `disabled`
    - Agent tool `permission_mode`: `allow`, `block`
16. GitHub imported tool risk must always be interpreted as:
    - preview/register = high risk
    - execution = critical
    - execution remains disabled for MVP

## How to Use This File with Codex

For each step:

1. Copy only one step prompt into Codex.
2. Ask Codex to inspect the repository first.
3. Ask Codex to make a short plan before editing.
4. Let Codex implement only that step.
5. Review the changed files.
6. Run the manual test.
7. Continue to the next step only after the current step is clean.

Do not allow Codex to skip steps, build advanced runtime features early, enable GitHub imported tool execution, run unrestricted terminal commands, or deploy automatically.

## Reusable Opening Prompt for Every Step

Paste this before each step instruction:

```txt
You are working on the Personal AI Agent Workspace v2.1 project.

Before editing code:
1. Read AGENTS.md and the documents in docs/.
2. Inspect the current repository structure.
3. Make a short plan.
4. Follow JavaScript-only frontend and Python-only backend rules.
5. Do not use TypeScript.
6. Do not perform large refactors.
7. Do not change architecture, security rules, database schema, or deployment target unless the current step explicitly asks for it.
8. Work only on the current step.
9. After editing, list changed files, explain what changed, and provide manual test steps.
```

## Step 1 - Repository Review and Setup Check

**Goal:** Review the repository structure and make sure the project starts from the existing v2.1 documents, not from a new concept.

**Codex may do:**
- Inspect the current project tree.
- Confirm these files exist: `AGENTS.md`, `docs/PRD.md`, `docs/TECHNICAL.md`, `docs/DATABASE.md`, `docs/SECURITY.md`, `docs/CONSISTENCY_FIXES.md`.
- Confirm these folders exist: `apps/api`, `apps/web`, `n8n/workflows`.
- Create only the missing folders or placeholder files required for structure.

**Codex must not do:**
- Create application logic.
- Add dependencies.
- Create TypeScript files.
- Start backend or frontend implementation.

**Done when:**
- Repository has a clean root structure.
- Documentation files are in the correct place.
- `apps/api`, `apps/web`, and `n8n/workflows` exist.
- No unnecessary framework or dependency is added.

## Step 2 - Backend Foundation

**Goal:** Create the FastAPI backend foundation inside `apps/api`.

**Codex may do:**
- Create `app/main.py`.
- Create `app/core/config.py`, `app/core/database.py`, `app/core/middleware.py`.
- Create `app/routes/health.py` and package init files.
- Add `.env.example`.
- Add `requirements.txt` or `pyproject.toml`, keeping it simple.
- Use only required backend dependencies: `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `psycopg[binary]`, `pydantic`, `pydantic-settings`, `python-dotenv`.
- Implement `GET /health`.
- Add `request_id` middleware.

**Codex must not do:**
- Implement auth, agents, OpenClaw, Hermes, approvals, or n8n.
- Hardcode secrets or URLs.
- Introduce application features outside foundation.

**Done when:**
- Backend runs with `uvicorn`.
- `GET /health` returns a healthy response.
- `request_id` exists in request state or response headers.
- `.env.example` exists and `.env` is ignored by git.

## Step 3 - Database and Alembic Setup

**Goal:** Connect FastAPI backend to PostgreSQL and initialize Alembic safely.

**Codex may do:**
- Read `DATABASE_URL` from environment variables.
- Create SQLAlchemy Base.
- Create database session dependency.
- Initialize Alembic if not already initialized.
- Configure Alembic `env.py` to access SQLAlchemy metadata.

**Codex must not do:**
- Hardcode database credentials.
- Create all tables at once unless explicitly instructed.
- Change the documented schema.

**Done when:**
- Backend imports database config without error.
- Alembic is initialized.
- Alembic `env.py` reads metadata correctly.
- No real secrets are committed.

## Step 4 - Users and Admin Auth

**Goal:** Implement owner or admin authentication for the private single-user MVP.

**Codex may do:**
- Create `users` model based on `docs/DATABASE.md`.
- Use UUID primary key.
- Use `password_hash`, never plaintext password.
- Implement password hashing.
- Implement JWT or secure token auth.
- Create auth schemas: `LoginRequest`, `LoginResponse`, `CurrentUserResponse`.
- Create routes: `POST /auth/login` and `GET /auth/me`.
- Optionally create `POST /auth/bootstrap-owner` only if needed.
- Add `current_user` dependency.
- Keep auth logic in service layer and database queries in repository layer.

**Codex must not do:**
- Return password hashes.
- Create multi-user marketplace auth.
- Change auth architecture beyond MVP scope.

**Done when:**
- Owner can log in.
- `/auth/me` works with token.
- Wrong password fails safely.
- Password hash is never returned.
- Manual test steps or basic tests are provided.

## Step 5 - Model Provider Management

**Goal:** Implement model provider configuration without exposing secrets.

**Codex may do:**
- Create `model_providers` model from `docs/DATABASE.md`.
- Create schemas, repository, service, and routes.
- Support `provider_type`: `api`, `subscription_oauth`, `local`.
- Support `auth_type`: `api_key`, `oauth_gateway`, `none`.
- Store only `secret_reference`, never raw secrets.
- Mask secret-like fields in responses.
- Add protected CRUD endpoints.
- Support `active` and `inactive` provider status.
- Add OpenClaw provider placeholder, but do not call OpenClaw yet.

**Codex must not do:**
- Expose secrets in API responses.
- Implement external provider execution.
- Expose OpenClaw Gateway publicly.

**Done when:**
- Authenticated owner can create, list, update, and deactivate providers.
- API responses do not expose secrets.
- OpenClaw provider can be configured as a private placeholder.
- No external model call is implemented yet.

## Step 6 - Agent Management

**Goal:** Implement agent CRUD and instruction management.

**Codex may do:**
- Create `agents` model.
- Create `agent_instructions` model.
- Create schemas, repository, service, and routes.
- Implement create, list, detail, update, and deactivate.
- Implement instruction versioning.
- Keep only one active instruction per agent.

**Agent fields must include:**
- `name`
- `slug`
- `description`
- `role_description`
- `default_model_provider_id`
- `default_model_name`
- `status`
- `max_steps`
- `max_runtime_seconds`
- `max_token_budget`
- `requires_approval_by_default`

**Codex must not do:**
- Implement agent execution yet.
- Bypass service and repository layers.

**Done when:**
- Owner can create and manage agents.
- Agent instruction can be created and updated.
- Agent status `active` or `inactive` is respected.
- Code follows `route -> service -> repository -> database`.

## Step 7 - Skill Registry

**Goal:** Implement manual skill CRUD and agent-skill assignment.

**Codex may do:**
- Create `skills` model.
- Create `agent_skills` model.
- Create schemas, repository, service, and routes.
- Implement skill CRUD.
- Implement assign and unassign skill to agent.
- Add validation for `risk_level`.
- Support skill status: `active`, `inactive`, `disabled`.

**Skill fields must include:**
- `name`
- `slug`
- `description`
- `content`
- `source_type`
- `source_id`
- `version_label`
- `risk_level`
- `status`

**Codex must not do:**
- Auto-run skills.
- Treat skills as executable tools.

**Done when:**
- Owner can create skills.
- Owner can assign skills to agents.
- Agent detail can show assigned skills.
- Skills remain instruction or SOP text, not executable tools.

## Step 8 - GitHub Skill Import Preview

**Goal:** Implement safe GitHub `SKILL.md` import preview.

**Codex may do:**
- Create `github_imports` model.
- Implement GitHub import preview service.
- Import text-based `SKILL.md` files only.
- Require user preview before saving skill.
- Save `repo_url`, `branch`, `commit_sha` if available, `file_path`, `content_preview`, and `status`.
- Support status: `preview`, `imported`, `rejected`, `disabled`.
- Add route to preview GitHub skill.
- Add route to approve or import preview into skill registry.

**Codex must not do:**
- Execute imported code.
- Implement GitHub tool execution.
- Activate imported skills automatically without owner review.

**Done when:**
- Owner can submit GitHub repo or file URL.
- Backend previews `SKILL.md` safely.
- Owner can approve import into skill registry.
- Imported skill has `source_type = github`.
- Imported tool execution remains disabled.

## Step 9 - Tool Registry

**Goal:** Implement tool registry and agent-tool assignment using the v2.1 permission model.

**Codex may do:**
- Create `tools` model.
- Create `agent_tools` model.
- Create schemas, repository, service, and routes.
- Implement assign and unassign tool to agent.
- Enforce risk and approval rules in service layer.
- Support tool status: `active`, `inactive`, `disabled`.
- Support `agent_tools.permission_mode`: `allow`, `block`.

**Tool fields must include:**
- `name`
- `slug`
- `description`
- `tool_type`
- `source_type`
- `source_id`
- `input_schema`
- `output_schema`
- `risk_level`
- `approval_required`
- `timeout_seconds`
- `rate_limit_per_hour`
- `status`

**Agent tool fields must include:**
- `agent_id`
- `tool_id`
- `permission_mode`
- `is_enabled`
- `override_approval_required`

**Codex must not do:**
- Execute imported GitHub tools.
- Make critical tools executable by default.
- Ignore block rules.

**Risk rules to preserve:**
- `low`: can run automatically if allowed
- `medium`: depends on agent configuration
- `high`: approval required
- `critical`: disabled by default
- GitHub imported tool preview or register = high risk
- GitHub imported tool execution = critical and disabled for MVP

**Done when:**
- Owner can register tools.
- Owner can assign tools to agents.
- `permission_mode` works with `allow` and `block`.
- Block wins over allow.
- Critical tools are not executable by default.

## Step 10 - Memory Management

**Goal:** Implement scoped memory management using the canonical v2.1 memory types.

**Codex may do:**
- Create `memories` model.
- Create schemas, repository, service, and routes.
- Implement create, list, update, and delete memory.
- Filter agent-scoped memory by agent.
- Enforce memory type validation.

**Memory fields must include:**
- `owner_id`
- `agent_id` nullable
- `memory_type`
- `title`
- `content`
- `visibility_scope`
- `metadata`

**Canonical memory types:**
- `profile`
- `contact`
- `project`
- `agent_instruction`
- `task_history`
- `skill`
- `sensitive_config_reference`

**Visibility scope values:**
- `global`
- `agent`
- `private`

**Codex must not do:**
- Store plaintext secrets as memory.
- Replace canonical memory types with old values like `task`.
- Expose secret-like data in responses or logs.

**Special rule:**
- `sensitive_config_reference` may store only a label or reference to external secret storage, never the secret itself.

**Done when:**
- Owner can create, list, update, and delete memory.
- Agent-scoped memory can be filtered by agent.
- Canonical memory types are enforced.
- No secret-like data is exposed.

## Step 11 - Tasks, Task Steps, and Basic Chat

**Goal:** Implement basic chat task creation and task lifecycle without real autonomous tool execution yet.

**Codex may do:**
- Create `tasks` model.
- Create `task_steps` model.
- Create basic chat route: `POST /agents/{agent_id}/chat`.
- On chat submit:
  - create `request_id`
  - create task with status `received`
  - load agent
  - load active instruction
  - load assigned skills
  - create task steps
  - return placeholder response or simple model-router stub
- Add task detail retrieval.

**Canonical task statuses to use:**
- `received`
- `thinking`
- `loading_memory`
- `selecting_skill`
- `selecting_tool`
- `waiting_approval`
- `running_tool`
- `completed`
- `failed`
- `cancelled`

**Codex must not do:**
- Use generic `running` as task status.
- Run tools yet.
- Call external model provider unless explicitly asked.
- Execute risky actions.

**Done when:**
- Owner can send chat to an agent.
- Backend creates task and task steps.
- Task has `request_id`.
- API can retrieve task detail.
- Canonical task lifecycle is used.
- No risky action is executed.

## Step 12 - Approval System

**Goal:** Implement approval request flow for high-risk and critical actions.

**Codex may do:**
- Create `approval_requests` model.
- Create schemas, repository, service, and routes.
- Implement routes to list pending approvals, get approval detail, approve request, and reject request.
- Allow task or tool execution services to check approval status later.

**Approval request fields must include:**
- `agent_id`
- `task_id`
- `tool_id` nullable
- `requested_action`
- `risk_level`
- `status`
- `request_payload`
- `decision_reason`

**Codex must not do:**
- Auto-execute rejected actions.
- Unblock critical actions by default.
- Skip audit-friendly decision recording.

**Done when:**
- High-risk tool request creates pending approval.
- Owner can approve or reject.
- Rejected approval does not execute anything.
- Approved status can be checked by task or tool execution service.

## Step 13 - Activity Logs, Audit Logs, Tool Calls, and Model Usage Logs

**Goal:** Implement logging and debugging foundation.

**Codex may do:**
- Create `activity_logs` model.
- Create `audit_logs` model.
- Create `tool_calls` model.
- Create `model_usage_logs` model.
- Add logging services.
- Add filters by `request_id`, `agent_id`, `event_type`, `status`, and date.
- Mask secrets in logs.

**Codex must not do:**
- Store plaintext secrets.
- Log raw credentials, webhook secrets, or tokens.
- Skip linking logs with `request_id` where applicable.

**Done when:**
- Important CRUD and task actions create logs.
- Logs can be listed and filtered.
- `request_id` can connect task, steps, tool calls, and activity logs.

## Step 14 - Model Router Stub and Provider Usage Logging

**Goal:** Create a safe model router stub and provider adapter structure without making real external model calls.

**Codex may do:**
- Create `integrations/model_router.py`.
- Add adapter interface and safe stubs for:
  - API provider adapter
  - OpenClaw adapter
  - local adapter
- Route model requests only to stub adapters.
- Record `model_usage_logs` for stub usage.
- Optionally add a protected stub test route such as `POST /model-router/stub-test`.

**Codex must not do:**
- Call OpenAI, Gemini, OpenRouter, Ollama, OpenClaw, or any external model provider.
- Expose `secret_reference`.
- Use real API keys or OAuth tokens.
- Bypass approval or permission rules.

**Done when:**
- Backend can choose adapter by `provider_type`.
- Response clearly says this is a stub.
- `model_usage_logs` can record stub activity.
- No external provider call happens.

## Step 15 - Tool Permission and Execution Guard Stub

**Goal:** Implement a safe permission guard for tool requests without executing any real tool.

**Codex may do:**
- Add `tool_execution_service`.
- Add protected route `POST /tools/execution-stub`.
- Validate:
  - owner owns the agent and task
  - task-agent match
  - tool exists
  - agent-tool assignment exists
  - `permission_mode` is respected
  - inactive or disabled tools are blocked
  - GitHub imported tool execution is blocked
  - critical tool execution is blocked in MVP
- Create `approval_requests` and `tool_calls` records when needed.
- Return safe stub responses only.

**Codex must not do:**
- Execute n8n workflows.
- Execute GitHub imported tools.
- Run shell or terminal commands.
- Call model providers.
- Write to external systems.

**Done when:**
- Default deny works when no assignment exists.
- Block rules work.
- High-risk requests create approval records safely.
- Low-risk allowed requests still return stub-only result.
- Database `tool_calls.status` stays canonical: `success`, `failed`, `waiting_approval`.

## Step 16 - n8n Workflow Registry Stub

**Goal:** Add an n8n workflow registry for safe metadata only.

**Codex may do:**
- Create `n8n_workflows` model, schema, repository, service, and routes.
- Store safe config metadata:
  - name
  - slug
  - workflow external id
  - trigger type
  - webhook URL reference label
  - risk level
  - approval requirement
  - metadata JSON
- Enforce high and critical approval defaults.
- Keep critical workflows disabled for MVP.
- Reject obvious secret-like webhook values.

**Codex must not do:**
- Execute workflows.
- Call n8n API.
- Call webhook URLs.
- Store raw webhook secret URLs.

**Done when:**
- Owner can create, list, update, and soft-delete workflow registry records.
- Registry stays config-only.
- n8n execution remains disabled.

## Step 17 - Agent Runtime Orchestrator Stub

**Goal:** Improve chat task flow with a safe internal orchestrator stub.

**Codex may do:**
- Add `agent_runtime_service.py`.
- Update `POST /agents/{agent_id}/chat` to use runtime orchestration stub.
- Load safe context summaries for:
  - memories
  - assigned skills
  - assigned tools
- Call the model router stub only when agent has a default provider.
- Record task steps:
  - `received`
  - `loading_memory`
  - `selecting_skill`
  - `selecting_tool`
  - `model_router_stub`
  - `completed`
- Save a structured safe final response explaining that no real execution happened.

**Codex must not do:**
- Execute skills.
- Execute tools.
- Execute n8n workflows.
- Execute GitHub imported tools.
- Call Hermes.
- Call OpenClaw.
- Call external model providers.

**Done when:**
- Chat creates exactly one task.
- Task steps use canonical task-step statuses only.
- Memory, skill, and tool context are treated as references only.
- Final response is safe and structured.

## Step 18 - Backend Smoke Test Foundation

**Goal:** Add a minimal backend smoke test setup without adding product features.

**Codex may do:**
- Add `pytest` to backend requirements if missing.
- Create lightweight backend tests such as:
  - `test_health.py`
  - `test_route_registration.py`
  - `test_safety_boundaries.py`
- Verify:
  - `/health` works
  - OpenAPI schema loads
  - important route groups are registered
  - dangerous direct execution routes are not registered
- Keep tests isolated from real PostgreSQL mutations when possible.

**Codex must not do:**
- Add heavy test frameworks unnecessarily.
- Run real tool execution.
- Run n8n, GitHub imported tools, Hermes, OpenClaw, or external model calls in tests.
- Mutate production or real local data.

**Done when:**
- Smoke test structure exists.
- Health and route registration tests exist.
- Safety boundary tests exist.
- Tests remain lightweight and safe.

## Step 19 - Backend Final Audit / Pre-Frontend Checkpoint

**Goal:** Perform a final backend checkpoint audit before starting frontend work.

**Codex may do:**
- Audit backend implementation from Step 1 through Step 18.
- Check architecture, auth protection, owner scoping, migrations, enum consistency, route registry, secret masking, and safety boundaries.
- Run validation such as:
  - `python -m compileall app`
  - `python -m pytest`
- Apply only tiny safe fixes if clearly necessary and approved by the step prompt.

**Codex must not do:**
- Start frontend work.
- Add new backend features.
- Create migrations.
- Refactor broadly.

**Done when:**
- Backend checkpoint is reported clearly.
- Remaining risks are documented.
- Safe next action is identified before frontend begins.

## Step 20 - Frontend Foundation

**Goal:** Start the frontend only after backend checkpoint is clean.

**Codex may do:**
- Work inside `apps/web`.
- Create Next.js frontend using JavaScript only.
- Add base layout, login page, API client helper, and protected dashboard shell.

**Codex must not do:**
- Use TypeScript.
- Assume backend unsafe stubs are real execution.
- Expose secrets in frontend.

**Done when:**
- Frontend foundation exists in JavaScript.
- Backend APIs remain the system of record.
- Frontend starts only after backend checkpoint is clean.

## Final Safety Reminder

Do not ask Codex to complete the whole project in one prompt. This project includes agents, tools, memory, approval, GitHub import, OpenClaw, Hermes, n8n, logs, deployment, and security boundaries. Building everything at once increases the risk of unnecessary refactors, unsafe defaults, TypeScript files, secret leaks, and broken architecture.

Recommended order:

1. Finish repository structure.
2. Finish backend foundation.
3. Finish database setup.
4. Finish auth.
5. Finish database-backed CRUD modules.
6. Finish logs and approval.
7. Add model router stub, tool execution guard stub, and n8n registry carefully.
8. Stabilize runtime orchestration stubs and smoke tests.
9. Run backend final audit checkpoint.
10. Build frontend only after backend APIs and safety boundaries are clean.
