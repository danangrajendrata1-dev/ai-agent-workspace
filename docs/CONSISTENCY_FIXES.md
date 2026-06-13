# Consistency Fixes v2.1 — Personal AI Agent Workspace

This file summarizes the consistency fixes applied before implementation.

## 1. Removed undefined source tables

The older Database document referenced `skill_sources` and `tool_sources`, but those tables were not defined.

Decision:

- Do not create separate `skill_sources` or `tool_sources` tables for MVP.
- Use `github_imports`, `skills.source_type`, `skills.source_id`, `tools.source_type`, and `tools.source_id` instead.

## 2. Unified skill and tool status values

Decision:

- `skills.status`: `active`, `inactive`, `disabled`.
- `tools.status`: `active`, `inactive`, `disabled`.

`disabled` is used for safety, especially imported/critical items.

## 3. Unified task lifecycle

Canonical task statuses:

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

Decision:

- Do not use generic task status `running` for MVP.
- Use `running_tool` when an approved tool is executing.

## 4. Unified memory categories

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

Decision:

- `sensitive_config_reference` stores reference labels only.
- It must never store plaintext secrets.

## 5. Clarified blocked tools schema

Decision:

- Keep `agent_tools` table.
- Add `permission_mode` with values `allow` and `block`.
- No row means not available.
- Block wins over allow.

## 6. Clarified GitHub imported tool risk

Decision:

- Previewing/registering an imported GitHub tool is high risk.
- Executing an imported GitHub tool is critical.
- Imported GitHub tool execution is disabled for MVP.

## 7. Files updated

- `PRD.md`
- `TECHNICAL.md`
- `DATABASE.md`
- `SECURITY.md`
- `AGENTS.md`
