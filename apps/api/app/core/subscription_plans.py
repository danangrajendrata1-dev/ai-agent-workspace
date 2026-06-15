from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


UserRole = Literal["admin", "user"]
SubscriptionPlan = Literal["free", "pro", "executive"]

ROLE_ADMIN: UserRole = "admin"
ROLE_USER: UserRole = "user"
LEGACY_ROLE_OWNER = "owner"

SUBSCRIPTION_PLAN_FREE: SubscriptionPlan = "free"
SUBSCRIPTION_PLAN_PRO: SubscriptionPlan = "pro"
SUBSCRIPTION_PLAN_EXECUTIVE: SubscriptionPlan = "executive"

DEFAULT_REGISTER_ROLE: UserRole = ROLE_USER
DEFAULT_REGISTER_SUBSCRIPTION_PLAN: SubscriptionPlan = SUBSCRIPTION_PLAN_FREE


@dataclass(frozen=True, slots=True)
class SubscriptionPlanLimits:
    max_agents: int
    n8n_access: bool
    max_saved_workflows: int


PLAN_LIMITS: dict[SubscriptionPlan, SubscriptionPlanLimits] = {
    SUBSCRIPTION_PLAN_FREE: SubscriptionPlanLimits(
        max_agents=5,
        n8n_access=False,
        max_saved_workflows=0,
    ),
    SUBSCRIPTION_PLAN_PRO: SubscriptionPlanLimits(
        max_agents=10,
        n8n_access=True,
        max_saved_workflows=1,
    ),
    SUBSCRIPTION_PLAN_EXECUTIVE: SubscriptionPlanLimits(
        max_agents=50,
        n8n_access=True,
        max_saved_workflows=10,
    ),
}


def get_subscription_plan_limits(plan: SubscriptionPlan) -> SubscriptionPlanLimits:
    try:
        return PLAN_LIMITS[plan]
    except KeyError as exc:
        raise ValueError(f"Unknown subscription plan: {plan}.") from exc


def can_access_n8n(plan: SubscriptionPlan) -> bool:
    return get_subscription_plan_limits(plan).n8n_access


def get_max_saved_workflows(plan: SubscriptionPlan) -> int:
    return get_subscription_plan_limits(plan).max_saved_workflows


def is_admin_role(role: str | None) -> bool:
    return role in {ROLE_ADMIN, LEGACY_ROLE_OWNER}
