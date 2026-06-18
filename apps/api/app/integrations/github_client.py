from dataclasses import dataclass
import re
from urllib.parse import urlparse

import httpx


MAX_CONTENT_BYTES = 200 * 1024
ALLOWED_TEXT_EXTENSIONS = {".md", ".markdown", ".txt"}
_RAW_GITHUB_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{7,40}$", re.IGNORECASE)
_GITHUB_API_BASE_URL = "https://api.github.com"
_GITHUB_USER_AGENT = "personal-ai-agent-workspace"


@dataclass(slots=True)
class GitHubRepositoryMetadata:
    repo_url: str
    owner: str
    repo: str
    default_branch: str | None
    description: str | None
    html_url: str | None


@dataclass(slots=True)
class GitHubPreviewFetchResult:
    raw_url: str
    content: str
    commit_sha: str | None
    source_identity: str | None
    source_identity_type: str | None


def _get_extension(file_path: str) -> str:
    lower_path = file_path.lower()
    last_dot = lower_path.rfind(".")
    if last_dot == -1:
        return ""
    return lower_path[last_dot:]


def build_raw_github_url(repo_url: str, branch: str | None, file_path: str) -> str:
    parsed = urlparse(repo_url)
    if parsed.netloc == "raw.githubusercontent.com":
        return repo_url

    if parsed.netloc != "github.com":
        raise ValueError("Only public GitHub URLs are supported.")

    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) < 2:
        raise ValueError("GitHub repository URL is invalid.")

    owner = path_parts[0]
    repo = path_parts[1]

    if len(path_parts) >= 5 and path_parts[2] == "blob":
        branch_name = path_parts[3]
        blob_file_path = "/".join(path_parts[4:])
        return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch_name}/{blob_file_path}"

    branch_name = branch or "main"
    normalized_file_path = file_path.lstrip("/")
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch_name}/{normalized_file_path}"


def fetch_repository_metadata(repo_url: str) -> GitHubRepositoryMetadata:
    owner, repo = _parse_github_repo_url(repo_url)
    api_url = f"{_GITHUB_API_BASE_URL}/repos/{owner}/{repo}"

    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        response = client.get(
            api_url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": _GITHUB_USER_AGENT,
            },
        )
        response.raise_for_status()
        payload = response.json()

    return GitHubRepositoryMetadata(
        repo_url=repo_url,
        owner=owner,
        repo=repo,
        default_branch=payload.get("default_branch"),
        description=payload.get("description"),
        html_url=payload.get("html_url"),
    )


def fetch_repository_tree(repo_url: str, branch: str | None) -> list[str]:
    owner, repo = _parse_github_repo_url(repo_url)
    branch_name = branch or "main"
    api_url = f"{_GITHUB_API_BASE_URL}/repos/{owner}/{repo}/git/trees/{branch_name}?recursive=1"

    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        response = client.get(
            api_url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": _GITHUB_USER_AGENT,
            },
        )
        response.raise_for_status()
        payload = response.json()

    tree = payload.get("tree")
    if not isinstance(tree, list):
        raise ValueError("GitHub repository tree response is invalid.")

    paths: list[str] = []
    for item in tree:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "blob":
            continue
        path = item.get("path")
        if isinstance(path, str) and path.strip():
            paths.append(path.strip())

    return paths


def fetch_text_preview(repo_url: str, branch: str | None, file_path: str) -> GitHubPreviewFetchResult:
    normalized_file_path = file_path.strip()
    if normalized_file_path.split("/")[-1].lower() != "skill.md":
        raise ValueError("Only SKILL.md files are supported in this step.")

    extension = _get_extension(normalized_file_path)
    if extension not in ALLOWED_TEXT_EXTENSIONS:
        raise ValueError("Only text-like Markdown files are supported.")

    raw_url = build_raw_github_url(repo_url, branch, normalized_file_path)

    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        response = client.get(raw_url, headers={"Accept": "text/plain"})
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()
        if "text" not in content_type and "markdown" not in content_type and "octet-stream" not in content_type:
            raise ValueError("Fetched file is not a supported text document.")

        content = response.text
        encoded_size = len(content.encode("utf-8"))
        if encoded_size > MAX_CONTENT_BYTES:
            raise ValueError("Fetched file exceeds the maximum preview size.")

        commit_sha = _extract_commit_sha_from_raw_url(raw_url)
        source_identity_type = None
        source_identity = None

        if commit_sha is not None:
            source_identity_type = "commit_sha"
            source_identity = commit_sha
        else:
            etag = _normalize_header_value(response.headers.get("etag"))
            if etag:
                source_identity_type = "etag"
                source_identity = etag
            else:
                last_modified = _normalize_header_value(response.headers.get("last-modified"))
                if last_modified:
                    source_identity_type = "last-modified"
                    source_identity = last_modified

    return GitHubPreviewFetchResult(
        raw_url=raw_url,
        content=content,
        commit_sha=commit_sha,
        source_identity=source_identity,
        source_identity_type=source_identity_type,
    )


def _parse_github_repo_url(repo_url: str) -> tuple[str, str]:
    parsed = urlparse(repo_url)
    if parsed.netloc != "github.com":
        raise ValueError("Only public GitHub URLs are supported.")

    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) < 2:
        raise ValueError("GitHub repository URL is invalid.")

    owner = path_parts[0]
    repo = path_parts[1]
    return owner, repo


def _extract_commit_sha_from_raw_url(raw_url: str) -> str | None:
    parsed = urlparse(raw_url)
    if parsed.netloc != "raw.githubusercontent.com":
        return None

    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) < 4:
        return None

    ref = path_parts[2]
    if _RAW_GITHUB_COMMIT_PATTERN.fullmatch(ref):
        return ref.lower()

    return None


def _normalize_header_value(value: str | None) -> str | None:
    if not value:
        return None

    normalized = value.strip().strip('"').strip("'")
    return normalized or None
