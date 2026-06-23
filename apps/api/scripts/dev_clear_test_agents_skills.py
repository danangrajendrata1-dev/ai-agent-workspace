from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

from sqlalchemy import delete, func, select, text


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal, engine
from app.models import (  # noqa: E402
    Agent,
    AgentAvatarAsset,
    AgentInstruction,
    AgentSkill,
    AgentTool,
    ApprovalRequest,
    ChatSession,
    GitHubImport,
    HandoffDraft,
    Memory,
    ModelUsageLog,
    Skill,
    Task,
    TaskStep,
    ToolCall,
    WorkflowExecution,
    WorkflowSkillTemplateBinding,
)


DELETE_ORDER = [
    ("agent instructions", AgentInstruction),
    ("agent avatar assets", AgentAvatarAsset),
    ("agent skill relations", AgentSkill),
    ("agent tool relations", AgentTool),
    ("memories linked to agents", Memory),
    ("chat sessions linked to agents", ChatSession),
    ("handoff drafts linked to agents", HandoffDraft),
    ("workflow executions linked to agents/skills", WorkflowExecution),
    ("model usage logs linked to agents/tasks", ModelUsageLog),
    ("tasks", Task),
    ("skills / library records", Skill),
    ("skill review/import records", GitHubImport),
    ("workflow skill template bindings", WorkflowSkillTemplateBinding),
    ("agents", Agent),
]

PRESERVED_TABLES = [
    ("users", "users"),
    ("model providers", "model_providers"),
    ("model provider settings", "model_provider_settings"),
    ("provider API keys", "model_provider_api_keys"),
]


def count_rows(session, model) -> int:
    stmt = select(func.count()).select_from(model)
    return int(session.execute(stmt).scalar_one())


def sample_rows(session, model, columns: Iterable, limit: int = 10):
    stmt = select(*columns).select_from(model).order_by(model.created_at.asc()).limit(limit)
    return session.execute(stmt).all()


def print_sample(title: str, rows, empty_label: str = "none") -> None:
    print(f"{title}:")
    if not rows:
        print(f"  - {empty_label}")
        return

    for row in rows:
        values = [str(item) for item in row]
        print(f"  - {' | '.join(values)}")


def print_counts(session, label: str) -> None:
    child_total = (
        count_rows(session, AgentInstruction)
        + count_rows(session, AgentAvatarAsset)
        + count_rows(session, AgentSkill)
        + count_rows(session, AgentTool)
        + count_rows(session, Task)
        + count_rows(session, TaskStep)
        + count_rows(session, ApprovalRequest)
        + count_rows(session, ToolCall)
        + count_rows(session, Memory)
        + count_rows(session, ChatSession)
        + count_rows(session, HandoffDraft)
        + count_rows(session, WorkflowExecution)
        + count_rows(session, ModelUsageLog)
        + count_rows(session, WorkflowSkillTemplateBinding)
    )

    print(label)
    print(f"- agents: {count_rows(session, Agent)}")
    print(f"- agent_skill relations: {count_rows(session, AgentSkill)}")
    print(f"- imported skills / library skills: {count_rows(session, Skill)}")
    print(f"- skill review/import records: {count_rows(session, GitHubImport)}")
    print(f"- related child records: {child_total}")
    print(f"- task steps: {count_rows(session, TaskStep)}")
    print(f"- approval requests: {count_rows(session, ApprovalRequest)}")
    print(f"- tool calls: {count_rows(session, ToolCall)}")
    print(f"- memories linked to agents: {count_rows(session, Memory)}")
    print(f"- chat sessions linked to agents: {count_rows(session, ChatSession)}")
    print(f"- handoff drafts linked to agents: {count_rows(session, HandoffDraft)}")
    print(f"- workflow executions linked to agents/skills: {count_rows(session, WorkflowExecution)}")
    print(f"- model usage logs linked to agents/tasks: {count_rows(session, ModelUsageLog)}")
    print(f"- workflow skill template bindings: {count_rows(session, WorkflowSkillTemplateBinding)}")


def print_preserved_counts(session, label: str) -> None:
    print(label)
    for title, table_name in PRESERVED_TABLES:
        value = int(session.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar_one())
        print(f"- {title}: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Clear test agents and imported skills data only.")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually delete the data. Without this flag the script only prints a dry run.",
    )
    args = parser.parse_args()

    print(f"Target DB: {engine.url.render_as_string(hide_password=True)}")
    print(f"Mode: {'CONFIRM DELETE' if args.confirm else 'DRY RUN'}")

    with SessionLocal() as preview_session:
        print_counts(preview_session, "Counts before:")
        print_preserved_counts(preview_session, "Preserved tables before:")

        print("Target rows to delete:")
        print_sample(
            "Agents",
            sample_rows(preview_session, Agent, [Agent.id, Agent.name, Agent.slug, Agent.owner_id, Agent.status], limit=20),
        )
        print_sample(
            "Skills / library",
            sample_rows(preview_session, Skill, [Skill.id, Skill.name, Skill.slug, Skill.source_type, Skill.status], limit=20),
        )
        print_sample(
            "GitHub imports",
            sample_rows(preview_session, GitHubImport, [GitHubImport.id, GitHubImport.repo_url, GitHubImport.file_path, GitHubImport.status], limit=20),
        )

        if not args.confirm:
            print("Dry run only. No data deleted.")
            return 0

        preview_session.rollback()

    try:
        with SessionLocal() as session:
            with session.begin():
                for _, model in DELETE_ORDER:
                    session.execute(delete(model))
    except Exception as exc:
        print(f"Delete failed: {exc}")
        raise

    with SessionLocal() as session:
        print_counts(session, "Counts after:")
        print_preserved_counts(session, "Preserved tables after:")

    print("Delete complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
