import unittest

from app.services.skill_manifest_risk_service import assess_skill_manifest_risk


class SkillManifestRiskServiceTest(unittest.TestCase):
    def test_low_risk_metadata_only_manifest(self):
        result = assess_skill_manifest_risk(
            {
                "name": "Email Summary",
                "version": "1.0.0",
                "description": "Generate summary.",
                "author": None,
                "required_capabilities": [],
                "required_tools": [],
                "required_credentials": [],
                "required_domains": [],
                "n8n_workflow": None,
                "permissions_requested": [],
                "safety_notes": None,
            }
        )

        self.assertEqual(result.risk_level, "low")
        self.assertFalse(result.requires_review)
        self.assertFalse(result.is_blocked)
        self.assertTrue(result.reasons)

    def test_medium_risk_domain_and_capability_manifest(self):
        result = assess_skill_manifest_risk(
            {
                "name": "Email Summary",
                "version": "1.0.0",
                "description": "Generate summary.",
                "author": None,
                "required_capabilities": ["read_email", "summarize"],
                "required_tools": [],
                "required_credentials": [],
                "required_domains": ["example.com"],
                "n8n_workflow": None,
                "permissions_requested": ["read_email"],
                "safety_notes": None,
            }
        )

        self.assertEqual(result.risk_level, "medium")
        self.assertTrue(result.requires_review)
        self.assertFalse(result.is_blocked)
        self.assertGreaterEqual(len(result.reasons), 1)

    def test_high_risk_credential_tool_n8n_manifest(self):
        result = assess_skill_manifest_risk(
            {
                "name": "Automation",
                "version": "1.0.0",
                "description": "Automate workflow.",
                "author": None,
                "required_capabilities": [],
                "required_tools": ["read_email"],
                "required_credentials": [{"type": "email_oauth", "label": "Inbox"}],
                "required_domains": [],
                "n8n_workflow": {
                    "template_name": "Email summary pipeline",
                    "template_version": "1.0",
                    "description": "Draft and send summary.",
                    "required_nodes": ["Trigger"],
                    "risk_level": "medium",
                },
                "permissions_requested": [],
                "safety_notes": None,
            }
        )

        self.assertEqual(result.risk_level, "high")
        self.assertTrue(result.requires_review)
        self.assertFalse(result.is_blocked)
        self.assertTrue(any("Credentials requested." in reason for reason in result.reasons))
        self.assertTrue(any("External tools requested." in reason for reason in result.reasons))
        self.assertTrue(any("n8n workflow metadata requested." in reason for reason in result.reasons))

    def test_blocked_invalid_input(self):
        result = assess_skill_manifest_risk(None)  # type: ignore[arg-type]

        self.assertEqual(result.risk_level, "blocked")
        self.assertTrue(result.requires_review)
        self.assertTrue(result.is_blocked)
        self.assertTrue(result.reasons)

    def test_returns_reasons(self):
        result = assess_skill_manifest_risk(
            {
                "name": "Email Summary",
                "version": "1.0.0",
                "description": "Generate summary.",
                "author": None,
                "required_capabilities": [],
                "required_tools": [],
                "required_credentials": [],
                "required_domains": ["example.com"],
                "n8n_workflow": None,
                "permissions_requested": [],
                "safety_notes": None,
            }
        )

        self.assertTrue(result.reasons)
        self.assertIn("Domain allowlist requested.", result.reasons)


if __name__ == "__main__":
    unittest.main()
