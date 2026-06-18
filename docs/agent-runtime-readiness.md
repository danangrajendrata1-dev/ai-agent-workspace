# Agent Runtime Readiness Design

## Current Alpha Status

- Alpha 19.0 is a design and service-contract checkpoint only.
- Runtime execution remains disabled.
- No tool, model, or workflow execution power is added by this document.

## Purpose

This document defines the safe readiness shape for future agent runtime execution without enabling execution in the current Alpha.

## Non-Goals For Current Alpha

- Do not run agent runtime tasks.
- Do not call external model providers.
- Do not call Hermes or OpenClaw runtime adapters.
- Do not execute tools or tool skills.
- Do not auto-execute from chat.
- Do not add retry or replay controls.
- Do not add custom or user-supplied webhooks.
- Do not add OAuth or payment activation.

## Future Runtime Lifecycle States

- `disabled`: runtime execution is not enabled yet.
- `planned`: runtime is defined in design but not yet active.
- `queued_future`: runtime is scheduled for a later checkpoint.
- `blocked`: runtime is blocked by safety review or missing requirements.
- `completed_future`: runtime capability is ready in a future approved checkpoint.
- `failed_future`: runtime readiness or activation failed.

## Runtime Request Contract Draft

Future runtime requests should carry safe metadata only:

- `agent_id`
- `session_id`
- `user_intent_summary`, not raw prompt text
- `allowed_skill_types`
- `capability_key`
- `confirmation_required`

## Runtime Response Contract Draft

Future runtime responses should expose only safe execution metadata:

- `status`
- `safe_message`
- `runtime_event_id` if a future runtime event exists
- no raw provider response
- no raw tool response
- no prompt echo

## Runtime Guard Requirements

- Owner check.
- Active agent check.
- Active skill check.
- Capability matrix check for visibility only, not sole authorization.
- Consent and confirmation where required.
- Provider key availability check without exposing the key.
- No `tool_skill` execution unless a future safety review explicitly allows it.
- No raw model generation until a separate future checkpoint approves it.

## Logging Rules

- Do not log raw prompt, chat, or knowledge content into audit, activity, or history rows.
- Do not log raw provider responses.
- Do not log raw tool responses.
- Only safe status and event metadata may be stored for readiness tracking.

## Frontend Rules

- Show readiness status only.
- Do not add a Run Agent button yet.
- Do not add a Runtime Execute button yet.
- Do not add retry or replay controls.
- Keep the UI read-only.

## Future Alpha Gates

- Alpha 19.x must start with an explicit safety review before runtime activation.
- Model provider raw generation must remain forbidden until separately approved.
- Tool execution must remain blocked until separately approved.
- No user-supplied or custom webhook execution may be added without a new review.

## Runtime Event Contract Stub

- Alpha 19.2 defines a safe runtime event contract stub for future use.
- Alpha 19.2 does not create a runtime event table, runtime event history, or runtime execution path.
- The contract may only use safe fields such as `event_id`, `agent_id`, `session_id`, `status`, `event_type`, `capability_key`, `safe_message`, `created_at`, `finished_at`, `requires_confirmation`, `confirmation_state`, `safe_error_code`, and `safe_error_message`.
- The contract must not include raw prompt, raw chat, raw knowledge content, raw provider response, raw tool response, raw webhook response, secrets, credentials, tokens, webhook URLs, arbitrary URLs, request headers, response headers, or stack traces.
- The contract is read-only metadata only and must not be treated as execution authorization.

## Boundary Notes

- `docs/runtime-boundaries.md` freezes the current execution boundaries.
- This document defines the next readiness shape without changing those boundaries.
- If future implementation changes execution behavior, both documents must be revisited first.
