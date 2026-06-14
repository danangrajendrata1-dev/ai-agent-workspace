# Phase 2 Skill Import and n8n Architecture

## 1. Purpose

This document defines the safe planning direction for Phase 2 of Personal AI Agent Workspace. The focus is GitHub Skill Import and n8n workflow draft creation. This is architecture planning only. No implementation, endpoint, migration, or execution is defined here.

## 2. Current MVP Safety Boundary

The current MVP is frozen on a safe boundary:

- Frontend is JavaScript only.
- Runtime execution is disabled.
- GitHub Skill Import is preview-only.
- Existing GitHub import review routes may fetch text from GitHub, but they do not execute content.
- n8n workflow handling is preview/read-only.
- Settings are preview-only.
- Command input is draft-only and UI-only.

Phase 2 must preserve those boundaries until a future step explicitly changes them.

## 3. Non-Goals

Phase 2 does not include:

- Runtime execution
- GitHub code execution
- Automatic dependency installation
- n8n workflow execution
- Automatic workflow activation
- Credential storage in the frontend
- Model or tool execution without approval
- Secret storage inside manifests
- Any uncontrolled automation

## 4. Core Safety Principles

- Import is not execution.
- Imported content is untrusted until reviewed.
- Allowlist fields only.
- Validate before save.
- Draft before activation.
- Approval before activation.
- Activation and execution are separate steps.
- Credentials are user-owned and attached later.
- Domains must be allowlisted before use.
- Logs must record import, review, draft, and approval events.
- Current MVP runtime stays disabled.

## 5. GitHub Skill Import Safe Flow

Safe GitHub Skill Import should follow this future planning flow:

1. User submits a GitHub URL.
2. Planned backend flow fetches metadata only.
3. Planned backend flow locates the skill manifest.
4. Manifest is parsed and validated.
5. System shows a preview.
6. User reviews the preview.
7. User approves import.
8. Planned backend flow saves skill metadata.
9. Skill appears in the skill list after future implementation.
10. No execution occurs.

Rules:

- No automatic code execution.
- No automatic dependency install.
- No automatic runtime or model call.
- No hidden side effects during preview.

## 6. Skill Manifest Schema

The manifest should be a safe metadata package, not an executable payload.

Proposed manifest shape:

```json
{
  "name": "Email Summary",
  "version": "1.0.0",
  "description": "Summarize recent emails into a concise daily digest.",
  "author": "Workspace Owner",
  "required_capabilities": ["email_read", "summary"],
  "required_tools": ["read_email"],
  "required_credentials": [
    {
      "type": "email_oauth",
      "label": "User email account"
    }
  ],
  "required_domains": [
    "gmail.com"
  ],
  "workflow_template": {
    "type": "n8n",
    "template_id": "email-summary-draft"
  },
  "permissions_requested": [
    "read_email"
  ],
  "safety_notes": [
    "Preview only until reviewed.",
    "No auto activation.",
    "No execution in MVP."
  ]
}
```

Manifest must not contain:

- API keys
- OAuth tokens
- Passwords
- Private keys
- Executable secrets
- Hidden scripts
- Auto-run instructions

## 7. Skill Validation Rules

Validation must be strict:

- Accept only known manifest fields.
- Reject unknown executable instructions.
- Reject raw HTML content if not needed.
- Reject script blocks.
- Reject dependency install instructions.
- Reject secret-like values.
- Reject dangerous URLs or unsupported protocols.
- Reject malformed versions or invalid identifiers.

Validation must happen before any save or any draft workflow creation.

## 8. Human Review and Approval Flow

GitHub skill import requires a human review step.

Review should show:

- Repository URL
- Manifest version
- Required capabilities
- Required tools
- Required credentials by type only
- Required domains
- Safety notes
- Review status

Approval in future flow means:

- Import is accepted as metadata.
- No execution is enabled.
- The imported skill remains subject to permission and approval rules.
- Current MVP approve-skill behavior may save reviewed skill content into the registry, but that is not execution.

## 9. n8n Workflow Draft Creation Flow

Future n8n draft flow:

1. Skill has a workflow template reference.
2. Planned system checks required configuration.
3. User maps credentials and config.
4. Planned backend creates an inactive draft workflow only.
5. User reviews the draft.
6. User requests activation.
7. Planned approval record is created.
8. Owner reviews the request.
9. Future activation can happen only after approval.
10. Execution still requires a separate explicit future action.

Rules:

- Draft first, inactive by default.
- No automatic activation.
- No automatic execution.
- No automatic binding of credentials.
- No automatic model or runtime call.

## 10. Credential and Domain Requirements

Credential and domain handling must stay server-side and explicit.

Requirements:

- n8n base URL is server-side only.
- n8n API key is server-side only.
- Public webhook or domain requirement must be declared.
- Email or OAuth credential is user-owned.
- Credential binding happens later through secure backend or n8n storage.
- Frontend never stores credentials.
- localStorage never stores API keys, passwords, or secrets.

## 11. Approval Before Activation

Approval gates should exist for future Phase 2 flow:

- Skill import approval
- Workflow draft creation approval
- Workflow activation approval
- Future execution approval

Approval must:

- Be explicit
- Be logged
- Be reviewable
- Not trigger execution by itself

Approval and execution are separate actions.

## 12. Execution Safety Boundary

The execution boundary must remain strict:

- No uncontrolled execution
- No automatic workflow run
- No automatic Hermes runtime run
- No automatic external model call
- No automatic tool execution
- No GitHub import execution in MVP

Current MVP remains non-executable for these surfaces.

## 13. Data Storage Planning

Future storage may include:

- `skill_imports`
- `skill_manifests`
- `n8n_workflow_drafts`
- `credential_requirements`
- `approval_requests` extension
- `audit_logs`

See also: `docs/PHASE_2_FUTURE_DATA_MODEL.md`.
See also: `docs/PHASE_2_FUTURE_FRONTEND_UX.md`.

Purpose:

- Store metadata only
- Store draft state only
- Store review and approval trail
- Store audit trail

No plaintext secret storage in these records.

## 14. Future Backend Planning

Future backend work should be introduced only after design approval.

Current MVP note:

- Existing `/github-imports` review endpoints already exist in the current backend.
- This future contract is separate from those current endpoints.
- The extraction helper and validation helper already exist as pure backend helpers.
- The pipeline helper is the next implementation target and is not implemented yet unless a future step adds it.

Possible future endpoints as design draft only:

- `POST /github-imports/preview`
- `POST /github-imports/save`
- `POST /n8n-workflows/drafts`
- `POST /n8n-workflows/{id}/activate-request`

Status:

- FUTURE
- NOT IMPLEMENTED

Backend implementation must preserve:

- Allowlist field validation
- Approval logging
- Inactive draft defaults
- Server-side credential handling

See also: `docs/PHASE_2_FUTURE_BACKEND_CONTRACTS.md`.

## 15. Future Frontend Planning

Future frontend work may show:

- GitHub import preview
- Manifest review
- Required credentials by type only
- Required domain list
- Draft workflow summary
- Approval request state

Frontend must not:

- Store credentials
- Trigger execution
- Pretend import is already active
- Pretend workflow is already executable

## 16. Audit Logging Requirements

Log these events when Phase 2 later exists:

- Import request created
- Repository metadata fetched
- Manifest parsed
- Manifest validation failed or passed
- Review completed
- Skill metadata saved
- Draft workflow created
- Draft workflow approved
- Draft workflow activation requested
- Future execution requested

Logs must mask:

- Secrets
- Tokens
- API keys
- Passwords
- Webhook secrets

## 17. Risk Register

Main risks:

- Malicious repository content
- Prompt injection inside README or manifest
- Secret leakage
- Workflow execution abuse
- Credential misuse
- Dependency execution
- Webhook exposure
- False assumption that preview means execution is safe

## 18. Phase 2 Implementation Checklist

- Define manifest allowlist
- Define validation rules
- Define approval states
- Define draft workflow state
- Define storage fields
- Define audit events
- Define safe preview UI
- Define credential handling policy
- Define activation gating
- Keep execution disabled until future approval

## 19. Final Safety Statement

Phase 2 must remain planning-first, review-first, and approval-first. GitHub skill import is not execution. n8n workflow draft creation is not execution. Imported content remains untrusted until reviewed. Runtime execution remains disabled in the current MVP.

Phase 2 documentation planning is temporarily complete after this step. Future documentation changes should be tied to real implementation changes, safety findings, or user-approved scope changes.
