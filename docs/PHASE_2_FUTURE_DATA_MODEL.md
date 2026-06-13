# Phase 2 Future Data Model Planning

## 1. Purpose

This document defines future data model planning for Phase 2. It covers the storage shape that may be needed for GitHub Skill Import, Skill Manifest review, n8n inactive workflow drafts, credential requirement references, domain allowlist references, approval relationships, and audit relationships. This is planning only.

See also: `docs/PHASE_2_FUTURE_FRONTEND_UX.md`.
See also: `docs/PHASE_2_BACKEND_MODULE_PLAN.md`.

## 2. Current MVP Database Boundary

Current MVP database boundary remains unchanged:

- Existing MVP tables and contracts stay authoritative.
- Runtime execution is disabled in current MVP.
- GitHub import handling is preview-only in current MVP.
- n8n workflow handling is preview/read-only in current MVP.
- Settings are preview-only in current MVP.

Future data models in this document must not be treated as implemented behavior.

## 3. Non-Goals

This phase does not include:

- Database migration
- Alembic revision
- ORM model implementation
- Endpoint implementation
- Route implementation
- Runtime execution
- n8n execution
- GitHub import execution
- External model call
- Tool execution
- Credential value storage

## 4. Data Safety Rules

- Future entities are planning only.
- Future entities must be marked `FUTURE / NOT IMPLEMENTED`.
- Future entities must not exist in current MVP schema.
- Future entities must store metadata only, not executable behavior.
- Secrets must never be stored as raw values.
- Credentials must be referenced by type or label only.
- Domain allowlists must be explicit and reviewable.
- Approval must not equal execution.
- Activation must not equal execution.
- Runtime execution remains disabled in current MVP.

## 5. Future Entity Overview

Planned future entities:

- `github_skill_imports`
- `skill_manifest_reviews`
- `skill_manifest_permissions`
- `skill_required_credentials`
- `skill_required_domains`
- `n8n_workflow_drafts`
- `workflow_activation_requests`

Common rule for each entity:

- Status: FUTURE / NOT IMPLEMENTED
- Migration: MUST NOT exist in current MVP
- Runtime: MUST NOT trigger runtime, n8n, tools, models, or GitHub execution
- Secrets: MUST NOT store raw API keys, OAuth tokens, passwords, private keys, or executable secrets

## 6. Future GitHub Import Records

### Entity: `github_skill_imports`

- Status: FUTURE / NOT IMPLEMENTED
- Migration: MUST NOT exist in current MVP
- Runtime: MUST NOT trigger runtime, n8n, tools, models, or GitHub execution
- Secrets: MUST NOT store raw API keys, OAuth tokens, passwords, private keys, or executable secrets

Purpose:

- Store metadata for a GitHub skill import request.
- Track repository reference and import review state.

Example fields:

- `id`
- `repo_url`
- `branch`
- `commit_sha`
- `file_path`
- `import_status`
- `reviewed_by`
- `reviewed_at`
- `created_at`

Forbidden fields:

- Raw secret values
- OAuth tokens
- Passwords
- Private keys
- Hidden scripts
- Auto-run instructions

Relationship to existing MVP concepts:

- Future record only.
- Current MVP preview remains read-only and does not require this entity yet.
- Imported skill content remains untrusted until validated and reviewed.

Lifecycle / status values:

- `preview`
- `review_pending`
- `approved`
- `rejected`
- `saved`
- `disabled`

Audit log events:

- `github_skill_import_recorded`
- `github_skill_import_reviewed`
- `github_skill_import_saved`

Safety notes:

- Store metadata only.
- Never store executable import payloads.
- Never store raw secret material.

## 7. Future Skill Manifest Records

### Entity: `skill_manifest_reviews`

- Status: FUTURE / NOT IMPLEMENTED
- Migration: MUST NOT exist in current MVP
- Runtime: MUST NOT trigger runtime, n8n, tools, models, or GitHub execution
- Secrets: MUST NOT store raw API keys, OAuth tokens, passwords, private keys, or executable secrets

Purpose:

- Store validation and review state for a skill manifest.
- Preserve what was reviewed, when, and by whom.

Example fields:

- `id`
- `github_skill_import_id`
- `manifest_version`
- `validation_result`
- `validation_errors`
- `review_notes`
- `reviewed_by`
- `reviewed_at`

Forbidden fields:

- Secret values
- Hidden scripts
- Auto-run instructions
- Unverified executable instructions

Relationship to existing MVP concepts:

- Future review layer for GitHub skill import.
- Current MVP preview is not a stored review flow yet.

Lifecycle / status values:

- `pending`
- `valid`
- `invalid`
- `approved`
- `rejected`

Audit log events:

- `skill_manifest_review_started`
- `skill_manifest_review_completed`
- `skill_manifest_review_rejected`

Safety notes:

- Review records must remain metadata only.
- Manifest content remains untrusted until validation passes.

## 8. Future Skill Review Records

### Entity: `skill_manifest_permissions`

- Status: FUTURE / NOT IMPLEMENTED
- Migration: MUST NOT exist in current MVP
- Runtime: MUST NOT trigger runtime, n8n, tools, models, or GitHub execution
- Secrets: MUST NOT store raw API keys, OAuth tokens, passwords, private keys, or executable secrets

Purpose:

- Store requested permission metadata from a manifest.
- Track which permissions were requested and which were allowed.

Example fields:

- `id`
- `skill_manifest_review_id`
- `permission_name`
- `permission_scope`
- `permission_status`
- `approval_required`

Forbidden fields:

- Raw secrets
- Runtime commands
- Auto-run flags
- Hidden execution instructions

Relationship to existing MVP concepts:

- Maps future manifest permissions to the existing approval model.
- Does not change current MVP permission enforcement.

Lifecycle / status values:

- `requested`
- `allowed`
- `blocked`
- `requires_review`

Audit log events:

- `skill_permission_requested`
- `skill_permission_reviewed`

Safety notes:

- Permission data is descriptive only.
- Block must remain safe default for unknown or risky permissions.

## 9. Future n8n Workflow Draft Records

### Entity: `n8n_workflow_drafts`

- Status: FUTURE / NOT IMPLEMENTED
- Migration: MUST NOT exist in current MVP
- Runtime: MUST NOT trigger runtime, n8n, tools, models, or GitHub execution
- Secrets: MUST NOT store raw API keys, OAuth tokens, passwords, private keys, or executable secrets

Purpose:

- Store an inactive workflow draft for future n8n automation.
- Preserve template reference and review state.

Example fields:

- `id`
- `skill_manifest_review_id`
- `workflow_template_id`
- `workflow_name`
- `draft_status`
- `created_by`
- `created_at`
- `updated_at`

Forbidden fields:

- Raw webhook secrets
- Private key values
- Execution payloads
- Auto-activate flags

Relationship to existing MVP concepts:

- Future storage layer for the workflow draft planning doc.
- Current MVP n8n data remains preview/read-only only.

Lifecycle / status values:

- `draft`
- `inactive`
- `review_pending`
- `approval_pending`
- `approved`
- `rejected`
- `disabled`

Audit log events:

- `n8n_workflow_draft_recorded`
- `n8n_workflow_draft_reviewed`
- `n8n_workflow_draft_approved`

Safety notes:

- Draft must be inactive by default.
- Draft is not execution.
- Draft is not activation.

## 10. Future Credential Requirement Records

### Entity: `skill_required_credentials`

- Status: FUTURE / NOT IMPLEMENTED
- Migration: MUST NOT exist in current MVP
- Runtime: MUST NOT trigger runtime, n8n, tools, models, or GitHub execution
- Secrets: MUST NOT store raw API keys, OAuth tokens, passwords, private keys, or executable secrets

Purpose:

- Describe credential type requirements for a future skill or workflow.
- Track requirement labels without storing credential values.

Example fields:

- `id`
- `skill_manifest_review_id`
- `credential_type`
- `credential_label`
- `credential_scope`
- `required`

Forbidden fields:

- Raw credential value
- Secret material
- Password
- OAuth token
- Private key

Relationship to existing MVP concepts:

- Future planning record only.
- Current MVP credential handling remains server-side and separate.

Lifecycle / status values:

- `required`
- `optional`
- `missing`
- `mapped`
- `rejected`

Audit log events:

- `credential_requirement_recorded`
- `credential_requirement_reviewed`

Safety notes:

- Type only, never value.
- Future secure vault remains separate and not implemented here.

## 11. Future Credential Reference Rules

### Entity: `skill_required_credentials`

Rules for credential references:

- Store type or label only.
- Store no raw secret value.
- Store no plaintext token.
- Store no password.
- Store no private key.
- Store no executable secret.

Future secure credential vault:

- Separate future system.
- Not implemented in current MVP.
- Must be required before any credential value storage.

## 12. Future Domain Allowlist Records

### Entity: `skill_required_domains`

- Status: FUTURE / NOT IMPLEMENTED
- Migration: MUST NOT exist in current MVP
- Runtime: MUST NOT trigger runtime, n8n, tools, models, or GitHub execution
- Secrets: MUST NOT store raw API keys, OAuth tokens, passwords, private keys, or executable secrets

Purpose:

- Record domains that must be allowed before future network use.
- Keep domain review explicit and auditable.

Example fields:

- `id`
- `skill_manifest_review_id`
- `domain`
- `allowlist_status`
- `reviewed_by`
- `reviewed_at`

Forbidden fields:

- Secret values
- Raw URLs containing secrets
- Execution URLs without review

Relationship to existing MVP concepts:

- Domain allowlist is a future requirement for import and draft planning.
- Current MVP makes no network use from these future records.

Lifecycle / status values:

- `pending`
- `allowed`
- `blocked`
- `review_required`

Audit log events:

- `domain_allowlist_recorded`
- `domain_allowlist_reviewed`

Safety notes:

- Domains must be reviewed before any future network use.
- Fail closed if domain is missing or unapproved.

## 13. Future Approval Relationship

Future approval relationships may connect:

- GitHub import preview review
- Skill manifest review
- Permission review
- Workflow draft creation
- Workflow activation request

Rules:

- Approval is metadata only.
- Approval is not execution.
- Approval is not activation.
- Approval records must reference the related future entity.

## 14. Future Audit Log Relationship

Future audit relationships may connect to:

- GitHub import records
- Skill manifest reviews
- Permission records
- Credential requirement records
- Domain allowlist records
- n8n workflow drafts
- Workflow activation requests

Audit events should capture:

- Who reviewed
- What was reviewed
- When it was reviewed
- Whether it passed or failed

Logs must mask:

- Secrets
- Tokens
- API keys
- Passwords
- Private keys
- Webhook secrets

## 15. Future Status Lifecycle

Canonical future statuses should remain explicit and separate from current MVP states.

Examples:

- Import preview: `preview`, `review_pending`, `approved`, `rejected`, `saved`, `disabled`
- Manifest review: `pending`, `valid`, `invalid`, `approved`, `rejected`
- Credential requirement: `required`, `optional`, `missing`, `mapped`, `rejected`
- Domain allowlist: `pending`, `allowed`, `blocked`, `review_required`
- Workflow draft: `draft`, `inactive`, `review_pending`, `approval_pending`, `approved`, `rejected`, `disabled`
- Activation request: `pending`, `approved`, `rejected`, `expired`

Rules:

- Draft and inactive are not execution states.
- Activation is not execution.
- Approval is not execution.

## 16. Future Data Retention Rules

- Store only metadata required for review and audit.
- Keep raw secrets out of all future records.
- Retain audit records longer than preview records when needed.
- Soft delete can be used for review artifacts if future implementation requires it.
- Deleted or rejected review artifacts must still preserve safe audit trail references.

## 17. Future Indexing Notes

Potential future indexes may include:

- `repo_url`
- `commit_sha`
- `skill_manifest_review_id`
- `workflow_template_id`
- `credential_type`
- `domain`
- `draft_status`
- `approval_status`

Index planning should support:

- Review lookup
- Audit lookup
- Draft lookup
- Safe filtering

## 18. Future Migration Checklist

- Define new tables only after design approval.
- Map entity relationships first.
- Keep secret storage external.
- Keep runtime disabled until future approval.
- Keep current MVP schema unchanged.
- Keep future data model separate from current MVP tables.

## 19. Security Review Checklist

- No secret values in records
- No hidden scripts in records
- No auto-run instructions in records
- No raw webhook secrets in records
- No raw credential values in records
- No runtime execution implied
- No n8n execution implied
- No GitHub import execution implied
- No approval equals execution confusion
- No activation equals execution confusion

## 20. Final Safety Statement

This document is planning only. All future entities are `FUTURE / NOT IMPLEMENTED`. Current MVP database boundary stays unchanged. Imported content remains untrusted until validated and reviewed. Workflow drafts remain inactive by default. Approval does not equal execution. Activation does not equal execution. Runtime execution remains disabled in the current MVP.
