# Phase 2 Future Frontend UX Planning

## 1. Purpose

This document defines future frontend UX planning for Phase 2. It covers preview and review surfaces for GitHub Skill Import, manifest validation, credential and domain requirements, n8n workflow draft preview, and activation request review. This is planning only.

## 2. Current MVP Frontend Boundary

Current MVP frontend boundary remains unchanged:

- JavaScript only
- Antique Ivory workspace UI
- Dashboard 3-column model
- Command input is draft-only
- Import Skill is preview-only
- n8n workflow is preview/read-only
- Settings are preview-only
- Runtime execution is disabled

Future UX in this document must not be read as current implementation.

## 3. Non-Goals

This phase does not include:

- Frontend implementation
- React components
- API client code
- Endpoint calls
- Runtime execution
- n8n execution
- GitHub import execution
- External model calls
- Tool execution
- Credential storage in frontend

## 4. UX Safety Rules

- Preview is not execution.
- Review is not activation.
- Activation is not execution.
- Future UI flows must remain explicitly labeled `FUTURE / NOT IMPLEMENTED`.
- Current MVP must not gain new execution actions.
- Current MVP localStorage keys must remain unchanged.
- Future credential panels must show type only, never raw secret values.
- Safety copy must be clear, calm, and professional.

## 5. Future UI Surface Overview

Planned future UI surfaces:

- GitHub Import Preview Modal
- Skill Manifest Validation Panel
- Permission Review Panel
- Credential Requirement Panel
- Domain Allowlist Review Panel
- n8n Draft Workflow Preview Panel
- Activation Request Confirmation Panel
- Approval Status Panel
- Safety Warning Banner
- Audit Trail Preview

Common future rule:

- Status: FUTURE / NOT IMPLEMENTED
- Execution: MUST NOT execute runtime, n8n, tools, models, GitHub scripts, or workflow actions
- Credential handling: MUST NOT collect or store raw secrets in current MVP
- Approval: MUST NOT approve, activate, or execute anything automatically

## 6. Future GitHub Skill Import Preview UX

### Status

FUTURE / NOT IMPLEMENTED

### Execution

MUST NOT execute runtime, n8n, tools, models, GitHub scripts, or workflow actions.

### Credential Handling

MUST NOT collect or store raw secrets in current MVP.

### Approval

MUST NOT approve, activate, or execute anything automatically.

### Purpose

Show GitHub repository preview before any future skill save flow.

### User-Visible Information

- Repository URL
- Branch
- Commit SHA
- File path
- Manifest preview
- Validation summary
- Safety notes

### Allowed Actions

- Review preview
- Expand manifest details
- Read validation results
- Cancel review

### Forbidden Actions

- Execute imported content
- Auto-save as active skill
- Auto-install dependencies
- Auto-activate anything

### Required Warning Copy

- `Preview only. Imported content is untrusted until reviewed.`
- `No execution in current MVP.`

### Backend Contract Reference

- `docs/PHASE_2_FUTURE_BACKEND_CONTRACTS.md`

### Safety Notes

Preview modal must feel intentional, not broken or empty. It must clearly communicate future planning only.

## 7. Future Skill Manifest Validation UX

### Status

FUTURE / NOT IMPLEMENTED

### Execution

MUST NOT execute runtime, n8n, tools, models, GitHub scripts, or workflow actions.

### Credential Handling

MUST NOT collect or store raw secrets in current MVP.

### Approval

MUST NOT approve, activate, or execute anything automatically.

### Purpose

Show safe/unsafe validation result for manifest content.

### User-Visible Information

- Validation pass/fail
- Invalid fields
- Unknown permissions
- Secret-like value warnings
- Script or auto-run rejection

### Allowed Actions

- Review validation
- Collapse or expand errors
- Cancel flow

### Forbidden Actions

- Save invalid manifest
- Execute content
- Auto-approve

### Required Warning Copy

- `Manifest validation is required before any future save flow.`
- `Secrets, scripts, and auto-run instructions are rejected.`

### Backend Contract Reference

- `docs/PHASE_2_FUTURE_BACKEND_CONTRACTS.md`

### Safety Notes

Validation UI must clearly separate safe metadata from unsafe content.

## 8. Future Permission Review UX

### Status

FUTURE / NOT IMPLEMENTED

### Execution

MUST NOT execute runtime, n8n, tools, models, GitHub scripts, or workflow actions.

### Credential Handling

MUST NOT collect or store raw secrets in current MVP.

### Approval

MUST NOT approve, activate, or execute anything automatically.

### Purpose

Show requested permissions before any future save or activation flow.

### User-Visible Information

- Requested permissions
- Permission scope
- Risk level
- Allow / block status
- Review notes

### Allowed Actions

- Review permission list
- Mark as safe for future review
- Cancel flow

### Forbidden Actions

- Auto-allow unknown permissions
- Auto-execute
- Auto-activate

### Required Warning Copy

- `Requested permissions must be reviewed before any future save or activation.`
- `Unknown permissions stay blocked by default.`

### Backend Contract Reference

- `docs/PHASE_2_FUTURE_BACKEND_CONTRACTS.md`

### Safety Notes

Permission review must make block state obvious and safe by default.

## 9. Future Credential Requirement UX

### Status

FUTURE / NOT IMPLEMENTED

### Execution

MUST NOT execute runtime, n8n, tools, models, GitHub scripts, or workflow actions.

### Credential Handling

MUST NOT collect or store raw secrets in current MVP.

### Approval

MUST NOT approve, activate, or execute anything automatically.

### Purpose

Show credential type requirements only.

### User-Visible Information

- Credential type
- Credential label
- Required or optional
- Missing status
- Secure vault note

### Allowed Actions

- Review type only
- Mark requirement acknowledged
- Cancel flow

### Forbidden Actions

- Enter raw secret
- Save raw credential
- Auto-bind credential

### Required Warning Copy

- `Credential type only. Raw secrets are not collected in current MVP.`
- `Future secure vault is separate and not implemented yet.`

### Backend Contract Reference

- `docs/PHASE_2_FUTURE_BACKEND_CONTRACTS.md`

### Safety Notes

Panel must never look like active secret input in current MVP.

## 10. Future Domain Allowlist UX

### Status

FUTURE / NOT IMPLEMENTED

### Execution

MUST NOT execute runtime, n8n, tools, models, GitHub scripts, or workflow actions.

### Credential Handling

MUST NOT collect or store raw secrets in current MVP.

### Approval

MUST NOT approve, activate, or execute anything automatically.

### Purpose

Show domains that must be explicitly reviewed before future network use.

### User-Visible Information

- Domain list
- Allowlist status
- Review notes
- Missing domain warning

### Allowed Actions

- Review domain list
- Mark allowlist reviewed
- Cancel flow

### Forbidden Actions

- Use unreviewed domain
- Auto-call network
- Auto-activate workflow

### Required Warning Copy

- `Domain use requires explicit review before any future network action.`
- `Fail closed if domain is not allowlisted.`

### Backend Contract Reference

- `docs/PHASE_2_FUTURE_BACKEND_CONTRACTS.md`

### Safety Notes

Domain review must be explicit and visible before any future network use.

## 11. Future n8n Workflow Draft Preview UX

### Status

FUTURE / NOT IMPLEMENTED

### Execution

MUST NOT execute runtime, n8n, tools, models, GitHub scripts, or workflow actions.

### Credential Handling

MUST NOT collect or store raw secrets in current MVP.

### Approval

MUST NOT approve, activate, or execute anything automatically.

### Purpose

Show an inactive workflow draft preview before any future activation flow.

### User-Visible Information

- Workflow template reference
- Draft status
- Required config summary
- Domain summary
- Credential type summary
- Safety notes

### Allowed Actions

- Review draft
- Expand template details
- Cancel flow

### Forbidden Actions

- Run workflow
- Activate workflow
- Auto-create active automation

### Required Warning Copy

- `Draft only. Workflow remains inactive by default.`
- `Activation is separate from execution.`

### Backend Contract Reference

- `docs/PHASE_2_FUTURE_BACKEND_CONTRACTS.md`

### Safety Notes

Draft preview must not imply execution is already available.

## 12. Future Activation Request UX

### Status

FUTURE / NOT IMPLEMENTED

### Execution

MUST NOT execute runtime, n8n, tools, models, GitHub scripts, or workflow actions.

### Credential Handling

MUST NOT collect or store raw secrets in current MVP.

### Approval

MUST NOT approve, activate, or execute anything automatically.

### Purpose

Confirm request only for future activation review.

### User-Visible Information

- Draft workflow reference
- Reason for activation request
- Review notes
- Pending approval status

### Allowed Actions

- Submit request
- Review request summary
- Cancel request

### Forbidden Actions

- Activate workflow
- Execute workflow
- Auto-approve request

### Required Warning Copy

- `This creates a request only. It does not activate or execute anything.`
- `Activation and execution remain separate future steps.`

### Backend Contract Reference

- `docs/PHASE_2_FUTURE_BACKEND_CONTRACTS.md`

### Safety Notes

Confirmation screen must feel final for request submission, not final for activation.

## 13. Future Approval Status UX

### Status

FUTURE / NOT IMPLEMENTED

### Execution

MUST NOT execute runtime, n8n, tools, models, GitHub scripts, or workflow actions.

### Credential Handling

MUST NOT collect or store raw secrets in current MVP.

### Approval

MUST NOT approve, activate, or execute anything automatically.

### Purpose

Display approval state for future flows.

### User-Visible Information

- Pending
- Approved
- Rejected
- Expired
- Review notes

### Allowed Actions

- View state
- Expand details
- Cancel flow

### Forbidden Actions

- Approve automatically
- Reject automatically
- Execute automatically

### Required Warning Copy

- `Approval status is informational until future approval flow exists.`
- `Approval does not equal execution.`

### Backend Contract Reference

- `docs/PHASE_2_FUTURE_BACKEND_CONTRACTS.md`

### Safety Notes

Approval UI must not look like live execution control in current MVP.

## 14. Future Error and Warning States

Future UI should use calm and explicit messaging:

- Validation failed
- Review required
- Approval required
- Draft inactive
- Domain not allowlisted
- Credential type missing

Forbidden copy:

- Raw stack traces
- Secret leakage
- Execution internals
- Provider tokens
- Webhook secrets

## 15. Future Empty and Loading States

Future UI should have clear states:

- Loading skeleton
- Empty preview
- No validation result yet
- No draft yet
- No approval yet

States must still communicate that future flows are planning only.

## 16. Future Audit Visibility UX

Future UI should expose:

- Import request timeline
- Validation timeline
- Review timeline
- Draft creation timeline
- Activation request timeline

Audit preview must be read-only.

## 17. Future Accessibility Notes

- Preserve readable contrast in Antique Ivory palette.
- Keep labels short and direct.
- Keep keyboard focus visible.
- Keep modal and panel layouts responsive.
- Do not rely on color only for safety state.

## 18. Frontend Implementation Checklist

- Keep Antique Ivory theme.
- Keep dashboard 3-column model.
- Keep sidebar actions opening modal or panel where appropriate.
- Keep current localStorage keys unchanged.
- Keep command input draft-only.
- Keep no TypeScript rule.
- Keep no new execution action in UI.
- Keep all future UX labeled `FUTURE / NOT IMPLEMENTED`.

## 19. Final Safety Statement

This document is planning only. It defines future frontend UX for Phase 2, not current product behavior. Import preview remains preview-only in current MVP. Future GitHub import preview, validation, credential review, domain allowlist review, draft workflow preview, activation request confirmation, approval status, and audit preview are all future planning only. Runtime execution remains disabled in the current MVP.

