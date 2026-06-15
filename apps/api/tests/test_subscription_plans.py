import unittest

from app.core.subscription_plans import (
    PLAN_LIMITS,
    ROLE_ADMIN,
    ROLE_USER,
    SUBSCRIPTION_PLAN_EXECUTIVE,
    SUBSCRIPTION_PLAN_FREE,
    SUBSCRIPTION_PLAN_PRO,
    get_subscription_plan_limits,
    is_admin_role,
)


class SubscriptionPlansTest(unittest.TestCase):
    def test_plan_limits_mapping(self):
        self.assertEqual(get_subscription_plan_limits(SUBSCRIPTION_PLAN_FREE), PLAN_LIMITS[SUBSCRIPTION_PLAN_FREE])
        self.assertEqual(get_subscription_plan_limits(SUBSCRIPTION_PLAN_PRO), PLAN_LIMITS[SUBSCRIPTION_PLAN_PRO])
        self.assertEqual(
            get_subscription_plan_limits(SUBSCRIPTION_PLAN_EXECUTIVE),
            PLAN_LIMITS[SUBSCRIPTION_PLAN_EXECUTIVE],
        )

        self.assertEqual(PLAN_LIMITS[SUBSCRIPTION_PLAN_FREE].max_agents, 5)
        self.assertFalse(PLAN_LIMITS[SUBSCRIPTION_PLAN_FREE].n8n_access)
        self.assertEqual(PLAN_LIMITS[SUBSCRIPTION_PLAN_FREE].max_saved_workflows, 0)

        self.assertEqual(PLAN_LIMITS[SUBSCRIPTION_PLAN_PRO].max_agents, 10)
        self.assertTrue(PLAN_LIMITS[SUBSCRIPTION_PLAN_PRO].n8n_access)
        self.assertEqual(PLAN_LIMITS[SUBSCRIPTION_PLAN_PRO].max_saved_workflows, 1)

        self.assertEqual(PLAN_LIMITS[SUBSCRIPTION_PLAN_EXECUTIVE].max_agents, 50)
        self.assertTrue(PLAN_LIMITS[SUBSCRIPTION_PLAN_EXECUTIVE].n8n_access)
        self.assertEqual(PLAN_LIMITS[SUBSCRIPTION_PLAN_EXECUTIVE].max_saved_workflows, 10)

    def test_is_admin_role_accepts_admin_and_legacy_owner(self):
        self.assertTrue(is_admin_role(ROLE_ADMIN))
        self.assertTrue(is_admin_role("owner"))
        self.assertFalse(is_admin_role(ROLE_USER))

    def test_unknown_plan_raises(self):
        with self.assertRaises(ValueError):
            get_subscription_plan_limits("starter")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
