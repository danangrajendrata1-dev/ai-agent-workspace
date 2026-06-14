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

    def test_markdown_with_secret_marker_is_unsafe_blocked(self):
        result = inspect_markdown_instruction_skill(
            "API_KEY = super-secret-value"
        )

        self.assertFalse(result.is_safe)
        self.assertEqual(result.risk_level, "blocked")
        self.assertTrue(any("secret" in error.lower() for error in result.errors))

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
