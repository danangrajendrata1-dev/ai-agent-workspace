import unittest
from unittest.mock import patch

from app.services.skill_markdown_instruction_service import (
    inspect_markdown_instruction_skill,
)


class SkillMarkdownInstructionServiceTest(unittest.TestCase):
    def test_plain_markdown_instruction_only_content_is_safe_low_risk(self):
        result = inspect_markdown_instruction_skill(
            "## Skill\nUse this skill to summarize notes into a concise digest."
        )

        self.assertEqual(result.skill_import_type, "markdown_instruction")
        self.assertTrue(result.is_safe)
        self.assertEqual(result.risk_level, "low")
        self.assertEqual(result.errors, [])
        self.assertFalse(result.requires_review)
        self.assertFalse(result.has_executable_resources)

    def test_pdf_tutorial_qpdf_password_is_safe_but_requires_review(self):
        result = inspect_markdown_instruction_skill(
            "Use qpdf --password=mypassword --decrypt encrypted.pdf decrypted.pdf."
        )

        self.assertTrue(result.is_safe)
        self.assertEqual(result.risk_level, "high")
        self.assertTrue(result.requires_review)
        self.assertTrue(any("Command example detected" in warning for warning in result.warnings))
        self.assertTrue(any("secret-related terms" in warning.lower() for warning in result.warnings))

    def test_pdf_tutorial_writer_encrypt_is_safe_but_requires_review(self):
        result = inspect_markdown_instruction_skill(
            'Example: writer.encrypt("userpassword", "ownerpassword")'
        )

        self.assertTrue(result.is_safe)
        self.assertEqual(result.risk_level, "medium")
        self.assertTrue(result.requires_review)
        self.assertTrue(any("Code example detected" in warning for warning in result.warnings))

    def test_generic_secret_words_do_not_block_by_themselves(self):
        result = inspect_markdown_instruction_skill(
            "This guide mentions password, encrypt, decrypt, credential, token, and api key."
        )

        self.assertTrue(result.is_safe)
        self.assertEqual(result.risk_level, "low")
        self.assertFalse(result.requires_review)
        self.assertTrue(any("secret-related terms" in warning.lower() for warning in result.warnings))

    def test_markdown_with_safe_resource_path_is_safe_medium_risk(self):
        result = inspect_markdown_instruction_skill(
            "Use [guide](docs/guide.md) and [data](assets/data.csv)."
        )

        self.assertTrue(result.is_safe)
        self.assertEqual(result.risk_level, "medium")
        self.assertTrue(result.requires_review)
        self.assertEqual(result.safe_resource_paths, ["docs/guide.md", "assets/data.csv"])

    def test_markdown_with_risky_executable_resource_is_safe_high_risk(self):
        result = inspect_markdown_instruction_skill(
            "Use [script](scripts/process.py) for local preprocessing."
        )

        self.assertTrue(result.is_safe)
        self.assertEqual(result.risk_level, "high")
        self.assertTrue(result.requires_review)
        self.assertTrue(result.has_executable_resources)
        self.assertEqual(result.risky_resource_paths, ["scripts/process.py"])

    def test_markdown_with_blocked_resource_is_unsafe_blocked(self):
        result = inspect_markdown_instruction_skill("Use [secret](../secret.env).")

        self.assertFalse(result.is_safe)
        self.assertEqual(result.risk_level, "blocked")
        self.assertTrue(result.requires_review)
        self.assertEqual(result.blocked_resource_paths, ["../secret.env"])

    def test_real_secret_leak_is_unsafe_blocked(self):
        result = inspect_markdown_instruction_skill(
            "OPENAI_API_KEY=sk-abc123def456ghi789"
        )

        self.assertFalse(result.is_safe)
        self.assertEqual(result.risk_level, "blocked")
        self.assertTrue(any("secret" in error.lower() for error in result.errors))

    def test_private_key_block_is_unsafe_blocked(self):
        result = inspect_markdown_instruction_skill(
            "-----BEGIN RSA PRIVATE KEY-----\nabc\n-----END RSA PRIVATE KEY-----"
        )

        self.assertFalse(result.is_safe)
        self.assertEqual(result.risk_level, "blocked")
        self.assertTrue(any("private key block" in error.lower() for error in result.errors))

    def test_blocks_env_secret_credential_private_key_resource_references(self):
        result = inspect_markdown_instruction_skill(
            ".env credentials.json private.key id_rsa"
        )

        self.assertFalse(result.is_safe)
        self.assertEqual(result.risk_level, "blocked")
        self.assertEqual(
            result.blocked_resource_paths,
            [".env", "credentials.json", "private.key", "id_rsa"],
        )

    def test_empty_content_is_unsafe_blocked(self):
        result = inspect_markdown_instruction_skill("   ")

        self.assertFalse(result.is_safe)
        self.assertEqual(result.risk_level, "blocked")
        self.assertTrue(any("non-empty" in error for error in result.errors))

    def test_does_not_execute_or_fetch_anything(self):
        with patch("builtins.open", side_effect=AssertionError("open should not be called")), patch(
            "subprocess.run", side_effect=AssertionError("subprocess should not be called")
        ), patch("urllib.request.urlopen", side_effect=AssertionError("urlopen should not be called")):
            result = inspect_markdown_instruction_skill("Use [guide](docs/guide.md).")

        self.assertTrue(result.is_safe)
        self.assertEqual(result.risk_level, "medium")


if __name__ == "__main__":
    unittest.main()
