from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.models.agent import Agent  # noqa: F401
from app.models.agent_instruction import AgentInstruction  # noqa: F401
from app.models.agent_skill import AgentSkill  # noqa: F401
from app.models.agent_tool import AgentTool  # noqa: F401
from app.models.activity_log import ActivityLog  # noqa: F401
from app.models.approval_request import ApprovalRequest  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.base import Base
from app.models.github_import import GitHubImport  # noqa: F401
from app.models.handoff_draft import HandoffDraft  # noqa: F401
from app.models.memory import Memory  # noqa: F401
from app.models.n8n_workflow import N8nWorkflow  # noqa: F401
from app.models.model_provider_api_key import ModelProviderApiKey  # noqa: F401
from app.models.model_usage_log import ModelUsageLog  # noqa: F401
from app.models.model_provider import ModelProvider  # noqa: F401
from app.models.model_provider_setting import ModelProviderSetting  # noqa: F401
from app.models.skill import Skill  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.task_step import TaskStep  # noqa: F401
from app.models.tool import Tool  # noqa: F401
from app.models.tool_call import ToolCall  # noqa: F401
from app.models.user import User  # noqa: F401


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
