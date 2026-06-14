# Phase 2 Future Backend Contracts

## 1. Purpose

This document defines future backend API contract planning for Phase 2. It is planning only. It describes how GitHub Skill Import preview/save and n8n workflow draft creation should behave in a future implementation, but it does not implement any endpoint or side effect.

## 2. Current MVP Boundary

Current MVP remains frozen on a safe boundary:

- GitHub Skill Import is preview-only.
- n8n workflow handling is preview/read-only.
- Runtime execution is disabled.
- Settings are preview-only.
- Command input is draft-only.
- Existing `/github-imports` review endpoints already exist in the current backend.
- Preview may fetch text from GitHub, but it must not execute content.
- `approve-skill` may save reviewed skill metadata into the skills registry.
- The extraction helper parses safe JSON text into a manifest dict candidate.
- The validation helper validates manifest dicts only.
- The pipeline helper is the next implementation target and is not implemented yet unless a future step adds it.

Future contracts in this document must not be read as current implementation.

## 3. Non-Goals

This phase does not include:

- Any endpoint implementation
- Any route implementation
- Any database migration
- Any runtime execution
- Any n8n execution
- Any GitHub import execution
- Any external model call
- Any tool execution
- Any credential saving in frontend
- Any automatic activation

## 4. Contract Safety Rules

- All contract descriptions are future only.
- All endpoints are marked `FUTURE / NOT IMPLEMENTED`.
- Preview must not save active state.
- Approval must not equal execution.
- Activation must not equal execution.
- Credentials must never be accepted as raw secrets unless a future secure vault exists.
- Runtime execution stays disabled in the current MVP.
- GitHub content remains untrusted until validated and reviewed.

## 5. Future Endpoint Overview

Planned future endpoints only:

- `POST /github-imports/preview`
- `POST /github-imports/save`
- `POST /skills/{id}/validate-manifest`
- `POST /n8n-workflows/drafts`
- `POST /n8n-workflows/{id}/activate-request`

Common future contract rule:

- Status: FUTURE / NOT IMPLEMENTED
- Execution: MUST NOT execute runtime, n8n, tools, models, or GitHub import scripts
- Credential handling: MUST NOT accept or store raw secrets unless future secure credential vault exists
- Approval: MUST NOT auto-approve or auto-activate

See also: `docs/PHASE_2_FUTURE_DATA_MODEL.md`.
See also: `docs/PHASE_2_FUTURE_FRONTEND_UX.md`.
See also: `docs/PHASE_2_BACKEND_MODULE_PLAN.md`.

## 6. Future GitHub Skill Import Preview Contract

### Status

FUTURE / NOT IMPLEMENTED

### Execution

MUST NOT execute runtime, n8n, tools, models, or GitHub import scripts.

### Credential Handling

MUST NOT accept or store raw secrets unless future secure credential vault exists.

### Approval

MUST NOT auto-approve or auto-activate.

### Purpose

Preview GitHub repository metadata and manifest content before any future save action.

### Allowed Input Shape

- `repo_url`
- `branch` optional
- `file_path` optional
- `commit_sha` optional

### Forbidden Input

- Raw secrets
- OAuth tokens
- Passwords
- Private keys
- Script bodies meant for execution
- Auto-run instructions

### Validation Rules

- URL must be valid and safe.
- Repository content must be treated as untrusted.
- Manifest fields must be allowlist only.
- Hidden scripts must be rejected.
- Unknown executable instructions must be rejected.

### Allowed Output Shape

- Repository metadata
- Manifest preview
- Validation result
- Review summary

### Forbidden Side Effects

- No save as active skill
- No execution
- No dependency install
- No automatic activation

### Audit Log Event

- `github_import_preview_requested`
- `github_import_preview_validated`

### Safety Notes

Preview only. Imported content remains untrusted until future human review and approval.
The current MVP review route may fetch text and save reviewed skill content, but that is not execution and is separate from this future contract.

## 7. Future GitHub Skill Import Save Contract

### Status

FUTURE / NOT IMPLEMENTED

### Execution

MUST NOT execute runtime, n8n, tools, models, or GitHub import scripts.

### Credential Handling

MUST NOT accept or store raw secrets unless future secure credential vault exists.

### Approval

MUST NOT auto-approve or auto-activate.

### Purpose

Save reviewed GitHub skill metadata after preview approval in a future implementation.

### Allowed Input Shape

- Reviewed skill metadata
- Repository reference
- Manifest reference
- Review notes

### Forbidden Input

- Raw secret values
- Hidden scripts
- Auto-run instructions
- Unreviewed manifest fields

### Validation Rules

- Save only reviewed metadata.
- Require prior validated preview state.
- Reject executable payloads.
- Reject unapproved fields.

### Allowed Output Shape

- Saved skill metadata reference
- Registry status
- Review record reference

### Forbidden Side Effects

- No activation
- No runtime execution
- No automatic assignment

### Audit Log Event

- `github_import_skill_saved`

### Safety Notes

Save only reviewed metadata in future implementation. Save does not mean execution.

## 8. Future Skill Manifest Validation Contract

### Status

FUTURE / NOT IMPLEMENTED

### Execution

MUST NOT execute runtime, n8n, tools, models, or GitHub import scripts.

### Credential Handling

MUST NOT accept or store raw secrets unless future secure credential vault exists.

### Approval

MUST NOT auto-approve or auto-activate.

### Purpose

Validate skill manifest content before preview or save in a future implementation.

### Allowed Input Shape

- Manifest JSON or structured manifest payload

### Forbidden Input

- Secrets
- Hidden scripts
- Auto-run instructions
- Unknown permissions
- Dependency install directives

### Validation Rules

- Reject secrets.
- Reject scripts.
- Reject auto-run instructions.
- Reject unknown permissions.
- Reject unsupported fields.
- Reject malformed version or identifiers.

### Allowed Output Shape

- Validation pass/fail
- Field-level error list
- Safety notes

### Forbidden Side Effects

- No save
- No execution
- No activation

### Audit Log Event

- `skill_manifest_validated`

### Safety Notes

Validation must happen before any future preview save flow or n8n planning flow.

## 9. Future n8n Workflow Draft Contract

### Status

FUTURE / NOT IMPLEMENTED

### Execution

MUST NOT execute runtime, n8n, tools, models, or GitHub import scripts.

### Credential Handling

MUST NOT accept or store raw secrets unless future secure credential vault exists.

### Approval

MUST NOT auto-approve or auto-activate.

### Purpose

Create an inactive n8n workflow draft in a future implementation.

### Allowed Input Shape

- Skill reference
- Workflow template reference
- Required config summary
- Credential type references only
- Domain references only

### Forbidden Input

- Raw credential values
- Raw webhook secrets
- Private keys
- Auto-run instructions
- Direct execution payloads

### Validation Rules

- Require inactive draft state.
- Require allowlisted domains.
- Require credential type only, not secret value.
- Reject direct execution flags.
- Reject activation flags in draft creation.

### Allowed Output Shape

- Draft workflow reference
- Inactive status
- Review summary

### Forbidden Side Effects

- No workflow execution
- No activation
- No credential binding to raw secret values

### Audit Log Event

- `n8n_workflow_draft_created`

### Safety Notes

Draft only. Inactive by default. Execution remains a separate future step.

## 10. Future Credential Requirement Contract

### Status

FUTURE / NOT IMPLEMENTED

### Execution

MUST NOT execute runtime, n8n, tools, models, or GitHub import scripts.

### Credential Handling

MUST NOT accept or store raw secrets unless future secure credential vault exists.

### Approval

MUST NOT auto-approve or auto-activate.

### Purpose

Describe credential type requirements without exposing credential values.

### Allowed Input Shape

- Credential type
- Credential label
- Usage context

### Forbidden Input

- API key
- OAuth token
- Password
- Private key
- Secret value

### Validation Rules

- Accept type only.
- Reject secret values.
- Reject raw tokens.
- Reject key material.

### Allowed Output Shape

- Credential type list
- Requirement summary
- Missing requirement notices

### Forbidden Side Effects

- No saving secret value
- No binding secret value
- No runtime execution

### Audit Log Event

- `credential_requirement_reviewed`

### Safety Notes

Type only. Value comes later through secure backend or secure vault.

## 11. Future Domain Allowlist Contract

### Status

FUTURE / NOT IMPLEMENTED

### Execution

MUST NOT execute runtime, n8n, tools, models, or GitHub import scripts.

### Credential Handling

MUST NOT accept or store raw secrets unless future secure credential vault exists.

### Approval

MUST NOT auto-approve or auto-activate.

### Purpose

Declare allowed domains before any future network use.

### Allowed Input Shape

- Domain list
- Hostname list
- Allowlist notes

### Forbidden Input

- Wildcard secret domains
- Unknown private endpoints
- Execution URLs without review

### Validation Rules

- Domain must be explicitly allowlisted.
- Network use must fail closed if domain missing.
- Review is required before network use.

### Allowed Output Shape

- Allowlist summary
- Pass/fail result
- Missing domain list

### Forbidden Side Effects

- No network call
- No execution
- No auto-binding

### Audit Log Event

- `domain_allowlist_reviewed`

### Safety Notes

Domain allowlisting is explicit and reviewable before future use.

## 12. Future Workflow Activation Request Contract

### Status

FUTURE / NOT IMPLEMENTED

### Execution

MUST NOT execute runtime, n8n, tools, models, or GitHub import scripts.

### Credential Handling

MUST NOT accept or store raw secrets unless future secure credential vault exists.

### Approval

MUST NOT auto-approve or auto-activate.

### Purpose

Create an approval request for a future workflow activation action.

### Allowed Input Shape

- Draft workflow reference
- Activation reason
- Review notes

### Forbidden Input

- Direct activation flag
- Execution payload
- Raw credential value

### Validation Rules

- Create approval request only.
- Do not activate workflow.
- Do not execute workflow.
- Require existing inactive draft.

### Allowed Output Shape

- Approval request reference
- Pending status
- Review summary

### Forbidden Side Effects

- No activation
- No execution
- No auto-approval

### Audit Log Event

- `workflow_activation_requested`

### Safety Notes

Approval request is not activation. Activation is not execution.

## 13. Future Approval Relationship

Approval chain future state:

- Import preview approval
- Skill save approval
- Draft workflow creation approval
- Workflow activation approval
- Future execution approval

Rules:

- Approval is a gate.
- Approval is not execution.
- Approval is not activation.
- Approval records must be logged.

## 14. Future Audit Logging Contract

Future audit logging must capture:

- Import preview request
- Manifest validation result
- Skill save decision
- Draft workflow creation
- Credential requirement review
- Domain allowlist review
- Activation request
- Approval decision

Logs must mask:

- Secrets
- Tokens
- API keys
- Passwords
- Private keys
- Webhook secrets

## 15. Error Response Planning

Future error responses should be safe and generic.

Allowed error patterns:

- Validation failed
- Review required
- Approval required
- Draft inactive
- Domain not allowlisted
- Credential type missing

Forbidden error patterns:

- Raw stack traces
- Secret leakage
- Execution internals
- Provider tokens
- Webhook secrets

## 16. Security Review Checklist

- Manifest allowlist only
- No secret values in manifest
- No hidden scripts
- No auto-run instructions
- No automatic dependency install
- No automatic workflow activation
- No automatic credential binding
- No automatic runtime execution
- No external model call during import/review
- No raw webhook secret storage
- Domains explicitly allowlisted
- Logs required for every future contract event

## 17. Contract Implementation Checklist

- Keep all endpoints marked FUTURE / NOT IMPLEMENTED
- Keep current MVP boundary intact
- Keep preview and save separated
- Keep draft and activation separated
- Keep approval and execution separated
- Keep credentials type-only in contract
- Keep domains allowlisted before use
- Keep runtime execution disabled in current MVP

## 18. Final Safety Statement

These contracts are planning only. They define future behavior for Phase 2, not current product behavior. GitHub Skill Import remains future planning until implemented. n8n workflow draft creation remains future planning until implemented. Approval does not equal execution. Activation does not equal execution. Runtime execution remains disabled in the current MVP.
