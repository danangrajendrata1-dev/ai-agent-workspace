# Runtime Boundaries Freeze

## Current Alpha Status

- Alpha 18.3 is PASS.
- Alpha 18.4 freezes the current runtime boundary documentation.
- This document is reference-only. It does not grant execution power.

## Capability Status Definitions

- `disabled`: feature exists conceptually but cannot run yet. UI may show preview or read-only disabled state. Backend must reject execution.
- `suggestion_only`: system may suggest something, but suggestion creation must never execute.
- `explicit_confirm`: execution is allowed only after explicit user confirmation for a specific run and backend revalidation.
- `forbidden`: feature must remain blocked hard in the current Alpha.

## Frozen Runtime Boundaries

### 1. Chat Boundary

- Agent chat may process messages and return safe metadata.
- Chat may suggest workflow templates.
- Chat must not execute tools directly.
- Chat must not auto-execute workflows.
- Chat must not call arbitrary external URLs.
- Chat must not expose provider keys or secrets.
- Chat must not log raw prompt, chat, or knowledge content into audit, activity, or history rows.

### 2. Orchestrator Boundary

- Orchestrator routes, selects, and suggests only.
- Orchestrator must not execute tools.
- Orchestrator must not auto-trigger workflow webhooks.
- Orchestrator must not bypass agent ownership.
- Orchestrator must not bypass skill attachment or active checks.
- Orchestrator must not bypass workflow consent checks.

### 3. Workflow Boundary

- Workflow templates are code-owned.
- No user-supplied webhook URL.
- No custom or free-form webhook URL.
- Workflow suggestions are suggestion-only.
- Advanced workflow explicit execute requires a valid template, safe URL, active consent, binding, and backend validation.
- Chat-confirm execute requires explicit per-run confirmation and backend validation.
- Revoked consent blocks future execution.
- Safe execution history must not expose raw webhook response or sensitive payload.
- `output_summary` must never echo the raw webhook body. It may only contain a generic safe status-based summary.

### 4. Tool Boundary

- Tool execution remains disabled or blocked.
- `tool_skill` execution is forbidden.
- Tool execution stub must return blocked.
- Tool execution stub must not produce fake success or waiting approval status.

### 5. Model Provider Boundary

- Provider API keys are encrypted or masked.
- Raw keys must never be returned to the frontend.
- Provider connection test must be sanitized.
- `model_provider.raw_generation` is forbidden.
- Model router stub must return blocked.
- Model usage log must not record fake success for blocked stub behavior.
- Raw provider response must not be stored, logged, returned, or displayed.

### 6. OAuth, Payment, and Webhook Boundary

- OAuth connection is disabled or forbidden.
- Payment and billing are disabled or forbidden.
- `custom_webhook.execution` is forbidden.
- `user_supplied_webhook.execution` is forbidden.
- No route should accept an arbitrary custom webhook URL for execution.

### 7. Frontend Boundary

- Runtime capability matrix is read-only visibility metadata.
- Frontend must not use the matrix to unlock execution.
- No hidden run, retry, replay, or tool execution buttons.
- `Confirm Execute` appears only when a workflow suggestion has `execution_available === true`.
- Backend still revalidates everything; frontend metadata is never trusted.

## Explicit Forbidden Behaviors

- Do not reintroduce raw webhook body echo into workflow output summaries.
- Do not treat runtime capability metadata as authorization.
- Do not add tool, model, or workflow execution without a new safety review checkpoint.
- Do not add user-supplied or custom webhook execution.
- Do not log prompt, chat, or knowledge content into audit, activity, or history rows.
- Do not expose secrets, API keys, tokens, credentials, provider responses, or webhook responses in the UI or logs.

## Future Implementation Notes

- Keep `output_summary` generic and status-based only.
- Keep runtime capability matrix as visibility metadata only.
- Require a new safety checkpoint before any new execution path is enabled.
- Keep user-supplied webhook execution out of MVP scope.
- Preserve backend validation even when the frontend shows explicit confirmation state.

## Reference Scope

- This freeze applies to Alpha 18.4 and later until a new approved safety checkpoint replaces it.
- If a future implementation changes execution behavior, this document must be revisited first.
