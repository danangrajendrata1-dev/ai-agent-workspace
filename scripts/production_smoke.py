#!/usr/bin/env python3
"""Production smoke helper for Personal AI Agent Workspace v2.1.

Default mode is read-only. Mutating checks need --with-mutations and a disposable
test tenant. The script never prints raw secrets.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_TIMEOUT = 20
PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"


@dataclass
class SmokeResult:
    name: str
    status: str
    detail: str


@dataclass
class SmokeConfig:
    api_base_url: str
    web_base_url: str | None
    cors_origin: str | None
    login_email: str | None
    login_password: str | None
    register_email: str | None
    register_password: str | None
    register_display_name: str | None
    agent_name: str
    agent_slug: str
    agent_description: str
    agent_role_description: str
    agent_instruction_text: str
    model_provider_id: str | None
    model_name: str
    github_repo_url: str | None
    github_branch: str | None
    github_file_path: str | None
    github_collection_repo_url: str | None
    github_collection_branch: str | None
    github_skill_name: str
    github_skill_slug: str
    github_skill_version: str
    github_skill_review_notes: str
    provider_name: str
    provider_api_key: str | None
    with_mutations: bool


def env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return default
    stripped = value.strip()
    return stripped if stripped else default


def must_env(name: str) -> str:
    value = env(name)
    if not value:
        raise SystemExit(f"Missing required env: {name}")
    return value


def build_url(base_url: str, path: str) -> str:
    base = base_url.rstrip("/")
    suffix = path if path.startswith("/") else f"/{path}"
    return f"{base}{suffix}"


def redact(text: str, secrets: list[str]) -> str:
    masked = text
    for secret in sorted({s for s in secrets if s}, key=len, reverse=True):
        masked = masked.replace(secret, "[REDACTED]")
    return masked


def parse_body(text: str) -> Any:
    if not text:
        return ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def response_message(payload: Any) -> str:
    if isinstance(payload, dict):
        for key in ("detail", "message", "error_message", "error"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return json.dumps(payload, sort_keys=True)
    if isinstance(payload, str):
        return payload.strip()
    return str(payload)


def http_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    origin: str | None = None,
    extra_headers: dict[str, str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> tuple[int, dict[str, str], Any]:
    headers = {
        "Accept": "application/json",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if origin:
        headers["Origin"] = origin
    if extra_headers:
        headers.update(extra_headers)

    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method, headers=headers)

    try:
      with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", "replace")
            return response.status, dict(response.headers.items()), parse_body(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        return exc.code, dict(exc.headers.items()), parse_body(raw)


def make_config(args: argparse.Namespace) -> SmokeConfig:
    api_base_url = must_env("SMOKE_API_BASE_URL")
    web_base_url = env("SMOKE_WEB_BASE_URL")
    cors_origin = env("SMOKE_CORS_ORIGIN")

    login_email = env("SMOKE_LOGIN_EMAIL", env("SMOKE_REGISTER_EMAIL"))
    login_password = env("SMOKE_LOGIN_PASSWORD", env("SMOKE_REGISTER_PASSWORD"))
    register_email = env("SMOKE_REGISTER_EMAIL")
    register_password = env("SMOKE_REGISTER_PASSWORD")
    register_display_name = env("SMOKE_REGISTER_DISPLAY_NAME")

    github_repo_url = env("SMOKE_GITHUB_REPO_URL")
    github_branch = env("SMOKE_GITHUB_BRANCH")
    github_file_path = env("SMOKE_GITHUB_FILE_PATH")
    github_collection_repo_url = env("SMOKE_GITHUB_COLLECTION_REPO_URL", github_repo_url)
    github_collection_branch = env("SMOKE_GITHUB_COLLECTION_BRANCH", github_branch)

    return SmokeConfig(
        api_base_url=api_base_url,
        web_base_url=web_base_url,
        cors_origin=cors_origin,
        login_email=login_email,
        login_password=login_password,
        register_email=register_email,
        register_password=register_password,
        register_display_name=register_display_name,
        agent_name=env("SMOKE_AGENT_NAME", "Production Smoke Agent") or "Production Smoke Agent",
        agent_slug=env("SMOKE_AGENT_SLUG", "production-smoke-agent") or "production-smoke-agent",
        agent_description=env("SMOKE_AGENT_DESCRIPTION", "Smoke test agent.") or "Smoke test agent.",
        agent_role_description=env("SMOKE_AGENT_ROLE_DESCRIPTION", "Production smoke role.") or "Production smoke role.",
        agent_instruction_text=env("SMOKE_AGENT_INSTRUCTION_TEXT", "Smoke only. No execution.") or "Smoke only. No execution.",
        model_provider_id=env("SMOKE_MODEL_PROVIDER_ID"),
        model_name=env("SMOKE_MODEL_NAME", "gpt-4o") or "gpt-4o",
        github_repo_url=github_repo_url,
        github_branch=github_branch,
        github_file_path=github_file_path,
        github_collection_repo_url=github_collection_repo_url,
        github_collection_branch=github_collection_branch,
        github_skill_name=env("SMOKE_GITHUB_SKILL_NAME", "Production Smoke Skill") or "Production Smoke Skill",
        github_skill_slug=env("SMOKE_GITHUB_SKILL_SLUG", "production-smoke-skill") or "production-smoke-skill",
        github_skill_version=env("SMOKE_GITHUB_SKILL_VERSION", "smoke") or "smoke",
        github_skill_review_notes=env("SMOKE_GITHUB_REVIEW_NOTES", "production smoke approval") or "production smoke approval",
        provider_name=env("SMOKE_PROVIDER_NAME", "openai") or "openai",
        provider_api_key=env("SMOKE_PROVIDER_API_KEY"),
        with_mutations=bool(args.with_mutations),
    )


def log_step(results: list[SmokeResult], name: str, status: str, detail: str) -> None:
    results.append(SmokeResult(name=name, status=status, detail=detail))
    print(f"[{status}] {name}: {detail}")


def skip(results: list[SmokeResult], name: str, detail: str) -> None:
    log_step(results, name, SKIP, detail)


def fail(results: list[SmokeResult], name: str, detail: str) -> None:
    log_step(results, name, FAIL, detail)


def check_ok(results: list[SmokeResult], name: str, detail: str) -> None:
    log_step(results, name, PASS, detail)


def check_health(cfg: SmokeConfig, results: list[SmokeResult]) -> None:
    status, _, body = http_json("GET", build_url(cfg.api_base_url, "/health"))
    if status != 200:
        fail(results, "Backend health", f"GET /health returned {status}.")
        return

    if isinstance(body, dict) and body.get("status") not in (None, "healthy", "ok", "pass"):
        fail(results, "Backend health", f"Unexpected health payload: {response_message(body)}")
        return

    check_ok(results, "Backend health", "GET /health returned 200.")


def check_frontend_load(cfg: SmokeConfig, results: list[SmokeResult]) -> None:
    if not cfg.web_base_url:
        skip(results, "Frontend loads", "SMOKE_WEB_BASE_URL missing.")
        return

    checks = ["/login", "/register"]
    if env("SMOKE_CHECK_DASHBOARD", "1") == "1":
        checks.append("/dashboard")

    for path in checks:
        status, _, _ = http_json("GET", build_url(cfg.web_base_url, path))
        if status not in (200, 301, 302, 307, 308):
            fail(results, f"Frontend loads {path}", f"GET {path} returned {status}.")
            return
        if path in ("/login", "/register") and status != 200:
            fail(results, f"Frontend loads {path}", f"GET {path} returned {status}, expected 200.")
            return

    check_ok(results, "Frontend loads", "Login, register, and dashboard routes responded.")


def auth_headers(token: str | None) -> dict[str, str]:
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def register_user(cfg: SmokeConfig, results: list[SmokeResult]) -> dict[str, Any] | None:
    if not cfg.with_mutations:
        skip(results, "Register smoke", "--with-mutations not set.")
        return None

    if not (cfg.register_email and cfg.register_password and cfg.register_display_name):
        skip(results, "Register smoke", "Register env missing.")
        return None

    payload = {
        "email": cfg.register_email,
        "password": cfg.register_password,
        "display_name": cfg.register_display_name,
    }
    status, _, body = http_json("POST", build_url(cfg.api_base_url, "/auth/register"), payload=payload)
    if status != 201:
        fail(results, "Register smoke", f"POST /auth/register returned {status}: {response_message(body)}")
        return None

    check_ok(results, "Register smoke", f"Registered {cfg.register_email}.")
    return body if isinstance(body, dict) else None


def login_user(cfg: SmokeConfig, results: list[SmokeResult]) -> str | None:
    if not (cfg.login_email and cfg.login_password):
        skip(results, "Login smoke", "Login env missing.")
        return None

    payload = {"email": cfg.login_email, "password": cfg.login_password}
    status, _, body = http_json("POST", build_url(cfg.api_base_url, "/auth/login"), payload=payload)
    if status != 200 or not isinstance(body, dict) or not body.get("access_token"):
        fail(results, "Login smoke", f"POST /auth/login returned {status}: {response_message(body)}")
        return None

    token = str(body["access_token"])
    check_ok(results, "Login smoke", "Bearer token returned.")
    return token


def auth_me(cfg: SmokeConfig, results: list[SmokeResult], token: str | None) -> dict[str, Any] | None:
    if not token:
        skip(results, "/auth/me smoke", "No token.")
        return None

    status, _, body = http_json("GET", build_url(cfg.api_base_url, "/auth/me"), token=token)
    if status != 200 or not isinstance(body, dict):
        fail(results, "/auth/me smoke", f"GET /auth/me returned {status}: {response_message(body)}")
        return None

    if any(key not in body for key in ("id", "email", "display_name", "role", "subscription_plan")):
        fail(results, "/auth/me smoke", f"Missing fields: {response_message(body)}")
        return None

    check_ok(results, "/auth/me smoke", f"Current user {body.get('email')} returned.")
    return body


def create_agent(cfg: SmokeConfig, results: list[SmokeResult], token: str | None) -> dict[str, Any] | None:
    if not cfg.with_mutations:
        skip(results, "Create agent smoke", "--with-mutations not set.")
        return None
    if not token:
        skip(results, "Create agent smoke", "Login token missing.")
        return None

    payload = {
        "name": cfg.agent_name,
        "slug": cfg.agent_slug,
        "description": cfg.agent_description,
        "role_description": cfg.agent_role_description,
        "default_model_provider_id": cfg.model_provider_id,
        "default_model_name": cfg.model_name,
        "status": "active",
        "max_steps": 3,
        "max_runtime_seconds": 120,
        "max_token_budget": 1000,
        "requires_approval_by_default": False,
        "instruction_text": cfg.agent_instruction_text,
    }
    status, _, body = http_json("POST", build_url(cfg.api_base_url, "/agents"), token=token, payload=payload)
    if status != 201 or not isinstance(body, dict) or not body.get("id"):
        fail(results, "Create agent smoke", f"POST /agents returned {status}: {response_message(body)}")
        return None

    agent_id = str(body["id"])
    status, _, detail = http_json("GET", build_url(cfg.api_base_url, f"/agents/{agent_id}"), token=token)
    if status != 200 or not isinstance(detail, dict):
        fail(results, "Agent detail smoke", f"GET /agents/{agent_id} returned {status}: {response_message(detail)}")
        return None

    status, _, listing = http_json("GET", build_url(cfg.api_base_url, "/agents"), token=token)
    if status != 200 or not isinstance(listing, dict):
        fail(results, "Agent list smoke", f"GET /agents returned {status}: {response_message(listing)}")
        return None

    items = listing.get("items") if isinstance(listing.get("items"), list) else []
    if not any(str(item.get("id")) == agent_id for item in items if isinstance(item, dict)):
        fail(results, "Agent list smoke", "Created agent not found in list response.")
        return None

    check_ok(results, "Create agent smoke", f"Created agent {agent_id}.")
    return body


def github_preview(cfg: SmokeConfig, results: list[SmokeResult], token: str | None) -> dict[str, Any] | None:
    if not token:
        skip(results, "GitHub skill preview smoke", "Login token missing.")
        return None
    if not (cfg.github_repo_url and cfg.github_file_path):
        skip(results, "GitHub skill preview smoke", "GitHub preview env missing.")
        return None

    payload = {
        "repo_url": cfg.github_repo_url,
        "branch": cfg.github_branch,
        "file_path": cfg.github_file_path,
    }
    status, _, body = http_json("POST", build_url(cfg.api_base_url, "/github-imports/skills/preview"), token=token, payload=payload)
    if status != 201 or not isinstance(body, dict) or not body.get("id"):
        fail(results, "GitHub skill preview smoke", f"POST /github-imports/skills/preview returned {status}: {response_message(body)}")
        return None

    check_ok(results, "GitHub skill preview smoke", "Preview metadata returned.")
    return body


def github_collection_preview(cfg: SmokeConfig, results: list[SmokeResult], token: str | None) -> dict[str, Any] | None:
    if not token:
        skip(results, "Collection preview smoke", "Login token missing.")
        return None
    if not cfg.github_collection_repo_url:
        skip(results, "Collection preview smoke", "Collection preview repo missing.")
        return None

    payload = {
        "repo_url": cfg.github_collection_repo_url,
        "branch": cfg.github_collection_branch,
    }
    status, _, body = http_json("POST", build_url(cfg.api_base_url, "/github-imports/skills/collection-preview"), token=token, payload=payload)
    if status != 200 or not isinstance(body, dict) or not body.get("repository"):
        fail(results, "Collection preview smoke", f"POST /github-imports/skills/collection-preview returned {status}: {response_message(body)}")
        return None

    check_ok(results, "Collection preview smoke", "Collection preview returned safely.")
    return body


def import_selected_skill(cfg: SmokeConfig, results: list[SmokeResult], token: str | None) -> dict[str, Any] | None:
    if not cfg.with_mutations:
        skip(results, "Import selected skill smoke", "--with-mutations not set.")
        return None
    if not token:
        skip(results, "Import selected skill smoke", "Login token missing.")
        return None
    if not cfg.github_repo_url:
        skip(results, "Import selected skill smoke", "GitHub import env missing.")
        return None

    payload = {
        "repo_url": cfg.github_repo_url,
        "branch": cfg.github_branch,
        "skill_path": cfg.github_file_path,
    }
    status, _, body = http_json("POST", build_url(cfg.api_base_url, "/github-imports/skills/import-selected"), token=token, payload=payload)
    if status != 201 or not isinstance(body, dict) or not body.get("id"):
        fail(results, "Import selected skill smoke", f"POST /github-imports/skills/import-selected returned {status}: {response_message(body)}")
        return None

    check_ok(results, "Import selected skill smoke", f"Import record {body.get('id')} created.")
    return body


def approve_skill(cfg: SmokeConfig, results: list[SmokeResult], token: str | None, import_record: dict[str, Any] | None) -> dict[str, Any] | None:
    if not cfg.with_mutations:
        skip(results, "Approve skill smoke", "--with-mutations not set.")
        return None
    if not token or not import_record or not import_record.get("id"):
        skip(results, "Approve skill smoke", "Import record missing.")
        return None

    import_id = str(import_record["id"])
    payload = {
        "name": cfg.github_skill_name,
        "slug": cfg.github_skill_slug,
        "description": "Production smoke approved skill.",
        "version_label": cfg.github_skill_version,
        "risk_level": "medium",
        "status": "active",
        "review_notes": cfg.github_skill_review_notes,
    }
    status, _, body = http_json("POST", build_url(cfg.api_base_url, f"/github-imports/{import_id}/approve-skill"), token=token, payload=payload)
    if status != 200 or not isinstance(body, dict) or str(body.get("status")) != "imported":
        fail(results, "Approve skill smoke", f"POST /github-imports/{import_id}/approve-skill returned {status}: {response_message(body)}")
        return None

    check_ok(results, "Approve skill smoke", f"Import {import_id} approved.")
    return body


def attach_skill(cfg: SmokeConfig, results: list[SmokeResult], token: str | None, agent: dict[str, Any] | None, approved_import: dict[str, Any] | None) -> dict[str, Any] | None:
    if not cfg.with_mutations:
        skip(results, "Attach skill smoke", "--with-mutations not set.")
        return None
    if not token or not agent or not agent.get("id") or not approved_import:
        skip(results, "Attach skill smoke", "Agent or approved import missing.")
        return None
    if not (cfg.github_skill_name and cfg.github_skill_slug):
        skip(results, "Attach skill smoke", "Skill lookup values missing.")
        return None

    status, _, library = http_json("GET", build_url(cfg.api_base_url, "/skills/library"), token=token)
    if status != 200 or not isinstance(library, dict):
        fail(results, "Attach skill smoke", f"GET /skills/library returned {status}: {response_message(library)}")
        return None

    items = library.get("items") if isinstance(library.get("items"), list) else []
    selected_item = None
    for item in items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "")
        source_ref = str(item.get("source_reference") or "")
        file_path = str(item.get("file_path") or "")
        if cfg.github_skill_name.lower() in title.lower() or cfg.github_file_path and cfg.github_file_path == file_path or cfg.github_file_path and cfg.github_file_path == source_ref:
            selected_item = item
            break

    if not selected_item or not selected_item.get("id"):
        fail(results, "Attach skill smoke", "Approved skill not found in library.")
        return None

    skill_id = str(selected_item["id"])
    status, _, body = http_json("POST", build_url(cfg.api_base_url, f"/agents/{agent['id']}/skills/imported/{skill_id}"), token=token)
    if status not in (200, 201) or not isinstance(body, dict):
        fail(results, "Attach skill smoke", f"POST /agents/{agent['id']}/skills/imported/{skill_id} returned {status}: {response_message(body)}")
        return None

    status, _, active = http_json("GET", build_url(cfg.api_base_url, f"/agents/{agent['id']}/active-skills"), token=token)
    if status != 200 or not isinstance(active, dict):
        fail(results, "Active skill visible smoke", f"GET /agents/{agent['id']}/active-skills returned {status}: {response_message(active)}")
        return None

    active_items = active.get("items") if isinstance(active.get("items"), list) else []
    if not any(str(item.get("skill_id")) == skill_id for item in active_items if isinstance(item, dict)):
        fail(results, "Active skill visible smoke", "Attached skill not visible in active skills.")
        return None

    status, _, detached = http_json("DELETE", build_url(cfg.api_base_url, f"/agents/{agent['id']}/skills/imported/{skill_id}"), token=token)
    if status not in (200, 204):
        fail(results, "Detach skill smoke", f"DELETE /agents/{agent['id']}/skills/imported/{skill_id} returned {status}: {response_message(detached)}")
        return None

    check_ok(results, "Attach skill smoke", f"Attached skill {skill_id} to agent {agent['id']}.")
    check_ok(results, "Detach skill smoke", f"Detached skill {skill_id} from agent {agent['id']}.")
    return selected_item


def provider_key_smoke(cfg: SmokeConfig, results: list[SmokeResult], token: str | None) -> None:
    if not cfg.with_mutations:
        skip(results, "Provider key save smoke", "--with-mutations not set.")
        return
    if not token:
        skip(results, "Provider key save smoke", "Login token missing.")
        return
    if not cfg.provider_api_key:
        skip(results, "Provider key save smoke", "Provider API key env missing.")
        return

    status, _, body = http_json(
        "PUT",
        build_url(cfg.api_base_url, f"/model-provider-keys/{cfg.provider_name}"),
        token=token,
        payload={"api_key": cfg.provider_api_key},
    )
    if status != 200 or not isinstance(body, dict):
        fail(results, "Provider key save smoke", f"PUT /model-provider-keys/{cfg.provider_name} returned {status}: {response_message(body)}")
        return

    masked = str(body.get("masked_key") or body.get("key_last4") or "")
    if cfg.provider_api_key in masked:
        fail(results, "Masked key visible smoke", "Masked key leaked raw secret.")
        return
    if isinstance(body, dict) and body.get("api_key") is not None:
        fail(results, "Masked key visible smoke", "Raw api_key field leaked in save response.")
        return

    status, _, status_body = http_json("GET", build_url(cfg.api_base_url, f"/model-provider-keys/{cfg.provider_name}"), token=token)
    if status != 200 or not isinstance(status_body, dict):
        fail(results, "Masked key visible smoke", f"GET /model-provider-keys/{cfg.provider_name} returned {status}: {response_message(status_body)}")
        return

    masked_status = str(status_body.get("masked_key") or status_body.get("key_last4") or "")
    if cfg.provider_api_key in masked_status:
        fail(results, "Raw key not visible smoke", "Raw provider key leaked in status response.")
        return
    if status_body.get("api_key") is not None:
        fail(results, "Raw key not visible smoke", "Raw api_key field leaked in status response.")
        return

    check_ok(results, "Provider key save smoke", f"Provider {cfg.provider_name} key stored with masked preview.")
    check_ok(results, "Masked key visible smoke", "Masked key returned by API.")
    check_ok(results, "Raw key not visible smoke", "Raw key not present in save/status responses.")


def monitoring_smoke(cfg: SmokeConfig, results: list[SmokeResult], token: str | None) -> None:
    if not token:
        skip(results, "Logs/tasks/approvals smoke", "Login token missing.")
        return

    checks = [
        ("Logs activity", "/logs/activity"),
        ("Logs audit", "/logs/audit"),
        ("Tasks", "/tasks"),
        ("Approvals pending", "/approvals/pending"),
    ]
    for name, path in checks:
        status, _, body = http_json("GET", build_url(cfg.api_base_url, path), token=token)
        if status != 200:
            fail(results, f"{name} smoke", f"GET {path} returned {status}: {response_message(body)}")
            return
    check_ok(results, "Logs/tasks/approvals smoke", "Read-only surfaces returned safely.")


def n8n_runtime_and_provider_smoke(cfg: SmokeConfig, results: list[SmokeResult], token: str | None) -> None:
    if not token:
        skip(results, "n8n guard smoke", "Login token missing.")
        return

    status, _, runtime = http_json("GET", build_url(cfg.api_base_url, "/runtime/capabilities"), token=token)
    if status != 200:
        fail(results, "OAuth panel safe status smoke", f"GET /runtime/capabilities returned {status}: {response_message(runtime)}")
        return

    status, _, n8n = http_json("GET", build_url(cfg.api_base_url, "/n8n-workflows"), token=token)
    if status in (401, 403, 404, 405):
        check_ok(results, "n8n guard smoke", f"GET /n8n-workflows blocked with {status}.")
    elif status == 200 and isinstance(n8n, dict) and isinstance(n8n.get("items"), list):
        check_ok(results, "n8n guard smoke", "GET /n8n-workflows returned metadata only.")
    elif status == 200 and isinstance(n8n, list):
        check_ok(results, "n8n guard smoke", "GET /n8n-workflows returned a safe list.")
    else:
        fail(results, "n8n guard smoke", f"GET /n8n-workflows returned {status}: {response_message(n8n)}")
        return

    status, _, keys = http_json("GET", build_url(cfg.api_base_url, "/model-provider-keys"), token=token)
    if status != 200:
        fail(results, "Provider settings smoke", f"GET /model-provider-keys returned {status}: {response_message(keys)}")
        return

    status_text = response_message(keys)
    if isinstance(keys, dict) and "items" in keys and not isinstance(keys.get("items"), list):
        fail(results, "Provider settings smoke", f"GET /model-provider-keys returned unexpected shape: {status_text}")
        return

    skip(results, "Provider test-connection smoke", "POST /providers/test-connection not run. External provider call is blocked for this smoke.")
    check_ok(results, "Provider settings smoke", "Provider key status endpoint returned safely.")


def cors_smoke(cfg: SmokeConfig, results: list[SmokeResult]) -> None:
    if not cfg.cors_origin:
        skip(results, "CORS production origin smoke", "SMOKE_CORS_ORIGIN missing.")
        return

    status, headers, body = http_json(
        "OPTIONS",
        build_url(cfg.api_base_url, "/auth/login"),
        origin=cfg.cors_origin,
        extra_headers={
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    allow_origin = headers.get("access-control-allow-origin") or headers.get("Access-Control-Allow-Origin")
    allow_credentials = headers.get("access-control-allow-credentials") or headers.get("Access-Control-Allow-Credentials")
    if status not in (200, 204):
        fail(results, "CORS production origin smoke", f"OPTIONS /auth/login returned {status}: {response_message(body)}")
        return
    if allow_origin not in (cfg.cors_origin, "*"):
        fail(results, "CORS production origin smoke", f"Allow-Origin mismatch: {allow_origin!r}")
        return
    if allow_credentials not in ("true", "True", True, None):
        fail(results, "CORS production origin smoke", f"Allow-Credentials mismatch: {allow_credentials!r}")
        return
    check_ok(results, "CORS production origin smoke", f"Origin {cfg.cors_origin} allowed.")


def run_smoke(cfg: SmokeConfig) -> list[SmokeResult]:
    results: list[SmokeResult] = []
    check_health(cfg, results)
    check_frontend_load(cfg, results)
    cors_smoke(cfg, results)

    register_user(cfg, results)
    token = login_user(cfg, results)
    auth_me(cfg, results, token)

    agent = create_agent(cfg, results, token)
    preview = github_preview(cfg, results, token)
    collection = github_collection_preview(cfg, results, token)
    import_record = import_selected_skill(cfg, results, token)
    approved_import = approve_skill(cfg, results, token, import_record)
    attach_skill(cfg, results, token, agent, approved_import)
    provider_key_smoke(cfg, results, token)
    monitoring_smoke(cfg, results, token)
    n8n_runtime_and_provider_smoke(cfg, results, token)

    if preview is not None or collection is not None:
        check_ok(results, "GitHub skill collection preview smoke", "Preview endpoints returned safe metadata.")

    return results


def print_summary(results: list[SmokeResult]) -> int:
    total = len(results)
    failed = sum(1 for item in results if item.status == FAIL)
    skipped = sum(1 for item in results if item.status == SKIP)
    passed = sum(1 for item in results if item.status == PASS)

    print("")
    print(f"Summary: {passed} pass, {skipped} skip, {failed} fail, {total} total.")
    if failed:
        return 1
    if skipped:
        return 2
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Production smoke helper for Personal AI Agent Workspace v2.1.")
    parser.add_argument("--with-mutations", action="store_true", help="Run state-changing smoke steps against a disposable test tenant.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary at the end.")
    args = parser.parse_args()

    cfg = make_config(args)
    results = run_smoke(cfg)

    if args.json:
        print(json.dumps([result.__dict__ for result in results], indent=2))

    return print_summary(results)


if __name__ == "__main__":
    raise SystemExit(main())
