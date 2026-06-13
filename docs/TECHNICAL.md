# Technical Design v2.1 — Personal AI Agent Workspace

## Document Info

| Field | Value |
| --- | --- |
| Project | Personal AI Agent Workspace |
| Version | v2.1 — Consistency Fixed |
| Scope | Private single-user MVP first |
| Language Rule | Frontend: JavaScript only. Backend: Python only. |
| Status | Implementation-ready planning document |

## 1. Technical Purpose

This document defines the technical architecture for Personal AI Agent Workspace. It applies the language rule: frontend in JavaScript only and backend in Python only.

## 2. Technology Boundaries

| Boundary | Decision |
| --- | --- |
| Frontend language | JavaScript only. No TypeScript for MVP. |
| Backend language | Python only. |
| Frontend framework | Next.js with JavaScript. |
| Backend framework | FastAPI. |
| Database | PostgreSQL / Neon. |
| Automation | n8n as supporting workflow executor. |
| Agent runtime | Hermes as supporting runtime. |
| Model gateway | OpenClaw Gateway as private service. |
| Other languages | Not allowed for core logic unless explicitly approved. |

## 3. High-Level Architecture

```txt
Browser / Telegram
↓
Next.js Frontend (JavaScript)
↓ REST API
FastAPI Backend (Python)
↓
Agent Manager Service
↓
Hermes Runtime Adapter
↓
Model Router
├─ API Provider Adapter
└─ OpenClaw Gateway Adapter
↓
Memory Service + Skill Service + Tool Service
↓
Tool Executors
├─ n8n Webhook Executor
├─ GitHub API Executor (read/preview first)
├─ Database Executor
└─ Messaging Executor
↓
PostgreSQL / Neon Logs + State
```

## 4. Repository Structure

```txt
personal-ai-agent-workspace/
├─ apps/
│  ├─ web/                 # Next.js frontend, JavaScript only
│  │  ├─ app/
│  │  ├─ components/
│  │  ├─ lib/
│  │  └─ package.json
│  │
│  └─ api/                 # FastAPI backend, Python only
│     ├─ app/
│     │  ├─ main.py
│     │  ├─ core/
│     │  ├─ models/
│     │  ├─ schemas/
│     │  ├─ repositories/
│     │  ├─ services/
│     │  ├─ routes/
│     │  └─ integrations/
│     ├─ alembic/
│     └─ pyproject.toml
│
├─ docs/
│  ├─ PRD.md
│  ├─ TECHNICAL.md
│  ├─ DATABASE.md
│  └─ SECURITY.md
│
├─ n8n/
│  └─ workflows/
├─ AGENTS.md
└─ docker-compose.yml
```

## 5. Frontend Architecture

Frontend is built with Next.js using JavaScript. TypeScript is not used for MVP. The frontend should remain simple, responsive, and easy to debug.

| Frontend Area | Responsibility |
| --- | --- |
| Dashboard | Display agent status, task status, approvals, provider health, and latest errors. |
| Agent Pages | Create, edit, and view agent configuration. |
| Skill Registry | Manage manual and GitHub-imported skills. |
| Tool Registry | Manage tool definitions and allowed/blocked agents. |
| Model Providers | Configure API providers and OpenClaw Gateway provider. |
| Chat | Send prompts to selected agent and display task lifecycle. |
| Activity Monitor | Display logs, task steps, provider usage, and errors. |
| Approval Center | Approve or reject sensitive actions. |
| Memory Pages | Manage scoped memory by type and agent. |

## 6. Backend Architecture

Backend uses FastAPI and Python. It follows route-service-repository structure for maintainability.

```txt
route → schema validation → service → repository → database
route → service → integration adapter → external service
```

| Backend Module | Responsibility |
| --- | --- |
| auth | Admin login, token/session handling, current user. |
| agents | Agent CRUD and configuration. |
| skills | Skill CRUD, GitHub skill import, registry. |
| tools | Tool config, allowed/blocked agents, risk level, approval rules. |
| n8n_workflows | n8n workflow registry metadata only; config records without execution. |
| memory | Memory CRUD and access scope. |
| tasks | Task creation, step tracking, status management. |
| approvals | Approval requests and decisions. |
| model_providers | API provider and OpenClaw provider configuration. |
| integrations | Hermes, OpenClaw, n8n, GitHub adapters. |
| logs | Activity logs, audit logs, provider usage logs. |

## 7. Canonical Task Lifecycle

The canonical task statuses are:

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

Do not use a separate generic `running` task status in MVP. Use `running_tool` when the task is executing an approved tool.

## 8. Agent Execution Flow

1. User sends message from web chat.
2. Backend creates task with status `received` and a unique `request_id`.
3. Agent Manager loads agent config.
4. Task status changes to `loading_memory`.
5. Memory Service loads allowed memory scopes.
6. Task status changes to `selecting_skill`.
7. Skill Service loads assigned enabled skills.
8. Task status changes to `thinking`.
9. Model Router selects provider.
10. Hermes Runtime processes instruction, memory, skills, and prompt.
11. Task status changes to `selecting_tool` if a tool is requested.
12. Tool Service checks agent permission, block rules, risk level, and approval requirement.
13. If approval is required, create approval request and set task status to `waiting_approval`.
14. If approved, set task status to `running_tool` and run executor.
15. Save tool call, task steps, logs, and final output.
16. Set task status to `completed`, `failed`, or `cancelled`.
17. Frontend displays result and trace.

## 9. Tool Permission Model

Tool permissions are explicit.

- No assignment means the agent cannot use the tool.
- `permission_mode = allow` means the agent may request the tool.
- `permission_mode = block` means the agent must never use the tool.
- Block wins over allow.
- High and critical tools require approval even if allowed.
- Critical tools are disabled by default.
- Imported GitHub tool execution is disabled for MVP.

## 10. Model Router Design

| Provider Type | Adapter | Use Case |
| --- | --- | --- |
| api | OpenAI/Gemini/OpenRouter adapter | Stable production API access and fallback. |
| subscription_oauth | OpenClaw Gateway adapter | Private owner subscription/OAuth model access. |
| local | Ollama adapter later | Optional future local inference. |

Rules:

- The Model Router must not expose API keys or OAuth tokens to the frontend.
- All provider calls are made from the backend.
- Every model call writes a model usage log.
- Provider fallback must not bypass approval or permission rules.

## 11. OpenClaw Gateway Integration

OpenClaw Gateway is configured as a private provider endpoint.

Rules:

- Only backend can call OpenClaw Gateway.
- Gateway is not exposed directly to public users.
- Provider health check is available from Model Provider Settings.
- All OpenClaw requests are logged as provider usage logs.
- Fallback API provider should be configured when OpenClaw is unavailable.

## 12. Hermes Runtime Integration

Hermes is integrated through a backend adapter. The backend prepares agent instruction, allowed memory, assigned skills, and model provider configuration before calling Hermes.

```txt
Agent Config + Memory + Skills + User Input
↓
Hermes Adapter
↓
Model Router
↓
Agent Decision
↓
Tool Permission Check
↓
Tool Execution / Approval
```

## 13. n8n Integration

n8n is used as workflow executor, not as the main application backend. The backend calls n8n webhooks through controlled tools.

For the current MVP registry step, `n8n_workflows` is config-only. It stores safe workflow references and approval metadata, but it does not execute workflows, call webhook URLs, or call the n8n API yet.

| n8n Tool | Purpose | Approval |
| --- | --- | --- |
| run_n8n_workflow | Execute registered n8n webhook. | Depends on risk level. |
| send_telegram_message | Send Telegram message through n8n workflow. | Required. |
| generate_daily_report | Run report automation. | Optional, depending on configuration. |

## 14. GitHub Skill and Tool Import Design

### 14.1 GitHub Skill Import

```txt
GitHub URL
↓
Importer Service
↓
Fetch repo metadata/files
↓
Detect SKILL.md files
↓
Preview content
↓
User approval
↓
Save skill to registry
↓
Assign to agent
```

MVP imports skill text only.

### 14.2 GitHub Tool Preview

GitHub tool import is preview/registry only for MVP.

- Imported tool code must not execute.
- Imported tool records are disabled by default.
- Execution of imported tool code is critical and outside MVP.
- Execution requires future sandboxing, allowlist, explicit enablement, approval, and logging.

## 15. Memory Design

Canonical memory types:

```txt
profile
contact
project
agent_instruction
task_history
skill
sensitive_config_reference
```

Rules:

- Agents can only access memory categories assigned to them.
- Contact memory must not be exposed to unrelated agents.
- `sensitive_config_reference` stores references only, not plaintext secrets.
- Memory reads and writes must be logged.

## 16. Approval System Design

| Risk Level | Default Behavior |
| --- | --- |
| low | Can execute automatically if tool is allowed. |
| medium | Depends on agent configuration. |
| high | Approval required. |
| critical | Blocked by default or approval plus explicit allowlist required. |

Approval requests must show:

- Agent name.
- Requested action.
- Selected skill.
- Tool name.
- Tool input preview.
- Risk level.
- Reason.
- Approve/reject buttons.

## 17. Logging and Debugging

Every request has `request_id`.
Every task has steps.
Every tool call stores input/output summary and status.
Every provider call stores provider name, model, latency, token estimate, and status.
Errors are saved with safe error messages and internal stack traces.
Frontend debug page can filter logs by agent, task, tool, provider, status, and date.

Do not log plaintext secrets.

## 18. Security Design

- Admin login required for workspace.
- Secrets are stored in environment variables or encrypted storage, not plaintext UI.
- OpenClaw Gateway must remain private.
- Tool allow/block rules per agent.
- Memory access scope per agent.
- Approval before sensitive actions.
- Rate limit auth and agent execution endpoints.
- No unrestricted shell execution.
- Imported GitHub tools are disabled by default.

## 19. Deployment Design

| Component | Deployment Target |
| --- | --- |
| Next.js frontend | Vercel |
| FastAPI backend | Google Cloud Run |
| Database | Neon PostgreSQL |
| n8n | Private VPS/local/private hosted service |
| OpenClaw Gateway | Private VPS/local/private service |
| Hermes runtime | Backend-integrated service or private runtime service |

## 20. MVP Implementation Order

1. Create backend foundation with FastAPI and Python.
2. Create database migrations.
3. Create admin auth.
4. Create agent, skill, tool, provider CRUD.
5. Create GitHub skill import preview.
6. Create GitHub tool preview only, with execution disabled.
7. Create frontend with Next.js JavaScript.
8. Create chat and activity monitor.
9. Create approval center.
10. Integrate n8n webhook tool.
11. Integrate model providers and OpenClaw provider config.
12. Integrate Hermes runtime adapter.
