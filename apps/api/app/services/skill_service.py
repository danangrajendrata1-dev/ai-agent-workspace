import re
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.subscription_plans import is_admin_role
from app.repositories import agent_repository, agent_skill_repository, skill_repository
from app.schemas.skill import (
    AgentSkillAssignRequest,
    AgentSkillResponse,
    SkillCreate,
    SkillLibraryItemResponse,
    SkillResponse,
    SkillUpdate,
)
from app.repositories import github_import_repository
from app.services.github_import_service import serialize_github_import


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:150] or "skill"


def ensure_unique_slug(
    db: Session,
    *,
    slug: str,
    current_skill_id: uuid.UUID | None = None,
) -> str:
    existing = skill_repository.get_by_slug(db, slug)
    if existing is None or existing.id == current_skill_id:
        return slug
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Skill slug is already in use.",
    )


def validate_skill_payload(source_type: str, source_id: uuid.UUID | None) -> None:
    if source_type == "manual" and source_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manual skills must not include source_id.",
        )


def _load_github_import_index(
    db: Session,
    *,
    owner_id: uuid.UUID | None = None,
) -> dict[str, dict]:
    github_imports = github_import_repository.list_imports(db, owner_id=owner_id)
    return {
        str(item.id): serialize_github_import(item).model_dump()
        for item in github_imports
    }


def _get_github_import_data_for_skill(
    skill,
    github_import_index: dict[str, dict],
) -> dict | None:
    if getattr(skill, "source_type", None) != "github" or not getattr(skill, "source_id", None):
        return None

    return github_import_index.get(str(skill.source_id))


def _is_approved_github_import(github_import_data: dict | None) -> bool:
    if github_import_data is None:
        return False

    import_status = github_import_data.get("import_status") or github_import_data.get("status")
    return import_status == "imported"


def _resolve_agent_for_skill_action(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
    current_user=None,
):
    if current_user is not None and is_admin_role(getattr(current_user, "role", None)):
        agent = agent_repository.get_by_id_for_admin(db, agent_id)
    else:
        agent = agent_repository.get_by_id(db, owner_id, agent_id)

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found.",
        )

    return agent


def _infer_skill_type(skill, github_import_data: dict | None) -> str:
    if not github_import_data:
        return "prompt_skill"

    import_type = github_import_data.get("skill_import_type")
    content_preview = str(github_import_data.get("content_preview") or "").lower()
    resource_paths = github_import_data.get("resource_paths") or []
    safe_resource_paths = github_import_data.get("safe_resource_paths") or []
    risky_resource_paths = github_import_data.get("risky_resource_paths") or []

    if import_type == "manifest_skill":
        if "workflow" in content_preview or "n8n" in content_preview:
            return "workflow_skill"
        if risky_resource_paths:
            return "tool_skill"
        if safe_resource_paths:
            return "knowledge_skill"
        return "prompt_skill"

    if import_type == "markdown_instruction":
        if risky_resource_paths:
            return "tool_skill"
        if safe_resource_paths:
            if "workflow" in content_preview or any("workflow" in path.lower() for path in resource_paths):
                return "workflow_skill"
            return "knowledge_skill"
        if "workflow" in content_preview or "automation" in content_preview:
            return "workflow_skill"
        return "prompt_skill"

    return "prompt_skill"


def _build_skill_security_state(skill, github_import_data: dict | None) -> tuple[str, str | None]:
    if getattr(skill, "deleted_at", None) is not None:
        return "blocked", "Skill has been removed."

    if getattr(skill, "status", None) == "disabled":
        return "blocked", "Skill is disabled."

    if github_import_data is None:
        if getattr(skill, "source_type", None) == "github":
            return "blocked", "Import source metadata is missing."
        return "safe", None

    import_status = github_import_data.get("import_status") or github_import_data.get("status")
    if import_status != "imported":
        return "blocked", f"Import status is {import_status or 'unknown'}."

    if github_import_data.get("inspection_errors"):
        return "blocked", "Import inspection reported blocking errors."

    if github_import_data.get("blocked_resource_paths"):
        return "blocked", "Blocked resource reference detected."

    if (
        github_import_data.get("risky_resource_paths")
        or github_import_data.get("has_executable_resources")
        or github_import_data.get("requires_review")
        or github_import_data.get("inspection_warnings")
        or getattr(skill, "risk_level", None) == "high"
    ):
        return "warning", None

    return "safe", None


def _build_skill_library_item(skill, github_import_data: dict | None) -> SkillLibraryItemResponse:
    security_status, block_reason = _build_skill_security_state(skill, github_import_data)
    import_status = "manual"
    source_url = None
    source_reference = None
    source_branch = None
    file_path = None
    warnings: list[str] = []
    resource_references: list[str] = []

    if github_import_data:
        import_status = github_import_data.get("import_status") or github_import_data.get("status") or "imported"
        source_url = github_import_data.get("repo_url") or None
        source_reference = github_import_data.get("commit_sha") or (
            str(skill.source_id) if getattr(skill, "source_id", None) else None
        )
        source_branch = github_import_data.get("branch") or None
        file_path = github_import_data.get("file_path") or None
        warnings = list(github_import_data.get("inspection_warnings") or [])
        resource_references = list(github_import_data.get("resource_paths") or [])

    return SkillLibraryItemResponse(
        id=skill.id,
        title=skill.name,
        skill_type=_infer_skill_type(skill, github_import_data),
        source_url=source_url,
        source_reference=source_reference,
        source_branch=source_branch,
        file_path=file_path,
        status=skill.status,
        import_status=import_status,
        security_status=security_status,
        risk_level=skill.risk_level,
        warnings=warnings,
        resource_references=resource_references,
        created_at=skill.created_at,
        is_attachable=security_status != "blocked",
        attach_block_reason=block_reason,
    )


def serialize_skill(skill) -> SkillResponse:
    return SkillResponse.model_validate(skill)


def serialize_assignment(assignment, github_import_data: dict | None = None) -> AgentSkillResponse:
    return AgentSkillResponse(
        id=assignment.id,
        agent_id=assignment.agent_id,
        skill_id=assignment.skill_id,
        is_enabled=assignment.is_enabled,
        created_at=assignment.created_at,
        skill=_build_skill_library_item(assignment.skill, github_import_data),
    )


def create_skill(db: Session, payload: SkillCreate) -> SkillResponse:
    validate_skill_payload(payload.source_type, payload.source_id)
    slug = ensure_unique_slug(db, slug=slugify(payload.slug or payload.name))

    skill_data = payload.model_dump()
    skill_data["slug"] = slug

    skill = skill_repository.create(db, skill_data)
    db.commit()
    db.refresh(skill)
    return serialize_skill(skill)


def list_skills(db: Session) -> list[SkillResponse]:
    skills = skill_repository.list(db)
    return [serialize_skill(skill) for skill in skills]


def list_skill_library(
    db: Session,
    *,
    owner_id: uuid.UUID | None = None,
) -> list[SkillLibraryItemResponse]:
    github_import_index = _load_github_import_index(db, owner_id=owner_id)
    skills = [
        skill
        for skill in skill_repository.list(db)
        if skill.source_type == "github" and skill.deleted_at is None
    ]
    library_items = [
        _build_skill_library_item(
            skill,
            github_import_index.get(str(skill.source_id)) if skill.source_id else None,
        )
        for skill in skills
    ]
    return library_items


def get_skill(db: Session, skill_id: uuid.UUID) -> SkillResponse:
    skill = skill_repository.get_by_id(db, skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found.",
        )
    return serialize_skill(skill)


def update_skill(db: Session, skill_id: uuid.UUID, payload: SkillUpdate) -> SkillResponse:
    skill = skill_repository.get_by_id(db, skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    source_type = update_data.get("source_type", skill.source_type)
    source_id = update_data.get("source_id", skill.source_id)
    validate_skill_payload(source_type, source_id)

    if "slug" in update_data or "name" in update_data:
        source_slug = update_data.get("slug") or update_data.get("name") or skill.slug
        update_data["slug"] = ensure_unique_slug(
            db,
            slug=slugify(source_slug),
            current_skill_id=skill.id,
        )

    skill = skill_repository.update(db, skill, update_data)
    db.commit()
    db.refresh(skill)
    return serialize_skill(skill)


def deactivate_skill(db: Session, skill_id: uuid.UUID) -> SkillResponse:
    skill = skill_repository.get_by_id(db, skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found.",
        )
    skill = skill_repository.soft_delete(db, skill, datetime.now(UTC))
    db.commit()
    db.refresh(skill)
    return serialize_skill(skill)


def assign_skill_to_agent(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
    payload: AgentSkillAssignRequest,
    current_user=None,
) -> AgentSkillResponse:
    agent = _resolve_agent_for_skill_action(
        db,
        owner_id=owner_id,
        agent_id=agent_id,
        current_user=current_user,
    )
    skill = skill_repository.get_by_id(db, payload.skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found.",
        )
    github_import_data = None
    if getattr(skill, "source_type", None) == "github" and getattr(skill, "source_id", None):
        github_import = github_import_repository.get_by_id_for_owner(db, skill.source_id, owner_id)
        if github_import is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Imported GitHub skill is unavailable or not approved.",
            )
        github_import_data = serialize_github_import(github_import).model_dump()
        if github_import_data.get("import_status") != "imported":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Imported GitHub skill is unavailable or not approved.",
            )

    assignment = agent_skill_repository.get_assignment(db, agent.id, skill.id)
    if assignment is not None:
        assignment.is_enabled = payload.is_enabled
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return serialize_assignment(assignment, github_import_data)

    assignment = agent_skill_repository.assign_skill_to_agent(
        db,
        {
            "agent_id": agent.id,
            "skill_id": skill.id,
            "is_enabled": payload.is_enabled,
        },
    )
    db.commit()
    db.refresh(assignment)
    assignment = agent_skill_repository.get_assignment(db, agent.id, skill.id)
    return serialize_assignment(assignment, github_import_data)


def attach_imported_skill_to_agent(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
    skill_id: uuid.UUID,
    current_user=None,
) -> AgentSkillResponse:
    agent = _resolve_agent_for_skill_action(
        db,
        owner_id=owner_id,
        agent_id=agent_id,
        current_user=current_user,
    )

    skill = skill_repository.get_by_id(db, skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found.",
        )
    if skill.source_type != "github":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only imported GitHub skills can be attached to agents.",
        )
    if skill.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill is no longer available.",
        )

    github_import = github_import_repository.get_by_id_for_owner(db, skill.source_id, owner_id) if skill.source_id else None
    github_import_data = serialize_github_import(github_import).model_dump() if github_import is not None else None
    library_item = _build_skill_library_item(skill, github_import_data)
    if not library_item.is_attachable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Blocked imported skill cannot be attached. "
                + (library_item.attach_block_reason or "Attachment is not allowed.")
            ),
        )

    assignment = agent_skill_repository.get_assignment(db, agent.id, skill.id)
    if assignment is not None:
        assignment.is_enabled = True
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return serialize_assignment(assignment, github_import_data)

    assignment = agent_skill_repository.assign_skill_to_agent(
        db,
        {
            "agent_id": agent.id,
            "skill_id": skill.id,
            "is_enabled": True,
        },
    )
    db.commit()
    db.refresh(assignment)
    assignment = agent_skill_repository.get_assignment(db, agent.id, skill.id)
    return serialize_assignment(assignment, github_import_data)


def remove_skill_from_agent(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
    skill_id: uuid.UUID,
    current_user=None,
) -> None:
    agent = _resolve_agent_for_skill_action(
        db,
        owner_id=owner_id,
        agent_id=agent_id,
        current_user=current_user,
    )
    assignment = agent_skill_repository.get_assignment(db, agent.id, skill_id)
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent skill assignment not found.",
        )

    agent_skill_repository.unassign_skill_from_agent(db, assignment)
    db.commit()


def list_agent_skills(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
    current_user=None,
) -> list[AgentSkillResponse]:
    return list_active_agent_skills(
        db,
        owner_id=owner_id,
        agent_id=agent_id,
        current_user=current_user,
    )


def list_active_agent_skills(
    db: Session,
    *,
    owner_id: uuid.UUID,
    agent_id: uuid.UUID,
    current_user=None,
) -> list[AgentSkillResponse]:
    agent = _resolve_agent_for_skill_action(
        db,
        owner_id=owner_id,
        agent_id=agent_id,
        current_user=current_user,
    )
    assignments = agent_skill_repository.list_agent_skills(db, agent.id)
    github_import_index = _load_github_import_index(db, owner_id=owner_id)
    active_assignments = []
    for assignment in assignments:
        if getattr(assignment, "agent_id", None) != agent.id:
            continue
        if not assignment.is_enabled:
            continue
        skill = assignment.skill
        if skill is None or skill.deleted_at is not None or skill.status == "disabled":
            continue
        github_import_data = _get_github_import_data_for_skill(skill, github_import_index)
        if getattr(skill, "source_type", None) == "github" and getattr(skill, "source_id", None):
            if not _is_approved_github_import(github_import_data):
                continue
        active_assignments.append(serialize_assignment(assignment, github_import_data))
    return active_assignments
