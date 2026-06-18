import json
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from app.core.security import create_access_token


def auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=str(user_id))}"}


def test_collection_preview_returns_multiple_candidates(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    repo_url = "https://github.com/ComposioHQ/awesome-codex-skills"
    repository = SimpleNamespace(
        repo_url=repo_url,
        owner="ComposioHQ",
        repo="awesome-codex-skills",
        default_branch="main",
        description="Collection of safe skills.",
        html_url=repo_url,
    )
    tree_paths = [
        "skills/canvas-design/SKILL.md",
        "skills/pdf/SKILL.md",
        "README.md",
    ]
    fetch_results = {
        "skills/canvas-design/SKILL.md": SimpleNamespace(
            raw_url="https://raw.githubusercontent.com/ComposioHQ/awesome-codex-skills/main/skills/canvas-design/SKILL.md",
            content='{"name":"Canvas Design","version":"1.0.0","description":"Create design drafts."}',
            commit_sha=None,
            source_identity=None,
            source_identity_type=None,
        ),
        "skills/pdf/SKILL.md": SimpleNamespace(
            raw_url="https://raw.githubusercontent.com/ComposioHQ/awesome-codex-skills/main/skills/pdf/SKILL.md",
            content='{"name":"PDF Review","version":"1.0.0","description":"Review PDFs safely."}',
            commit_sha=None,
            source_identity=None,
            source_identity_type=None,
        ),
    }

    def fetch_preview_side_effect(repo_url, branch, file_path):
        return fetch_results[file_path]

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.github_import_service.fetch_repository_metadata",
        return_value=repository,
    ), patch(
        "app.services.github_import_service.fetch_repository_tree",
        return_value=tree_paths,
    ), patch(
        "app.services.github_import_service.fetch_text_preview",
        side_effect=fetch_preview_side_effect,
    ):
        response = client.post(
            "/github-imports/skills/collection-preview",
            headers=auth_headers(user.id),
            json={"repo_url": repo_url, "branch": "main"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_collection"] is True
    assert payload["candidate_count"] == 2
    assert payload["repository"]["owner"] == "ComposioHQ"
    assert payload["repository"]["repo"] == "awesome-codex-skills"
    assert len(payload["candidates"]) == 2
    assert {candidate["path"] for candidate in payload["candidates"]} == {
        "skills/canvas-design",
        "skills/pdf",
    }
    assert "token" not in json.dumps(payload).lower()
    assert "api_key" not in json.dumps(payload).lower()
    assert "secret" not in json.dumps(payload).lower()


def test_selected_skill_import_requires_skill_path(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    repo_url = "https://github.com/ComposioHQ/awesome-codex-skills"

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.github_import_service.fetch_text_preview",
        side_effect=AssertionError("fetch must not run when skill_path is missing"),
    ):
        response = client.post(
            "/github-imports/skills/import-selected",
            headers=auth_headers(user.id),
            json={"repo_url": repo_url, "branch": "main"},
        )

    assert response.status_code == 400
    assert "skill_path" in response.json()["detail"].lower()


def test_selected_skill_import_rejects_traversal_skill_path(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    repo_url = "https://github.com/ComposioHQ/awesome-codex-skills"

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.github_import_service.fetch_text_preview",
        side_effect=AssertionError("fetch must not run for traversal paths"),
    ):
        response = client.post(
            "/github-imports/skills/import-selected",
            headers=auth_headers(user.id),
            json={"repo_url": repo_url, "branch": "main", "skill_path": "../secret"},
        )

    assert response.status_code == 400
    assert "relative folder path" in response.json()["detail"].lower()


def test_selected_skill_import_rejects_absolute_skill_path(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    repo_url = "https://github.com/ComposioHQ/awesome-codex-skills"

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.github_import_service.fetch_text_preview",
        side_effect=AssertionError("fetch must not run for absolute paths"),
    ):
        response = client.post(
            "/github-imports/skills/import-selected",
            headers=auth_headers(user.id),
            json={"repo_url": repo_url, "branch": "main", "skill_path": "/etc/passwd"},
        )

    assert response.status_code == 400
    assert "relative folder path" in response.json()["detail"].lower()


def test_selected_skill_import_creates_preview_for_selected_folder(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    repo_url = "https://github.com/ComposioHQ/awesome-codex-skills"
    manifest_path = "skills/pdf/SKILL.md"
    manifest_content = '{"name":"PDF Review","version":"1.0.0","description":"Review PDFs safely."}'
    created_at = datetime.now(timezone.utc)
    import_record = SimpleNamespace(
        id=uuid.uuid4(),
        repo_url=repo_url,
        branch="main",
        commit_sha=None,
        import_type="skill",
        file_path=manifest_path,
        content_preview=manifest_content,
        status="preview",
        review_notes=None,
        created_at=created_at,
        updated_at=created_at,
    )

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.github_import_service.fetch_text_preview",
        return_value=SimpleNamespace(
            raw_url=f"https://raw.githubusercontent.com/ComposioHQ/awesome-codex-skills/main/{manifest_path}",
            content=manifest_content,
            commit_sha=None,
            source_identity=None,
            source_identity_type=None,
        ),
    ) as mock_fetch_text_preview, patch(
        "app.services.github_import_service.github_import_repository.create_preview",
        return_value=import_record,
    ) as mock_create_preview, patch(
        "app.services.github_import_service.skill_repository.create",
        side_effect=AssertionError("selected import must not create a skill yet"),
    ), patch(
        "app.services.github_import_service.github_import_repository.update_status",
        side_effect=AssertionError("selected import must not auto-approve"),
    ), patch(
        "app.services.github_import_service.github_import_repository.update_review_notes",
        side_effect=AssertionError("selected import must not auto-approve"),
    ), patch(
        "app.services.github_import_service.log_service.record_activity",
    ), patch(
        "sqlalchemy.orm.session.Session.refresh",
        autospec=True,
        return_value=None,
    ):
        response = client.post(
            "/github-imports/skills/import-selected",
            headers=auth_headers(user.id),
            json={"repo_url": repo_url, "branch": "main", "skill_path": "skills/pdf"},
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["file_path"] == manifest_path
    assert payload["repo_url"] == repo_url
    mock_fetch_text_preview.assert_called_once_with(repo_url, "main", manifest_path)
    mock_create_preview.assert_called_once()
    assert "token" not in json.dumps(payload).lower()
    assert "api_key" not in json.dumps(payload).lower()
    assert "secret" not in json.dumps(payload).lower()


def test_selected_skill_import_preview_does_not_expose_secrets(client):
    user = SimpleNamespace(id=uuid.uuid4(), role="user")
    repo_url = "https://github.com/ComposioHQ/awesome-codex-skills"
    repository = SimpleNamespace(
        repo_url=repo_url,
        owner="ComposioHQ",
        repo="awesome-codex-skills",
        default_branch="main",
        description="Collection of safe skills.",
        html_url=repo_url,
    )

    with patch("app.services.auth_service.get_current_active_user", return_value=user), patch(
        "app.services.github_import_service.fetch_repository_metadata",
        return_value=repository,
    ), patch(
        "app.services.github_import_service.fetch_repository_tree",
        return_value=["skills/pdf/SKILL.md"],
    ), patch(
        "app.services.github_import_service.fetch_text_preview",
        return_value=SimpleNamespace(
            raw_url="https://raw.githubusercontent.com/ComposioHQ/awesome-codex-skills/main/skills/pdf/SKILL.md",
            content='{"name":"PDF Review","version":"1.0.0","description":"Review PDFs safely."}',
            commit_sha=None,
            source_identity=None,
            source_identity_type=None,
        ),
    ):
        response = client.post(
            "/github-imports/skills/collection-preview",
            headers=auth_headers(user.id),
            json={"repo_url": repo_url, "branch": "main"},
        )

    payload = response.json()
    assert response.status_code == 200
    assert "token" not in json.dumps(payload).lower()
    assert "api_key" not in json.dumps(payload).lower()
    assert "secret" not in json.dumps(payload).lower()
