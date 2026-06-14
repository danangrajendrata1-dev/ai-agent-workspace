# Phase 2 Backend Module Plan

## 1. Purpose

This document defines the backend module split and file map for Phase 2 planning. It exists to prevent semantic collision with the current MVP backend and to identify safe future insertion points for GitHub skill import preview/save and n8n draft planning. This document is planning only.

## 2. Current Backend Boundary

The current backend boundary remains unchanged:

- Existing MVP routes, services, repositories, schemas, and models stay authoritative.
- GitHub import handling remains preview/review behavior in the current MVP.
- n8n workflow handling remains registry/config behavior in the current MVP.
- Approval and audit logging remain active safety layers in the current MVP.
- Runtime execution remains disabled in the current MVP.

Future Phase 2 work must not change current behavior until an explicit implementation step is approved.

## 3. Non-Goals

This phase does not include:

- Endpoint implementation
- Route implementation
- Database migration
- ORM model implementation
- Schema implementation
- Runtime execution
- n8n execution
- GitHub API execution
- Secret storage
- Approval execution

## 4. Existing Module Inventory

Current backend module groups already present:

- `core`: config, database session, security, dependencies, middleware
- `models`: SQLAlchemy entities and relationships
- `schemas`: Pydantic request and response schemas
- `repositories`: database access layer
- `services`: business logic layer
- `routes`: HTTP layer
- `integrations`: GitHub client, model router, model adapters

The current backend already has dedicated stacks for auth, agents, skills, tools, memories, tasks, approvals, logs, model providers, GitHub imports, and n8n workflows.

## 5. Existing GitHub Import Stack

The current GitHub import stack already exists:

- Route: `apps/api/app/routes/github_imports.py`
- Service: `apps/api/app/services/github_import_service.py`
- Repository: `apps/api/app/repositories/github_import_repository.py`
- Schema: `apps/api/app/schemas/github_import.py`
- Model: `apps/api/app/models/github_import.py`

Observed behavior:

- Preview exists.
- Approve / reject / disable flows exist.
- Import rows currently store preview metadata and review notes.
- Current preview may fetch text from GitHub.
- Current approve-skill flow saves reviewed skill content into `skills`.
- This stack is review/save behavior, not runtime execution.

Important note:

- This stack must not be blindly repurposed for Phase 2 without explicit review.
- The current preview/review flow is not the same as the future contract split described in Phase 2 docs.
- The extraction helper and validation helper already exist as pure backend helpers.
- The pipeline helper is the next implementation target and is not implemented yet unless a future step adds it.

## 6. Existing n8n Workflow Stack

The current n8n workflow stack already exists:

- Route: `apps/api/app/routes/n8n_workflows.py`
- Service: `apps/api/app/services/n8n_workflow_service.py`
- Repository: `apps/api/app/repositories/n8n_workflow_repository.py`
- Schema: `apps/api/app/schemas/n8n_workflow.py`
- Model: `apps/api/app/models/n8n_workflow.py`

Observed behavior:

- Registry create / read / update / soft-delete exists.
- Risk checks and secret-like validation already exist.
- Registry records are inactive by default.
- This stack is config-oriented, not execution-oriented.

Important note:

- The registry stack must not be confused with execution or draft activation.
- Phase 2 draft planning must stay separate from current registry CRUD semantics unless a future slice explicitly reuses fields.

## 7. Existing Approval and Audit Stack

The current approval and audit stack already exists:

- Approval route: `apps/api/app/routes/approvals.py`
- Approval service: `apps/api/app/services/approval_service.py`
- Audit/log service: `apps/api/app/services/log_service.py`
- Log repository: `apps/api/app/repositories/log_repository.py`

Observed behavior:

- Pending approvals can be created, listed, approved, and rejected.
- Approval actions write activity logs and audit logs.
- Log serialization masks secret-like values.

Important note:

- Phase 2 should reuse approval and audit primitives, but not overload them with execution semantics.
- Approval and execution must stay separate.

## 8. Semantic Collision Risks

Main collision risks:

- Reusing `github_imports` as if it already equals Phase 2 preview/save contract behavior.
- Reusing `n8n_workflows` as if it already equals draft activation flow.
- Mixing registry CRUD with draft lifecycle semantics.
- Treating approval records as execution permission instead of review evidence.
- Adding future endpoints before the supporting helper/service split is defined.

## 9. Future Module Split

Recommended future split for Phase 2:

- Keep current GitHub import registry stack intact for MVP behavior.
- Add future GitHub import validation helpers in a separate service or helper module.
- Add future manifest review helpers in a separate review-focused module.
- Add future n8n draft planning helpers in a separate draft-focused module.
- Keep approval and audit services as shared safety primitives.
- Keep routes thin and explicit.

This split reduces the risk of turning the current preview registry into a mixed-purpose execution surface.

## 10. Future GitHub Import Preview/Save Plan

Future preview/save planning should stay metadata-only:

- Preview should fetch and validate metadata only.
- Preview should not activate anything.
- Save should persist reviewed metadata only.
- Save should not execute imported content.
- Current MVP review endpoints already exist and remain separate from the future preview/save contract.

Recommended future insertion point:

- A helper/service layer under `app/services/` that validates manifest content before any future public endpoint is introduced.

## 11. Future Manifest Validation Plan

Future manifest validation should be isolated from route behavior:

- Validate manifest shape.
- Reject secrets, scripts, and auto-run content.
- Return structured validation results.
- Do not execute imported content.

Recommended future insertion point:

- A manifest validation helper that can be called by the existing GitHub import service or by a dedicated future service, but not by runtime code.

## 12. Future n8n Draft Workflow Plan

Future n8n draft planning should be draft-only:

- Draft records must remain inactive.
- Draft creation must not call n8n.
- Draft creation must not activate workflow.
- Draft creation must not execute workflow.

Recommended future insertion point:

- A future draft-planning service that prepares inactive workflow metadata and uses approval/log services for review evidence.

## 13. Future Activation Request Plan

Future activation requests should only create approval requests:

- Activation request is not activation.
- Activation request is not execution.
- Approval records must remain the gate.

Recommended future insertion point:

- Reuse `approval_service` and `log_service` as the shared backend gate.

## 14. Files To Reuse

Reusable files for Phase 2:

- `apps/api/app/core/dependencies.py`
- `apps/api/app/services/approval_service.py`
- `apps/api/app/services/log_service.py`
- `apps/api/app/repositories/approval_repository.py`
- `apps/api/app/repositories/log_repository.py`
- `apps/api/app/main.py`
- `apps/api/alembic/env.py`

Reuse rules:

- Use owner checks and current-user dependency patterns as-is.
- Use log masking and audit helpers as-is.
- Use Alembic metadata registration as-is.

## 15. Files To Avoid Changing Initially

Avoid changing these files in the first Phase 2 coding slice:

- `apps/api/app/routes/github_imports.py`
- `apps/api/app/services/github_import_service.py`
- `apps/api/app/repositories/github_import_repository.py`
- `apps/api/app/schemas/github_import.py`
- `apps/api/app/models/github_import.py`
- `apps/api/app/routes/n8n_workflows.py`
- `apps/api/app/services/n8n_workflow_service.py`
- `apps/api/app/repositories/n8n_workflow_repository.py`
- `apps/api/app/schemas/n8n_workflow.py`
- `apps/api/app/models/n8n_workflow.py`

Reason:

- These files already carry MVP behavior and can create semantic collision if changed too early.

## 16. Future Files To Add Only If Needed

Add future files only when the design needs separation that the current modules cannot cleanly support:

- `apps/api/app/services/github_import_preview_service.py`
- `apps/api/app/services/github_manifest_validation_service.py`
- `apps/api/app/services/n8n_draft_service.py`
- `apps/api/app/schemas/github_import_preview.py`
- `apps/api/app/schemas/github_manifest_validation.py`
- `apps/api/app/schemas/n8n_draft.py`

These are planning names only. They are not implemented in the current MVP.

## 17. Next Implementation Sequence

1. Backend manifest safety pipeline helper.
2. Pipeline helper final audit.
3. GitHub import service integration plan.
4. Safe pipeline connection inside service layer only.
5. Existing endpoint behavior audit after integration.
6. Frontend read-only preview integration only after backend behavior is stable.

Commit and push are manual checkpoints and must not be counted as separate numbered feature steps.

Why this roadmap order is safer than adding endpoints first:

- It validates the rules before any public surface is exposed.
- It reduces semantic collision with current MVP preview routes.
- It lets future preview/save endpoints reuse tested validation logic.
- It keeps runtime and network side effects out of the first slice.

## 18. Backend Safety Checklist

- Current MVP remains unchanged.
- Existing GitHub import stack is not blindly repurposed.
- Existing n8n registry stack is not confused with execution.
- Approval and activation remain separate.
- Activation and execution remain separate.
- Runtime remains disabled.
- No credentials or secrets are accepted in this phase.

## 19. Final Recommendation

Keep Phase 2 backend work modular and conservative. First build reusable validation helpers and keep routes untouched until the helper layer is stable. Only then consider future preview/save or draft-related endpoints.

## 20. Final Safety Statement

This document is planning only. It does not change the current MVP backend. It defines future backend module boundaries, file map, and safe insertion points for Phase 2. All implementation items remain FUTURE / NOT IMPLEMENTED until a later approved step.

Phase 2 documentation planning is temporarily complete after Step 65. Future documentation changes should be tied to real implementation changes, safety findings, or user-approved scope changes.
