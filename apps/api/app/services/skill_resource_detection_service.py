from __future__ import annotations

from dataclasses import dataclass
import re


_SAFE_EXTENSIONS = {
    "md",
    "txt",
    "csv",
    "json",
    "yaml",
    "yml",
    "docx",
    "xlsx",
    "pptx",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "webp",
    "svg",
}

_RISKY_EXTENSIONS = {
    "py",
    "js",
    "mjs",
    "cjs",
    "sh",
    "ps1",
    "bat",
    "cmd",
    "exe",
    "dll",
    "so",
    "dylib",
    "jar",
}

_BLOCKED_BASENAMES = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
    ".envrc",
    "credentials",
    "credentials.json",
    "credential",
    "credential.json",
    "secret",
    "secrets",
    "secret.json",
    "token",
    "token.json",
    "private",
    "private.pem",
    "private.key",
    "private_key",
    "private-key",
    "id_rsa",
    "id_dsa",
    "oauth_credentials.json",
    "client_secret",
    "client_secret.json",
    "apikey",
    "api_key",
}

_URL_PREFIXES = ("http://", "https://", "file://")
_MARKDOWN_RESOURCE_PATTERN = re.compile(
    r"(?P<markdown>(?:!\[[^\]]*\]|\[[^\]]*\])\((?P<target>[^)]+)\))"
)
_INLINE_URL_PATTERN = re.compile(r"(?P<path>(?:https?|file)://[^\s<>)]+)", re.IGNORECASE)
_INLINE_ABSOLUTE_PATTERN = re.compile(
    r"(?P<path>(?:[A-Za-z]:[\\/]|(?<![\w./-])/|~/)[^\s<>)]+)",
    re.IGNORECASE,
)
_INLINE_ENV_PATTERN = re.compile(
    r"(?<![\w./-])(?P<path>\.env(?:\.[A-Za-z0-9._-]+)?|\.envrc)(?![\w./-])",
    re.IGNORECASE,
)
_INLINE_BARE_BLOCKED_PATTERN = re.compile(
    r"(?<![\w./-])(?P<path>id_rsa|id_dsa)(?![\w./-])",
    re.IGNORECASE,
)

_INLINE_EXTENSION_PATTERN = re.compile(
    r"""
    (?<![\w@])
    (?P<path>
        (?:
            (?:\.\./)+
            |
            (?:\./)+
            |
            (?:~\/)+
            |
            [A-Za-z]:[\\/]
            |
            [^:\s<>"]+(?:/[^\s<>"]+)*
        )
        [^\s<>"'`)]*\.(?P<ext>md|txt|csv|json|ya?ml|docx|xlsx|pptx|pdf|png|jpe?g|webp|svg|py|js|mjs|cjs|sh|ps1|bat|cmd|exe|dll|so|dylib|jar|pem|key|p12|pfx|crt|cer)
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


@dataclass(slots=True)
class SkillResourceDetectionResult:
    resource_paths: list[str]
    safe_resource_paths: list[str]
    risky_resource_paths: list[str]
    blocked_resource_paths: list[str]
    warnings: list[str]
    has_executable_resources: bool
    requires_review: bool


def detect_skill_resource_references(content: str) -> SkillResourceDetectionResult:
    resource_paths: list[str] = []
    safe_resource_paths: list[str] = []
    risky_resource_paths: list[str] = []
    blocked_resource_paths: list[str] = []
    warnings: list[str] = []
    seen_paths: set[str] = set()
    has_executable_resources = False

    if not isinstance(content, str) or not content.strip():
        return SkillResourceDetectionResult(
            resource_paths=resource_paths,
            safe_resource_paths=safe_resource_paths,
            risky_resource_paths=risky_resource_paths,
            blocked_resource_paths=blocked_resource_paths,
            warnings=warnings,
            has_executable_resources=False,
            requires_review=False,
        )

    candidates, masked_content = _find_markdown_resource_references(content)
    for pattern in (
        _INLINE_URL_PATTERN,
        _INLINE_ABSOLUTE_PATTERN,
        _INLINE_ENV_PATTERN,
        _INLINE_BARE_BLOCKED_PATTERN,
        _INLINE_EXTENSION_PATTERN,
    ):
        pattern_candidates, masked_content = _find_regex_resource_references(masked_content, pattern)
        candidates.extend(pattern_candidates)
    candidates.sort(key=lambda item: item[0])

    for _, raw_reference in candidates:
        normalized_reference = _normalize_reference(raw_reference)
        if normalized_reference is None:
            continue
        if normalized_reference in seen_paths:
            continue

        seen_paths.add(normalized_reference)
        resource_paths.append(normalized_reference)

        blocked_reason = _blocked_reference_reason(normalized_reference)
        if blocked_reason is not None:
            blocked_resource_paths.append(normalized_reference)
            warnings.append(f"Blocked resource reference detected: {blocked_reason}")
            if _has_risky_extension(normalized_reference):
                has_executable_resources = True
            continue

        if _has_risky_extension(normalized_reference):
            risky_resource_paths.append(normalized_reference)
            has_executable_resources = True
            continue

        if _has_safe_extension(normalized_reference):
            safe_resource_paths.append(normalized_reference)
            continue

        warnings.append(f"Unclassified resource reference detected: {normalized_reference}")

    if resource_paths:
        warnings.append("Resource references were detected in SKILL.md; no files were fetched or executed.")

    requires_review = bool(risky_resource_paths or blocked_resource_paths)

    return SkillResourceDetectionResult(
        resource_paths=resource_paths,
        safe_resource_paths=safe_resource_paths,
        risky_resource_paths=risky_resource_paths,
        blocked_resource_paths=blocked_resource_paths,
        warnings=_dedupe_preserve_order(warnings),
        has_executable_resources=has_executable_resources,
        requires_review=requires_review,
    )


def _find_markdown_resource_references(content: str) -> tuple[list[tuple[int, str]], str]:
    candidates: list[tuple[int, str]] = []
    spans: list[tuple[int, int]] = []
    for match in _MARKDOWN_RESOURCE_PATTERN.finditer(content):
        target = match.group("target").strip()
        cleaned_target = _clean_markdown_target(target)
        if cleaned_target is None:
            continue
        candidates.append((match.start(), cleaned_target))
        spans.append(match.span())

    return candidates, _mask_spans(content, spans)


def _find_regex_resource_references(
    content: str,
    pattern: re.Pattern[str],
) -> tuple[list[tuple[int, str]], str]:
    candidates: list[tuple[int, str]] = []
    spans: list[tuple[int, int]] = []
    for match in pattern.finditer(content):
        path = match.group("path").strip()
        if not path:
            continue
        candidates.append((match.start(), path))
        spans.append(match.span())

    return candidates, _mask_spans(content, spans)


def _clean_markdown_target(target: str) -> str | None:
    if not target:
        return None

    cleaned = target.strip().strip("<>").strip()
    if not cleaned:
        return None

    cleaned = cleaned.split()[0].strip()
    cleaned = cleaned.rstrip(".,;:")
    return cleaned or None


def _normalize_reference(reference: str) -> str | None:
    if not isinstance(reference, str):
        return None

    cleaned = reference.strip().strip("<>").strip().strip('"').strip("'")
    if not cleaned:
        return None

    cleaned = cleaned.split()[0].strip()
    cleaned = cleaned.rstrip(".,;:")
    if not cleaned:
        return None

    return cleaned.replace("\\", "/")


def _blocked_reference_reason(path: str) -> str | None:
    lowered = path.lower()

    if lowered.startswith(_URL_PREFIXES):
        return "external URL"
    if lowered.startswith("~"):
        return "home-relative path"
    if lowered.startswith("/"):
        return "absolute path"
    if re.match(r"^[a-z]:/", lowered):
        return "absolute drive path"
    if "//" in lowered and lowered.startswith("//"):
        return "network path"

    segments = [segment for segment in lowered.split("/") if segment]
    if any(segment == ".." for segment in segments):
        return "parent directory traversal"

    basename = segments[-1] if segments else lowered
    if basename in _BLOCKED_BASENAMES:
        return "secret-like filename"
    if basename.startswith(".env"):
        return "environment file"
    if "credential" in basename:
        return "credential-like filename"
    if "secret" in basename:
        return "secret-like filename"
    if "token" in basename:
        return "token-like filename"
    if any(marker in basename for marker in ("private", "id_rsa", "id_dsa")):
        return "private key filename"
    if basename.endswith((".pem", ".key", ".p12", ".pfx", ".crt", ".cer")):
        return "private key filename"

    return None


def _has_safe_extension(path: str) -> bool:
    return _get_extension(path) in _SAFE_EXTENSIONS


def _has_risky_extension(path: str) -> bool:
    return _get_extension(path) in _RISKY_EXTENSIONS


def _get_extension(path: str) -> str:
    basename = path.rsplit("/", 1)[-1]
    if "." not in basename:
        return ""
    return basename.rsplit(".", 1)[-1].lower()


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _mask_spans(content: str, spans: list[tuple[int, int]]) -> str:
    if not spans:
        return content

    chars = list(content)
    for start, end in spans:
        for index in range(start, end):
            chars[index] = " "
    return "".join(chars)
