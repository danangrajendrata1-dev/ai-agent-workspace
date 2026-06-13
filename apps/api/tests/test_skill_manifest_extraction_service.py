import unittest

from app.services.skill_manifest_extraction_service import extract_skill_manifest_from_text


class SkillManifestExtractionServiceTest(unittest.TestCase):
    def test_extracts_whole_json_object(self):
        result = extract_skill_manifest_from_text(
            '{"name":"Email Summary","version":"1.0.0","description":"Short summary."}'
        )

        self.assertTrue(result.is_extracted)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])
        self.assertEqual(result.source_format, "json")
        self.assertEqual(
            result.manifest,
            {
                "name": "Email Summary",
                "version": "1.0.0",
                "description": "Short summary.",
            },
        )

    def test_extracts_fenced_json_object(self):
        result = extract_skill_manifest_from_text(
            "```json\n{\"name\":\"Email Summary\",\"version\":\"1.0.0\",\"description\":\"Short summary.\"}\n```"
        )

        self.assertTrue(result.is_extracted)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])
        self.assertEqual(result.source_format, "markdown_json_fence")
        self.assertEqual(
            result.manifest,
            {
                "name": "Email Summary",
                "version": "1.0.0",
                "description": "Short summary.",
            },
        )

    def test_extracts_fenced_json_object_under_skill_manifest_heading(self):
        result = extract_skill_manifest_from_text(
            "# Skill Manifest\n\n```json\n{\"name\":\"Email Summary\",\"version\":\"1.0.0\",\"description\":\"Short summary.\"}\n```"
        )

        self.assertTrue(result.is_extracted)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.source_format, "markdown_json_fence")
        self.assertEqual(
            result.manifest,
            {
                "name": "Email Summary",
                "version": "1.0.0",
                "description": "Short summary.",
            },
        )

    def test_rejects_empty_content(self):
        result = extract_skill_manifest_from_text("   ")

        self.assertFalse(result.is_extracted)
        self.assertIsNone(result.manifest)
        self.assertTrue(any("Content is empty." in error for error in result.errors))

    def test_rejects_non_string_input(self):
        result = extract_skill_manifest_from_text(None)  # type: ignore[arg-type]

        self.assertFalse(result.is_extracted)
        self.assertIsNone(result.manifest)
        self.assertTrue(any("Content must be a string." in error for error in result.errors))

    def test_rejects_json_array(self):
        result = extract_skill_manifest_from_text('["name","version"]')

        self.assertFalse(result.is_extracted)
        self.assertIsNone(result.manifest)
        self.assertTrue(any("JSON content must be an object." in error for error in result.errors))

    def test_rejects_invalid_json(self):
        result = extract_skill_manifest_from_text('{"name": "Email Summary",}')

        self.assertFalse(result.is_extracted)
        self.assertIsNone(result.manifest)
        self.assertTrue(any("No JSON manifest found." in error for error in result.errors))

    def test_rejects_unsupported_fenced_language_python(self):
        result = extract_skill_manifest_from_text(
            "```python\n{\"name\":\"Email Summary\"}\n```"
        )

        self.assertFalse(result.is_extracted)
        self.assertIsNone(result.manifest)
        self.assertTrue(any("Unsupported fenced code block language: python." in error for error in result.errors))

    def test_rejects_unsupported_fenced_language_bash(self):
        result = extract_skill_manifest_from_text(
            "```bash\n{\"name\":\"Email Summary\"}\n```"
        )

        self.assertFalse(result.is_extracted)
        self.assertIsNone(result.manifest)
        self.assertTrue(any("Unsupported fenced code block language: bash." in error for error in result.errors))

    def test_rejects_yaml_fenced_block(self):
        result = extract_skill_manifest_from_text(
            "```yaml\nname: Email Summary\n```"
        )

        self.assertFalse(result.is_extracted)
        self.assertIsNone(result.manifest)
        self.assertTrue(any("Unsupported fenced code block language: yaml." in error for error in result.errors))

    def test_rejects_multiple_json_fenced_blocks(self):
        result = extract_skill_manifest_from_text(
            "```json\n{\"name\":\"Email Summary\"}\n```\n\n```json\n{\"name\":\"Other\"}\n```"
        )

        self.assertFalse(result.is_extracted)
        self.assertIsNone(result.manifest)
        self.assertTrue(any("Exactly one JSON fenced block is required." in error for error in result.errors))

    def test_rejects_content_with_execution_instruction(self):
        result = extract_skill_manifest_from_text(
            '{"name":"Email Summary","description":"Use curl to fetch data."}'
        )

        self.assertFalse(result.is_extracted)
        self.assertIsNone(result.manifest)
        self.assertTrue(any("forbidden execution marker" in error for error in result.errors))

    def test_rejects_content_with_secret_marker(self):
        result = extract_skill_manifest_from_text(
            '{"name":"Email Summary","description":"api_key=secret-value"}'
        )

        self.assertFalse(result.is_extracted)
        self.assertIsNone(result.manifest)
        self.assertTrue(any("forbidden secret marker" in error for error in result.errors))

    def test_rejects_content_exceeding_max_length(self):
        result = extract_skill_manifest_from_text("{" + "a" * 200_001 + "}")

        self.assertFalse(result.is_extracted)
        self.assertIsNone(result.manifest)
        self.assertTrue(any("maximum length" in error for error in result.errors))

    def test_does_not_validate_manifest_fields_only_extracts_dict(self):
        result = extract_skill_manifest_from_text(
            '{"name":"Email Summary","version":"1.0.0","description":"Short summary.","unexpected":"value"}'
        )

        self.assertTrue(result.is_extracted)
        self.assertEqual(result.source_format, "json")
        self.assertEqual(result.manifest["unexpected"], "value")
        self.assertEqual(result.errors, [])


if __name__ == "__main__":
    unittest.main()
