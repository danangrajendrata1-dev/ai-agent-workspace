import unittest
from unittest.mock import patch

from app.services.skill_resource_detection_service import (
    detect_skill_resource_references,
)


class SkillResourceDetectionServiceTest(unittest.TestCase):
    def test_detects_markdown_links(self):
        result = detect_skill_resource_references("[template](templates/example.docx)")

        self.assertEqual(result.resource_paths, ["templates/example.docx"])
        self.assertEqual(result.safe_resource_paths, ["templates/example.docx"])
        self.assertEqual(result.risky_resource_paths, [])
        self.assertEqual(result.blocked_resource_paths, [])

    def test_detects_markdown_images(self):
        result = detect_skill_resource_references("![diagram](assets/diagram.png)")

        self.assertEqual(result.resource_paths, ["assets/diagram.png"])
        self.assertEqual(result.safe_resource_paths, ["assets/diagram.png"])

    def test_detects_inline_resource_paths(self):
        result = detect_skill_resource_references(
            "Use templates/report.docx and scripts/process.py in the same guide."
        )

        self.assertEqual(result.resource_paths, ["templates/report.docx", "scripts/process.py"])
        self.assertEqual(result.safe_resource_paths, ["templates/report.docx"])
        self.assertEqual(result.risky_resource_paths, ["scripts/process.py"])

    def test_deduplicates_paths(self):
        result = detect_skill_resource_references(
            "[template](templates/example.docx) and templates/example.docx again."
        )

        self.assertEqual(result.resource_paths, ["templates/example.docx"])

    def test_classifies_safe_resources(self):
        result = detect_skill_resource_references(
            "[data](assets/sample.csv) [spec](docs/spec.json) [guide](docs/guide.md)"
        )

        self.assertEqual(
            result.safe_resource_paths,
            ["assets/sample.csv", "docs/spec.json", "docs/guide.md"],
        )
        self.assertFalse(result.requires_review)
        self.assertFalse(result.has_executable_resources)

    def test_classifies_risky_executable_resources(self):
        result = detect_skill_resource_references(
            "[script](scripts/process.py) and [shell](scripts/run.sh)"
        )

        self.assertEqual(result.risky_resource_paths, ["scripts/process.py", "scripts/run.sh"])
        self.assertTrue(result.requires_review)
        self.assertTrue(result.has_executable_resources)

    def test_blocks_parent_directory_traversal(self):
        result = detect_skill_resource_references("[secret](../secret.env)")

        self.assertEqual(result.blocked_resource_paths, ["../secret.env"])
        self.assertTrue(result.requires_review)
        self.assertIn("../secret.env", result.resource_paths)

    def test_blocks_absolute_paths(self):
        result = detect_skill_resource_references("[secret](/secrets/token.txt)")

        self.assertEqual(result.blocked_resource_paths, ["/secrets/token.txt"])
        self.assertTrue(result.requires_review)

    def test_blocks_external_urls(self):
        result = detect_skill_resource_references("[script](https://example.com/file.py)")

        self.assertEqual(result.blocked_resource_paths, ["https://example.com/file.py"])
        self.assertTrue(result.requires_review)
        self.assertTrue(result.has_executable_resources)

    def test_blocks_file_urls(self):
        result = detect_skill_resource_references("file:///etc/passwd")

        self.assertEqual(result.blocked_resource_paths, ["file:///etc/passwd"])
        self.assertTrue(result.requires_review)

    def test_blocks_env_secret_credential_private_key_filenames(self):
        result = detect_skill_resource_references(
            ".env credentials.json keys/private.pem token.json"
        )

        self.assertEqual(
            result.blocked_resource_paths,
            [".env", "credentials.json", "keys/private.pem", "token.json"],
        )
        self.assertTrue(result.requires_review)

    def test_sets_requires_review_correctly(self):
        safe_result = detect_skill_resource_references("[doc](docs/readme.md)")
        risky_result = detect_skill_resource_references("[script](scripts/run.sh)")

        self.assertFalse(safe_result.requires_review)
        self.assertTrue(risky_result.requires_review)

    def test_sets_has_executable_resources_correctly(self):
        result = detect_skill_resource_references("[script](scripts/process.py)")

        self.assertTrue(result.has_executable_resources)

    def test_handles_empty_content_safely(self):
        result = detect_skill_resource_references("   ")

        self.assertEqual(result.resource_paths, [])
        self.assertEqual(result.safe_resource_paths, [])
        self.assertEqual(result.risky_resource_paths, [])
        self.assertEqual(result.blocked_resource_paths, [])
        self.assertEqual(result.warnings, [])
        self.assertFalse(result.has_executable_resources)
        self.assertFalse(result.requires_review)

    def test_does_not_execute_or_fetch_anything(self):
        with patch("builtins.open", side_effect=AssertionError("open should not be called")), patch(
            "subprocess.run", side_effect=AssertionError("subprocess should not be called")
        ), patch("urllib.request.urlopen", side_effect=AssertionError("urlopen should not be called")):
            result = detect_skill_resource_references("[doc](docs/readme.md)")

        self.assertEqual(result.resource_paths, ["docs/readme.md"])
        self.assertFalse(result.requires_review)


if __name__ == "__main__":
    unittest.main()
