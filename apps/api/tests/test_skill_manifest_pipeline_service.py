import unittest
from unittest.mock import patch

from app.services.skill_manifest_pipeline_service import inspect_skill_manifest_content
from app.services.skill_manifest_validation_service import SkillManifestValidationResult


class SkillManifestPipelineServiceTest(unittest.TestCase):
    def test_valid_whole_json_manifest_returns_safe(self):
        result = inspect_skill_manifest_content(
            '{"name":"Email Summary","version":"1.0.0","description":"Generate summary."}'
        )

        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_extracted)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])
        self.assertEqual(result.source_format, "json")
        self.assertEqual(
            result.normalized_manifest,
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
            },
        )

    def test_valid_fenced_json_manifest_returns_safe(self):
        result = inspect_skill_manifest_content(
            "```json\n{\"name\":\"Email Summary\",\"version\":\"1.0.0\",\"description\":\"Generate summary.\"}\n```"
        )

        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_extracted)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.source_format, "markdown_json_fence")

    def test_extraction_failure_prevents_validation(self):
        with patch(
            "app.services.skill_manifest_pipeline_service.validate_skill_manifest",
            side_effect=AssertionError("validation should not run"),
        ) as mock_validate:
            result = inspect_skill_manifest_content("not json")

        self.assertFalse(result.is_safe)
        self.assertFalse(result.is_extracted)
        self.assertFalse(result.is_valid)
        self.assertIsNone(result.manifest)
        self.assertIsNone(result.normalized_manifest)
        self.assertTrue(any(error.startswith("extraction:") for error in result.errors))
        mock_validate.assert_not_called()

    def test_validation_failure_returns_unsafe(self):
        result = inspect_skill_manifest_content(
            '{"name":"Email Summary","version":"1.0.0","description":"Generate summary.","unexpected":"value"}'
        )

        self.assertFalse(result.is_safe)
        self.assertTrue(result.is_extracted)
        self.assertFalse(result.is_valid)
        self.assertIsNotNone(result.manifest)
        self.assertIsNone(result.normalized_manifest)
        self.assertTrue(any(error.startswith("validation:") for error in result.errors))

    def test_unknown_top_level_field_returns_validation_error(self):
        result = inspect_skill_manifest_content(
            '{"name":"Email Summary","version":"1.0.0","description":"Generate summary.","unexpected":"value"}'
        )

        self.assertFalse(result.is_safe)
        self.assertTrue(any("validation: Unknown top-level field: unexpected." in error for error in result.errors))

    def test_secret_marker_in_raw_content_returns_extraction_error(self):
        result = inspect_skill_manifest_content(
            '{"name":"Email Summary","description":"api_key=secret-value"}'
        )

        self.assertFalse(result.is_safe)
        self.assertFalse(result.is_extracted)
        self.assertFalse(result.is_valid)
        self.assertIsNone(result.manifest)
        self.assertTrue(any(error.startswith("extraction:") for error in result.errors))

    def test_execution_marker_in_raw_content_returns_extraction_error(self):
        result = inspect_skill_manifest_content(
            '{"name":"Email Summary","description":"Use curl to fetch data."}'
        )

        self.assertFalse(result.is_safe)
        self.assertFalse(result.is_extracted)
        self.assertFalse(result.is_valid)
        self.assertIsNone(result.manifest)
        self.assertTrue(any(error.startswith("extraction:") for error in result.errors))

    def test_invalid_domain_returns_validation_error(self):
        result = inspect_skill_manifest_content(
            '{"name":"Email Summary","version":"1.0.0","description":"Generate summary.","required_domains":["https://example.com"]}'
        )

        self.assertFalse(result.is_safe)
        self.assertTrue(result.is_extracted)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("validation:" in error for error in result.errors))

    def test_normalized_manifest_is_returned_on_success(self):
        result = inspect_skill_manifest_content(
            '{"name":" Email Summary ","version":" 1.0.0 ","description":" Generate summary. ","required_domains":["Example.COM"]}'
        )

        self.assertTrue(result.is_safe)
        self.assertEqual(
            result.normalized_manifest,
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
            },
        )

    def test_warnings_are_preserved(self):
        content = "# Skill Manifest\n\n```json\n{\"name\":\"Email Summary\",\"version\":\"1.0.0\",\"description\":\"Generate summary.\"}\n```"
        validation_result = SkillManifestValidationResult(
            is_valid=True,
            errors=[],
            warnings=["validation warning"],
            normalized_manifest={
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
            },
        )

        with patch(
            "app.services.skill_manifest_pipeline_service.validate_skill_manifest",
            return_value=validation_result,
        ):
            result = inspect_skill_manifest_content(content)

        self.assertIn("Skill manifest heading found.", result.warnings)
        self.assertIn("validation warning", result.warnings)

    def test_source_format_is_preserved(self):
        result = inspect_skill_manifest_content(
            "```json\n{\"name\":\"Email Summary\",\"version\":\"1.0.0\",\"description\":\"Generate summary.\"}\n```"
        )

        self.assertEqual(result.source_format, "markdown_json_fence")

    def test_input_content_is_not_mutated(self):
        content = '{"name":"Email Summary","version":"1.0.0","description":"Generate summary."}'
        original = content

        inspect_skill_manifest_content(content)

        self.assertEqual(content, original)


if __name__ == "__main__":
    unittest.main()
