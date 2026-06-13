# PRD v2.1 — Personal AI Agent Workspace

## Document Info

| Field | Value |
| --- | --- |
| Project | Personal AI Agent Workspace |
| Version | v2.1 — Consistency Fixed |
| Scope | Private single-user MVP first |
| Language Rule | Frontend: JavaScript only. Backend: Python only. |
| Status | Implementation-ready planning document |

## 1. Product Overview

Personal AI Agent Workspace is a private application for creating, managing, running, monitoring, and limiting multiple AI agents from one workspace. The system is designed for a single owner first, with clear security, approvals, logs, and agent boundaries.

The implementation direction is intentionally simplified for stability:

- Frontend uses Next.js with JavaScript.
- Backend uses FastAPI with Python.
- TypeScript is not used for MVP.
- The workspace is private and single-user during MVP.

## 2. Problem Statement

AI agents become risky when they can call tools, read memory, access GitHub, trigger n8n workflows, use model gateways, update databases, send messages, or execute commands without clear monitoring and approval.

The owner needs a controlled workspace where each agent has:

- A clear role.
- A system instruction.
- Assigned skills.
- Allowed and blocked tools.
- Memory scope.
- Model provider configuration.
- Approval rules.
- Execution logs and debugging trace.

## 3. Product Goals

1. Create a private workspace for managing multiple AI agents.
2. Allow each agent to have its own name, role, instruction, memory access, skills, tools, and model provider.
3. Support model providers through API-based access and private subscription/OAuth access through OpenClaw Gateway.
4. Support GitHub skill import with review and versioning.
5. Keep GitHub imported tool execution disabled for MVP until sandboxing and safety rules are mature.
6. Provide monitoring, execution traces, approval center, and activity logs.
7. Keep the system responsive, scalable, maintainable, easy to debug, and secure.
8. Limit core application languages to JavaScript for frontend and Python for backend.

## 4. Non-Goals for MVP

- No public SaaS or multi-tenant marketplace.
- No TypeScript implementation for MVP.
- No unrestricted terminal command execution.
- No automatic production deployment without approval.
- No payment or transaction automation.
- No model training from scratch.
- No automatic execution of imported GitHub tools.
- No complex real-time video or voice pipeline in MVP.

## 5. Target User

The initial target user is the workspace owner only. The system is private, personal, and technical-user oriented.

Typical usage:

- Developer who wants a personal AI agent system.
- Owner who wants to control agent permissions and activity.
- User who wants to connect agents with n8n, GitHub, Telegram, and custom tools safely.

## 6. Core Architecture Concept

```txt
Custom Web App / Telegram
↓
Workspace Backend (FastAPI / Python)
↓
Agent Manager
↓
Hermes Agent Runtime
↓
Model Router
├─ API Providers: OpenAI API, Gemini API, OpenRouter
└─ Subscription/OAuth Provider: OpenClaw Gateway + ChatGPT/Codex OAuth
↓
Memory + Skills + Tools
↓
FastAPI Tools / n8n / GitHub / External APIs
↓
Approval + Logs + Monitoring
```

## 7. Core Language Rule

| Area | Language | Decision |
| --- | --- | --- |
| Frontend workspace | JavaScript | Required for MVP |
| Backend API and agent services | Python | Required for MVP |
| Styling | CSS / Tailwind output | Allowed as supporting files only |
| Scripts / config | Shell, PowerShell, YAML, Dockerfile | Allowed only when necessary |
| TypeScript | Not used | Avoid for MVP to keep stack simple |
| Other languages | Go, Rust, Java, PHP, Ruby, C#, etc. | Not allowed unless explicitly approved |

## 8. Model Provider Strategy

### 8.1 API Providers

API providers use API keys and are suitable for stable backend deployment. They can be used as primary or fallback providers.

MVP provider targets:

- OpenAI API.
- Gemini API.
- OpenRouter.
- Local/Ollama later only if explicitly approved and resources are available.

### 8.2 Subscription/OAuth Provider

Subscription/OAuth providers use a private OpenClaw Gateway connected to the owner's ChatGPT/Codex OAuth subscription.

Rules:

- This path is only for private personal use.
- OpenClaw Gateway must not be exposed as a public API.
- OpenClaw Gateway must be private and protected.
- Subscription/OAuth provider is not the same as official OpenAI API billing.
- Provider follows subscription limits.
- Fallback API provider should be available if the gateway fails.

## 9. Core Modules

| Module | Purpose |
| --- | --- |
| Dashboard | Shows total agents, active agents, running tasks, failed tasks, pending approvals, recent activity, model provider status, and n8n status. |
| Agent Management | Create and manage agents with role, instruction, model provider, skills, tools, memory scope, approval rules, max steps, max runtime, and status. |
| Instruction Management | Edit system instruction and behavior rules for each agent. |
| Skill Management | Create, edit, import, version, and assign skills to agents. |
| Tool Management | Register tools, set schemas, risk levels, approvals, timeouts, and allowed or blocked agents. |
| GitHub Skill Import | Import SKILL.md from GitHub repositories after preview and user approval. |
| GitHub Tool Preview | Preview imported GitHub tools only. Execution is disabled for MVP. |
| Skill/Tool Registry | Central registry for manual skills, GitHub skills, tool definitions, n8n tools, and FastAPI tools. |
| Memory Management | Store, edit, delete, and scope memory by agent. |
| Chat Interface | Interact with selected agent and view task status, selected skill, selected tool, approval request, and final result. |
| Activity Monitor | Track agent actions, provider usage, skill usage, tool calls, token/cost estimates, duration, and errors. |
| Approval Center | Approve or reject sensitive actions before execution. |
| Model Provider Settings | Configure API provider and private OpenClaw Gateway provider. |

## 10. Agent Boundaries and Approval Rules

Agents may think, select skills, and prepare actions, but they cannot run sensitive actions without permission, approval, and logging.

| Action | Default Rule |
| --- | --- |
| Summarize, translate, draft text | Can run automatically if allowed. |
| Read non-sensitive memory | Allowed according to memory scope. |
| Send message or email | Approval required. |
| Write/update database | Approval required for important data. |
| Create GitHub PR or push code | Approval required. |
| Deploy to VPS or cloud | Approval required. |
| Run terminal command | Blocked by default; allowlist and approval required if added later. |
| Execute imported GitHub tool | Disabled for MVP. |

## 11. Tool Permission Model

MVP uses explicit tool permissions.

- A tool is not available to an agent unless explicitly assigned.
- `allow` permission means the agent may request the tool.
- `block` permission means the tool is explicitly forbidden for that agent.
- If both allowed and blocked rules could apply, block wins.
- High and critical tools still require approval even when allowed.
- Critical tools are disabled by default.

## 12. Memory Categories

The canonical memory types for MVP are:

- `profile`
- `contact`
- `project`
- `agent_instruction`
- `task_history`
- `skill`
- `sensitive_config_reference`

Important rule: `sensitive_config_reference` stores only references or labels to external secret storage. It must not store plaintext API keys, OAuth tokens, passwords, database URLs, webhook secrets, or credentials.

## 13. GitHub Import Risk Rule

GitHub skill import is allowed for MVP as text instruction import.

GitHub tool import is handled differently:

- Previewing or registering an imported GitHub tool is treated as a high-risk review activity.
- Executing an imported GitHub tool is a critical action.
- Imported GitHub tool execution is disabled for MVP.
- Execution can only be considered later after sandboxing, allowlist, explicit enablement, approval, and logging are implemented.

## 14. MVP Scope

MVP includes:

1. Admin login.
2. Dashboard.
3. Agent CRUD.
4. Skill CRUD.
5. Tool config CRUD.
6. Skill/tool registry.
7. GitHub skill import with preview.
8. GitHub tool preview only, execution disabled.
9. Model provider config for API and OpenClaw Gateway.
10. Chat with agent.
11. Activity logs and task steps.
12. Approval center.
13. n8n webhook integration.
14. Responsive JavaScript frontend.
15. Python FastAPI backend.

## 15. User Flows

### 15.1 Create Agent

1. Open workspace.
2. Click Create Agent.
3. Input name, role, and instruction.
4. Choose model provider.
5. Assign skills.
6. Set allowed and blocked tools.
7. Set memory scope.
8. Set approval rules and limits.
9. Save agent.

### 15.2 Import Skill from GitHub

1. Open GitHub Import page.
2. Input repository URL or file URL.
3. Workspace scans or fetches SKILL.md.
4. Preview skill content.
5. Approve import.
6. Save to registry.
7. Assign to selected agent.

### 15.3 Run Agent

1. Choose agent.
2. Send prompt.
3. Backend creates task and request_id.
4. Agent loads instruction, memory, skills, and provider.
5. Agent selects skill and optional tool.
6. Tool permission is checked.
7. If action is sensitive, create approval request and pause task.
8. Execute only after approval.
9. Save logs and show result.

## 16. Non-Functional Requirements

| Requirement | Rule |
| --- | --- |
| Responsive | Must work well on desktop, tablet, and mobile. |
| Scalable | Modules must be separated: agents, skills, tools, memory, providers, logs, approvals. |
| Maintainable | Use clean architecture. No large logic in route/controller. |
| Easy Debugging | Every task has request_id, steps, tool calls, provider logs, and error trace. |
| Secure | Auth, permission, approval, secret masking, rate limits, audit logs, and private OpenClaw gateway. |
| Stack Stability | Core frontend in JavaScript and backend in Python only. |

## 17. Suggested Stack

| Layer | Technology | Notes |
| --- | --- | --- |
| Frontend | Next.js + JavaScript + Tailwind CSS | No TypeScript for MVP. |
| Backend | FastAPI + Python | Main API and service layer. |
| Database | PostgreSQL / Neon | Hosted relational database. |
| ORM/Migration | SQLAlchemy + Alembic | Python backend. |
| Agent Runtime | Hermes | Agent runtime and skill/memory execution. |
| Model Gateway | OpenClaw Gateway | Private subscription/OAuth provider. |
| Automation | n8n | Workflow executor. |
| Deployment | Vercel + Google Cloud Run + Neon | Frontend/backend/database deployment. |

## 18. Success Criteria

1. User can create at least three agents.
2. User can create and assign skills.
3. User can import skill from GitHub after preview.
4. User can configure API model provider and OpenClaw private provider.
5. User can chat with agent.
6. Agent can select skill and call at least one n8n workflow.
7. Sensitive action requires approval.
8. All activity is logged and debuggable.
9. Frontend is responsive and written in JavaScript.
10. Backend is written in Python.
11. Imported GitHub tool execution remains disabled for MVP.
