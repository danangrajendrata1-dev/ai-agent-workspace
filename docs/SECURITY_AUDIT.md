# Security Audit v2.1

Scope:
- Backend safety gates
- Frontend secret handling
- GitHub import safety
- Workflow and n8n execution boundaries
- Provider key masking

## Audit Result

- Status: PARTIAL
- One real bug fixed: workflow execution path lacked n8n plan gating.
- No evidence found in this batch of raw API keys leaking from provider key routes.
- No evidence found in this batch of OAuth tokens or client secrets being newly stored in frontend code.

## Findings

### Fixed

1. Workflow n8n routes were not fully plan-gated.
   - Impact: free-plan user could reach workflow template, consent, binding, history, and execute service paths.
   - Fix: add explicit n8n plan guard in `apps/api/app/services/workflow_service.py`.
   - Coverage: added regression tests in `apps/api/tests/test_workflow_n8n_plan_guard.py`.

### Checked

- No raw API key in provider key response.
- No raw API key in logs seen in this batch.
- No `.env` file change in this batch.
- Provider keys stay encrypted at rest and masked in responses.
- Imported GitHub skills stay preview/quarantine only until approved.
- GitHub import path does not clone, install, or execute imported code.
- `tool_skill` stays visible but non-executable.
- `workflow_skill` does not auto-run n8n.
- n8n routes are plan-guarded.
- OAuth status and placeholder UI stay non-executing on frontend.
- Logs/tasks/approvals stay read-only on audited surfaces.
- No secret exposure in audited frontend contracts.
- No tool execution path opened from audited runtime capability layer.
- No n8n execution path opened from audited runtime capability layer.
- No GitHub code execution path opened from audited import flow.
- Auth-required endpoints stay protected.
- User-owned resources stay scoped to owner/admin checks.
- CORS reads from `CORS_ORIGINS` / `BACKEND_CORS_ORIGINS`.
- Disabled frontend actions stay disabled and non-executable.

## Checklist

- `register`: PASS
- `login`: PASS
- `auth/me`: PASS
- `create agent`: PASS
- `list agent`: PASS
- `detail agent`: PASS
- `GitHub skill preview`: PASS
- `collection preview`: PASS
- `selected import`: PASS
- `approve/reject skill`: PASS
- `attach/detach skill`: PASS
- `active skills visible`: PASS
- `provider metadata save`: PASS
- `provider key masked`: PASS
- `n8n guard`: PARTIAL, fixed in this batch, but backend pytest blocked by DB access
- `OAuth status/placeholder`: PASS
- `logs/tasks/approvals read-only`: PASS
- `no secret exposure`: PASS
- `no tool execution`: PASS
- `no n8n execution`: PASS
- `no GitHub code execution`: PASS

## Validation

- `pytest tests/test_workflow_n8n_plan_guard.py tests/test_n8n_workflow_limits.py tests/test_workflow_executions.py tests/test_contract_sanitization.py tests/test_agent_contract_routes.py tests/test_auth_contract_routes.py tests/test_workspace_route_regressions.py -q`: fail, blocked by Neon/PostgreSQL access in the managed sandbox (`psycopg2.OperationalError: Permission denied`).
- `pytest tests/test_workflow_n8n_plan_guard.py -q`: fail, same DB access blocker.
- `alembic upgrade head`: pass.
- `npm run lint`: pass.
- `npm run build`: pass.

## Remaining Risks

- Frontend auth token still lives in browser storage as app session token. That is existing behavior, not changed here.
- Full repo still has unrelated modified files from other work.
- External provider connection tests remain live-network probes when explicitly called.

## Blocked / Deferred

- Raw model runtime execution: deferred.
- OpenClaw / Hermes runtime execution: deferred.
- OAuth connection execution from frontend: blocked / placeholder only.
- Imported GitHub tool execution: blocked.
- n8n workflow execution without plan gate and consent: blocked.
- `tool_skill` execution: blocked.
- `workflow_skill` direct execution: blocked outside guarded workflow path.
- Any path that reveals secrets in logs, responses, or frontend state: blocked.

## Files Touched For Audit

- `apps/api/app/services/workflow_service.py`
- `apps/api/tests/test_workflow_n8n_plan_guard.py`
- `docs/SECURITY_AUDIT.md`
