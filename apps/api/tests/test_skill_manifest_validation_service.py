import unittest

from app.services.skill_manifest_validation_service import validate_skill_manifest


class SkillManifestValidationServiceTest(unittest.TestCase):
    def test_valid_minimal_manifest(self):
        result = validate_skill_manifest(
            {
                "name": "Email Summary",
                "version": "1.0.0",
                "description": "Generate a short summary.",
            }
        )

        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])
        self.assertEqual(
            result.normalized_manifest,
            {
                "name": "Email Summary",
                "version": "1.0.0",
                "description": "Generate a short summary.",
                "author": None,
                "required_capabilities": [],
                "required_tools": [],
                "required_credentials": [],
                "required_domains": [],
                "n8n_workflow": None,
                "permissions_requested": [],
                "safety_notes": None,
            },
        )

    def test_valid_full_metadata_manifest(self):
        result = validate_skill_manifest(
            {
                "name": " Email Summary ",
                "version": " 2.1.0 ",
                "description": " Summarize email threads for the owner. ",
                "author": " Agent Team ",
                "required_capabilities": ["read_email", "summarize", "triage"],
                "required_tools": ["gmail_reader", "notion_writer"],
                "required_credentials": [
                    {
                        "type": "email_oauth",
                        "label": "Primary email account",
                        "reason": "Read inbox content.",
                        "required": True,
                    }
                ],
                "required_domains": ["Example.COM", "mail.example.com"],
                "n8n_workflow": {
                    "template_name": "Email summary pipeline",
                    "template_version": " 1.0 ",
                    "description": " Draft and send summary. ",
                    "required_nodes": ["Trigger", "Send Email"],
                    "risk_level": "medium",
                },
                "permissions_requested": ["read_email", "send_summary"],
                "safety_notes": " Review before activation. ",
            }
        )

        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])
        self.assertEqual(
            result.normalized_manifest,
            {
                "name": "Email Summary",
                "version": "2.1.0",
                "description": "Summarize email threads for the owner.",
                "author": "Agent Team",
                "required_capabilities": ["read_email", "summarize", "triage"],
                "required_tools": ["gmail_reader", "notion_writer"],
                "required_credentials": [
                    {
                        "type": "email_oauth",
                        "label": "Primary email account",
                        "reason": "Read inbox content.",
                        "required": True,
                    }
                ],
                "required_domains": ["example.com", "mail.example.com"],
                "n8n_workflow": {
                    "template_name": "Email summary pipeline",
                    "template_version": "1.0",
                    "description": "Draft and send summary.",
                    "required_nodes": ["Trigger", "Send Email"],
                    "risk_level": "medium",
                },
                "permissions_requested": ["read_email", "send_summary"],
                "safety_notes": "Review before activation.",
            },
        )

    def test_rejects_unknown_top_level_field(self):
        result = validate_skill_manifest(
            {
                "name": "Email Summary",
                "version": "1.0.0",
                "description": "Generate a short summary.",
                "unexpected": "value",
            }
        )

        self.assertFalse(result.is_valid)
        self.assertTrue(any("Unknown top-level field: unexpected." in error for error in result.errors))
        self.assertIsNone(result.normalized_manifest)

    def test_rejects_raw_credential_secret_key(self):
        result = validate_skill_manifest(
            {
                "name": "Email Summary",
                "version": "1.0.0",
                "description": "Generate a short summary.",
                "required_credentials": [
                    {
                        "type": "email_oauth",
                        "api_key": "secret-value",
                    }
                ],
            }
        )

        self.assertFalse(result.is_valid)
        self.assertTrue(any("forbidden field" in error for error in result.errors))
        self.assertIsNone(result.normalized_manifest)

    def test_rejects_suspicious_nested_secret_key(self):
        result = validate_skill_manifest(
            {
                "name": "Email Summary",
                "version": "1.0.0",
                "description": "Generate a short summary.",
                "n8n_workflow": {
                    "template_name": "Email summary pipeline",
                    "required_nodes": [{"api_key": "secret-value"}],
                },
            }
        )

        self.assertFalse(result.is_valid)
        self.assertTrue(any("forbidden field" in error for error in result.errors))
        self.assertIsNone(result.normalized_manifest)

    def test_rejects_execution_instruction(self):
        result = validate_skill_manifest(
            {
                "name": "Email Summary",
                "version": "1.0.0",
                "description": "Generate a short summary.",
                "safety_notes": "Use curl to execute the import step.",
            }
        )

        self.assertFalse(result.is_valid)
        self.assertTrue(any("forbidden execution content" in error for error in result.errors))
        self.assertIsNone(result.normalized_manifest)

    def test_rejects_domain_with_protocol(self):
        result = validate_skill_manifest(
            {
                "name": "Email Summary",
                "version": "1.0.0",
                "description": "Generate a short summary.",
                "required_domains": ["https://example.com"],
            }
        )

        self.assertFalse(result.is_valid)
        self.assertTrue(any("must not include a protocol" in error for error in result.errors))
        self.assertIsNone(result.normalized_manifest)

    def test_rejects_wildcard_domain(self):
        result = validate_skill_manifest(
            {
                "name": "Email Summary",
                "version": "1.0.0",
                "description": "Generate a short summary.",
                "required_domains": ["*.example.com"],
            }
        )

        self.assertFalse(result.is_valid)
        self.assertTrue(any("must not contain wildcard characters" in error for error in result.errors))
        self.assertIsNone(result.normalized_manifest)

    def test_rejects_localhost_domain(self):
        result = validate_skill_manifest(
            {
                "name": "Email Summary",
                "version": "1.0.0",
                "description": "Generate a short summary.",
                "required_domains": ["localhost"],
            }
        )

        self.assertFalse(result.is_valid)
        self.assertTrue(any("must not be localhost" in error for error in result.errors))
        self.assertIsNone(result.normalized_manifest)

    def test_rejects_private_ip_domain(self):
        result = validate_skill_manifest(
            {
                "name": "Email Summary",
                "version": "1.0.0",
                "description": "Generate a short summary.",
                "required_domains": ["192.168.0.10"],
            }
        )

        self.assertFalse(result.is_valid)
        self.assertTrue(any("must not be an IP address" in error for error in result.errors))
        self.assertIsNone(result.normalized_manifest)

    def test_rejects_n8n_executable_workflow_keys(self):
        result = validate_skill_manifest(
            {
                "name": "Email Summary",
                "version": "1.0.0",
                "description": "Generate a short summary.",
                "n8n_workflow": {
                    "template_name": "Email summary pipeline",
                    "nodes": [],
                },
            }
        )

        self.assertFalse(result.is_valid)
        self.assertTrue(any("forbidden field" in error for error in result.errors))
        self.assertIsNone(result.normalized_manifest)

    def test_normalizes_missing_optional_list_fields(self):
        result = validate_skill_manifest(
            {
                "name": "Email Summary",
                "version": "1.0.0",
                "description": "Generate a short summary.",
            }
        )

        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.normalized_manifest)
        self.assertEqual(result.normalized_manifest["required_capabilities"], [])
        self.assertEqual(result.normalized_manifest["required_tools"], [])
        self.assertEqual(result.normalized_manifest["required_credentials"], [])
        self.assertEqual(result.normalized_manifest["required_domains"], [])
        self.assertEqual(result.normalized_manifest["permissions_requested"], [])
        self.assertIsNone(result.normalized_manifest["n8n_workflow"])


if __name__ == "__main__":
    unittest.main()
