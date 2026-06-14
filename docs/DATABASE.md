# Database Schema v2.1 — Personal AI Agent Workspace

## Document Info

| Field | Value |
| --- | --- |
| Project | Personal AI Agent Workspace |
| Version | v2.1 — Consistency Fixed |
| Scope | Private single-user MVP first |
| Language Rule | Frontend: JavaScript only. Backend: Python only. |
| Status | Implementation-ready planning document |

## 1. Database Purpose

This document defines the database schema for Personal AI Agent Workspace. The database supports agent configuration, skills, tools, GitHub imports, model providers, n8n workflow registry, memory, tasks, approvals, logs, and audit trails.

## 2. Database Technology

| Area | Decision |
| --- | --- |
| Primary database | PostgreSQL / Neon |
| Backend ORM | SQLAlchemy |
| Migrations | Alembic |
| Primary key style | UUID |
| Timestamps | `created_at`, `updated_at` |
| Soft delete | `deleted_at` for important entities |
| Semantic memory later | pgvector optional later |

## 3. Core Entity Groups

There are no separate `skill_sources` or `tool_sources` tables in MVP. Source tracking is handled through `github_imports`, `skills.source_type`, `skills.source_id`, `tools.source_type`, and `tools.source_id`.

| Group | Entities |
| --- | --- |
| Identity | `users` |
| Agent Config | `agents`, `agent_instructions` |
| Skills | `skills`, `agent_skills`, `github_imports` |
| Tools | `tools`, `agent_tools`, `github_imports`, `n8n_workflows` |
| Providers | `model_providers`, `model_usage_logs` |
| Memory | `memories` |
| Execution | `tasks`, `task_steps`, `tool_calls` |
| Control | `approval_requests` |
| Logs | `activity_logs`, `audit_logs` |

## 4. Entity Relationship Overview

```txt
users
  └─ agents
       ├─ agent_instructions
       ├─ agent_skills ── skills ── github_imports
       ├─ agent_tools ── tools ── github_imports
       ├─ memories
       └─ tasks
            ├─ task_steps
            ├─ tool_calls
            └─ approval_requests

model_providers
  ├─ agents.default_model_provider_id
  └─ model_usage_logs

activity_logs and audit_logs track important events.
```

## 5. Canonical Status Values

| Entity | Allowed Status Values |
| --- | --- |
| `agents` | `active`, `inactive` |
| `skills` | `active`, `inactive`, `disabled` |
| `tools` | `active`, `inactive`, `disabled` |
| `github_imports` | `preview`, `imported`, `rejected`, `disabled` |
| `tasks` | `received`, `thinking`, `loading_memory`, `selecting_skill`, `selecting_tool`, `waiting_approval`, `running_tool`, `completed`, `failed`, `cancelled` |
| `task_steps` | `success`, `failed`, `running`, `skipped` |
| `tool_calls` | `success`, `failed`, `waiting_approval` |
| `approval_requests` | `pending`, `approved`, `rejected`, `expired` |
| `model_usage_logs` | `success`, `failed` |

Do not use generic task status `running` in MVP. Use `running_tool` for approved tool execution.

## 6. Canonical Memory Types

| Memory Type | Purpose |
| --- | --- |
| `profile` | Owner profile or preference memory. |
| `contact` | Contact-related memory. |
| `project` | Project-specific memory. |
| `agent_instruction` | Memory related to agent behavior/instruction history. |
| `task_history` | Reusable task history or execution summary. |
| `skill` | Skill-related memory. |
| `sensitive_config_reference` | Reference to secret/config storage only. No plaintext secret. |

## 7. Tables

### users

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `email` | varchar(255) | unique, required |
| `password_hash` | text | required |
| `display_name` | varchar(120) | required |
| `role` | varchar(50) | default `owner` |
| `is_active` | boolean | default `true` |
| `created_at` | timestamp | required |
| `updated_at` | timestamp | required |
| `deleted_at` | timestamp | nullable |

### model_providers

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `name` | varchar(120) | required |
| `provider_type` | varchar(40) | `api`, `subscription_oauth`, `local` |
| `base_url` | text | nullable |
| `auth_type` | varchar(40) | `api_key`, `oauth_gateway`, `none` |
| `secret_reference` | text | nullable; never raw secret |
| `default_model` | varchar(120) | nullable |
| `fallback_provider_id` | uuid | FK `model_providers.id` nullable |
| `status` | varchar(30) | `active`, `inactive` |
| `is_private` | boolean | default `true` |
| `created_at` | timestamp | required |
| `updated_at` | timestamp | required |

### agents

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `owner_id` | uuid | FK `users.id` |
| `name` | varchar(120) | required |
| `slug` | varchar(120) | unique |
| `description` | text | nullable |
| `role_description` | text | required |
| `default_model_provider_id` | uuid | FK `model_providers.id` nullable |
| `default_model_name` | varchar(120) | nullable |
| `status` | varchar(30) | `active`, `inactive` |
| `max_steps` | integer | default `10` |
| `max_runtime_seconds` | integer | default `300` |
| `max_token_budget` | integer | nullable |
| `requires_approval_by_default` | boolean | default `false` |
| `created_at` | timestamp | required |
| `updated_at` | timestamp | required |
| `deleted_at` | timestamp | nullable |

### agent_instructions

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `agent_id` | uuid | FK `agents.id` |
| `instruction_text` | text | required |
| `version` | integer | default `1` |
| `is_active` | boolean | default `true` |
| `created_at` | timestamp | required |
| `updated_at` | timestamp | required |

Only one active instruction should exist per agent.

### skills

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `name` | varchar(150) | required |
| `slug` | varchar(150) | unique |
| `description` | text | nullable |
| `content` | text | required |
| `source_type` | varchar(30) | `manual`, `github`, `template` |
| `source_id` | uuid | nullable; usually FK-like reference to `github_imports.id` when source_type is `github` |
| `version_label` | varchar(80) | nullable |
| `risk_level` | varchar(30) | `low`, `medium`, `high` |
| `status` | varchar(30) | `active`, `inactive`, `disabled` |
| `created_at` | timestamp | required |
| `updated_at` | timestamp | required |
| `deleted_at` | timestamp | nullable |

### agent_skills

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `agent_id` | uuid | FK `agents.id` |
| `skill_id` | uuid | FK `skills.id` |
| `is_enabled` | boolean | default `true` |
| `created_at` | timestamp | required |

### tools

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `name` | varchar(150) | required |
| `slug` | varchar(150) | unique |
| `description` | text | nullable |
| `tool_type` | varchar(50) | `n8n`, `github`, `database`, `messaging`, `custom` |
| `source_type` | varchar(30) | `manual`, `github`, `n8n`, `internal`, `custom` |
| `source_id` | uuid | nullable; usually FK-like reference to `github_imports.id` when source_type is `github` |
| `input_schema` | jsonb | nullable |
| `output_schema` | jsonb | nullable |
| `risk_level` | varchar(30) | `low`, `medium`, `high`, `critical` |
| `approval_required` | boolean | default `false` |
| `timeout_seconds` | integer | default `60` |
| `rate_limit_per_hour` | integer | nullable |
| `status` | varchar(30) | `active`, `inactive`, `disabled` |
| `created_at` | timestamp | required |
| `updated_at` | timestamp | required |
| `deleted_at` | timestamp | nullable |

Rules:

- Critical tools should be created with `status = disabled` by default.
- A GitHub imported executable tool should be considered `critical` if it is ever converted into an executable tool record.
- During MVP, imported GitHub tools remain preview/registry only and must not execute.

### agent_tools

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `agent_id` | uuid | FK `agents.id` |
| `tool_id` | uuid | FK `tools.id` |
| `permission_mode` | varchar(30) | `allow` or `block` |
| `is_enabled` | boolean | default `true` |
| `override_approval_required` | boolean | nullable |
| `created_at` | timestamp | required |

Rules:

- No row means the tool is not available to the agent.
- `permission_mode = allow` means the agent may request the tool.
- `permission_mode = block` means the tool is explicitly blocked for the agent.
- Block wins over allow.
- High and critical tools still require approval even if allowed.

### github_imports

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `repo_url` | text | required |
| `branch` | varchar(120) | nullable |
| `commit_sha` | varchar(120) | nullable |
| `import_type` | varchar(30) | `skill`, `tool` |
| `file_path` | text | required |
| `content_preview` | text | nullable |
| `status` | varchar(30) | `preview`, `imported`, `rejected`, `disabled` |
| `review_notes` | text | nullable |
| `created_at` | timestamp | required |
| `updated_at` | timestamp | required |

Rules:

- For `import_type = skill`, approved imports may create a `skills` record.
- The current approve-skill flow saves reviewed skill content into `skills`; that is registry write behavior, not execution.
- For `import_type = tool`, MVP only allows preview/registry tracking. Execution is disabled.
- Previewing or registering an imported GitHub tool is high risk.
- Executing an imported GitHub tool is critical and outside MVP.

### n8n_workflows

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `owner_id` | uuid | FK `users.id` |
| `name` | varchar(160) | required |
| `slug` | varchar(180) | unique, required |
| `description` | text | nullable |
| `workflow_external_id` | varchar(180) | nullable |
| `trigger_type` | varchar(50) | `webhook`, `manual`, `scheduled` |
| `webhook_url_reference` | text | nullable |
| `status` | varchar(30) | `active`, `inactive`, `disabled` |
| `risk_level` | varchar(30) | `low`, `medium`, `high`, `critical` |
| `approval_required` | boolean | default `true` |
| `metadata` | jsonb | nullable |
| `created_at` | timestamp | required |
| `updated_at` | timestamp | required |
| `deleted_at` | timestamp | nullable |

Rules:

- SQLAlchemy model should use `metadata_json` mapped to database column `metadata` because `metadata` is reserved in SQLAlchemy Declarative models.
- High and critical workflows require approval.
- Critical workflows remain `disabled` for MVP.
- `webhook_url_reference` must store a safe reference label or placeholder, not a raw secret URL.
- n8n workflow execution is not implemented yet in this table.
- n8n API calls and webhook execution remain disabled in MVP for this registry step.

### memories

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `owner_id` | uuid | FK `users.id` |
| `agent_id` | uuid | FK `agents.id` nullable |
| `memory_type` | varchar(50) | `profile`, `contact`, `project`, `agent_instruction`, `task_history`, `skill`, `sensitive_config_reference` |
| `title` | varchar(200) | required |
| `content` | text | required |
| `visibility_scope` | varchar(50) | `global`, `agent`, `private` |
| `metadata` | jsonb | nullable |
| `created_at` | timestamp | required |
| `updated_at` | timestamp | required |
| `deleted_at` | timestamp | nullable |

Rules:

- `sensitive_config_reference` stores only references or labels, not raw secrets.
- Contact memory must be restricted to allowed agents.
- Memory reads and writes must be logged.

### tasks

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `request_id` | varchar(120) | unique |
| `owner_id` | uuid | FK `users.id` |
| `agent_id` | uuid | FK `agents.id` |
| `input_text` | text | required |
| `status` | varchar(40) | canonical task status; see Section 5 |
| `selected_skill_id` | uuid | FK `skills.id` nullable |
| `selected_tool_id` | uuid | FK `tools.id` nullable |
| `final_response` | text | nullable |
| `error_message` | text | nullable |
| `started_at` | timestamp | nullable |
| `completed_at` | timestamp | nullable |
| `created_at` | timestamp | required |
| `updated_at` | timestamp | required |

### task_steps

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `task_id` | uuid | FK `tasks.id` |
| `step_order` | integer | required |
| `step_name` | varchar(120) | required |
| `status` | varchar(30) | `success`, `failed`, `running`, `skipped` |
| `input_summary` | text | nullable |
| `output_summary` | text | nullable |
| `error_message` | text | nullable |
| `created_at` | timestamp | required |

### tool_calls

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `task_id` | uuid | FK `tasks.id` |
| `tool_id` | uuid | FK `tools.id` |
| `agent_id` | uuid | FK `agents.id` |
| `input_payload` | jsonb | nullable; mask secrets before logging |
| `output_payload` | jsonb | nullable; mask secrets before logging |
| `status` | varchar(30) | `success`, `failed`, `waiting_approval` |
| `latency_ms` | integer | nullable |
| `error_message` | text | nullable |
| `created_at` | timestamp | required |

Rules:

- Blocked tool requests should not use database status `blocked`.
- Blocked or denied tool requests are stored as `tool_calls.status = failed`.
- The blocked reason should be stored in `error_message`.
- API response status may still say `blocked` at the response level when a request is denied.

### approval_requests

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `task_id` | uuid | FK `tasks.id` |
| `agent_id` | uuid | FK `agents.id` |
| `tool_id` | uuid | FK `tools.id` nullable |
| `requested_action` | text | required |
| `risk_level` | varchar(30) | required |
| `status` | varchar(30) | `pending`, `approved`, `rejected`, `expired` |
| `request_payload` | jsonb | nullable; input preview only, mask secrets |
| `decision_reason` | text | nullable |
| `decided_by` | uuid | FK `users.id` nullable |
| `decided_at` | timestamp | nullable |
| `created_at` | timestamp | required |

### model_usage_logs

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `provider_id` | uuid | FK `model_providers.id` |
| `agent_id` | uuid | FK `agents.id` nullable |
| `task_id` | uuid | FK `tasks.id` nullable |
| `model_name` | varchar(120) | nullable |
| `prompt_tokens` | integer | nullable |
| `completion_tokens` | integer | nullable |
| `estimated_cost` | numeric(12,6) | nullable |
| `latency_ms` | integer | nullable |
| `status` | varchar(30) | `success`, `failed` |
| `error_message` | text | nullable |
| `created_at` | timestamp | required |

### activity_logs

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `request_id` | varchar(120) | nullable |
| `actor_type` | varchar(50) | `user`, `agent`, `system` |
| `actor_id` | uuid | nullable |
| `event_type` | varchar(120) | required |
| `message` | text | required |
| `metadata` | jsonb | nullable; mask secrets |
| `created_at` | timestamp | required |

### audit_logs

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | PK |
| `user_id` | uuid | FK `users.id` nullable |
| `action` | varchar(150) | required |
| `entity_type` | varchar(100) | required |
| `entity_id` | uuid | nullable |
| `before_data` | jsonb | nullable; mask secrets |
| `after_data` | jsonb | nullable; mask secrets |
| `ip_address` | varchar(80) | nullable |
| `created_at` | timestamp | required |

## 8. Important Indexes

| Table | Index |
| --- | --- |
| `users` | unique(`email`) |
| `agents` | unique(`slug`), index(`owner_id`), index(`status`) |
| `agent_instructions` | index(`agent_id`), index(`is_active`) |
| `skills` | unique(`slug`), index(`source_type`), index(`status`) |
| `agent_skills` | unique(`agent_id`, `skill_id`) |
| `tools` | unique(`slug`), index(`tool_type`), index(`source_type`), index(`risk_level`), index(`status`) |
| `agent_tools` | unique(`agent_id`, `tool_id`), index(`permission_mode`) |
| `github_imports` | index(`repo_url`), index(`status`), index(`commit_sha`), index(`import_type`) |
| `n8n_workflows` | unique(`slug`), index(`owner_id`), index(`slug`), index(`status`), index(`risk_level`) |
| `model_providers` | index(`provider_type`), index(`status`) |
| `memories` | index(`owner_id`), index(`agent_id`), index(`memory_type`), index(`visibility_scope`) |
| `tasks` | unique(`request_id`), index(`agent_id`), index(`status`), index(`created_at`) |
| `task_steps` | index(`task_id`, `step_order`) |
| `tool_calls` | index(`task_id`), index(`tool_id`), index(`status`) |
| `approval_requests` | index(`status`), index(`task_id`), index(`agent_id`) |
| `model_usage_logs` | index(`provider_id`), index(`agent_id`), index(`task_id`), index(`created_at`) |
| `activity_logs` | index(`request_id`), index(`event_type`), index(`created_at`) |
| `audit_logs` | index(`user_id`), index(`entity_type`), index(`created_at`) |

## 9. Data Security Rules

- API keys and OAuth secrets must not be stored as visible plaintext in database.
- Use `secret_reference` for provider credentials.
- Sensitive payloads should be masked in logs.
- Memory access is scoped per agent.
- Imported GitHub tool execution is disabled for MVP.
- Approval decisions must be immutable audit events.
- Soft delete is used for important configuration entities.

## 10. MVP Migration Order

1. Create `users` table.
2. Create `model_providers` table.
3. Create `agents` and `agent_instructions` tables.
4. Create `skills` and `agent_skills` tables.
5. Create `tools` and `agent_tools` tables.
6. Create `github_imports` table.
7. Create `memories` table.
8. Create `tasks`, `task_steps`, and `tool_calls` tables.
9. Create `approval_requests` table.
10. Create `model_usage_logs` table.
11. Create `activity_logs` and `audit_logs` tables.
12. Add indexes and constraints.

## 11. Seed Data for MVP

| Seed | Purpose |
| --- | --- |
| Owner user | Initial workspace login. |
| General Assistant Agent | Default general agent. |
| Coding Agent | Agent for code tasks, approval required for GitHub actions. |
| Automation Agent | Agent for n8n workflow calls. |
| OpenClaw Provider placeholder | Private subscription/OAuth provider config. |
| Gemini/OpenAI API provider placeholder | Fallback API provider. |
| Basic skills | `general-assistant`, `coding-review`, `n8n-automation`. |
| Basic tools | Safe placeholders only, such as `run_n8n_workflow` disabled until configured. |

Phase 2 future data model planning reference: see `docs/PHASE_2_FUTURE_DATA_MODEL.md`.
