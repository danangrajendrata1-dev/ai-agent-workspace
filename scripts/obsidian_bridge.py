#!/usr/bin/env python3
"""Local-only bridge for packing repo context, summarizing with Ollama, and appending Obsidian notes."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen

DEFAULT_MODEL = "qwen2.5:3b"
DEFAULT_OLLAMA_ENDPOINT = "http://localhost:11434/api/chat"
DEFAULT_MAX_DIFF_LINES = 300
DEFAULT_MAX_TEST_LOG_LINES = 120
DEFAULT_NOTE_FILENAME = "AI_SUMMARIES.md"
DEFAULT_PROJECTS_ROOT = "Projects"
LOCAL_HOSTS = {"localhost", "127.0.0.1"}
NOISY_DIR_NAMES = {".git", "node_modules", ".next", "dist", "build", "__pycache__"}
SENSITIVE_NAME_MARKERS = ("secret", "token", "key", "password", "credential")


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def run_command(args: list[str], cwd: Path) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    return (
        completed.returncode,
        normalize_text(completed.stdout).strip(),
        normalize_text(completed.stderr).strip(),
    )


def line_limit(text: str, max_lines: int) -> str:
    text = normalize_text(text).strip("\n")
    if not text:
        return ""
    lines = text.split("\n")
    if len(lines) <= max_lines:
        return text
    remaining = len(lines) - max_lines
    return "\n".join(lines[:max_lines] + [f"... [truncated {remaining} line(s)]"])


def line_looks_sensitive(line: str) -> bool:
    lowered = normalize_text(line).replace("\\", "/").lower()
    if any(marker in lowered for marker in ("node_modules", "/.next/", "/dist/", "/build/", "__pycache__", "/.git/")):
        return True
    if ".env" in lowered:
        return True
    if any(marker in lowered for marker in SENSITIVE_NAME_MARKERS):
        return True
    return False


def redact_line(line: str) -> str:
    lowered = line.lower()

    if re.search(r"(?i)(api[_-]?key|secret|token|password|passwd|credential|cookie|session|authorization)\s*[:=]", line):
        match = re.match(r"^(\s*(?:export\s+)?)?([^:=\s]+)(\s*[:=]\s*)(.*)$", line)
        if match:
            key = match.group(2)
            sep = match.group(3)
            if any(marker in key.lower() for marker in SENSITIVE_NAME_MARKERS) or any(
                marker in lowered for marker in SENSITIVE_NAME_MARKERS
            ):
                return f"{match.group(1) or ''}{key}{sep}[REDACTED]"
        return "[REDACTED]"

    if "bearer " in lowered:
        return re.sub(r"(?i)(Bearer\s+)[A-Za-z0-9._\-+=/]{8,}", r"\1[REDACTED]", line)

    if re.search(r"(?i)\b(api[_-]?key|secret|token|password|passwd|credential|cookie|session)\b", line):
        return "[REDACTED]"

    if re.search(r"\b[A-Za-z0-9._%+\-/]{32,}\b", line) and any(marker in lowered for marker in SENSITIVE_NAME_MARKERS):
        return "[REDACTED]"

    return line


def redact_text(text: str) -> str:
    text = normalize_text(text)
    if not text:
        return ""
    return "\n".join(redact_line(line) for line in text.split("\n"))


def is_sensitive_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    parts = [part for part in normalized.split("/") if part]
    if not parts:
        return False

    if any(part in NOISY_DIR_NAMES for part in parts):
        return True

    basename = parts[-1]
    if basename.startswith(".env"):
        return True

    if any(marker in basename for marker in SENSITIVE_NAME_MARKERS):
        return True

    return False


def sanitize_path_segment(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 _.\-()]+", "_", value).strip(" ._")
    return cleaned or "project"


def local_ollama_endpoint(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    if parsed.scheme != "http":
        raise ValueError("Endpoint Ollama harus memakai http://localhost:11434 atau http://127.0.0.1:11434.")
    if parsed.hostname not in LOCAL_HOSTS:
        raise ValueError("Endpoint Ollama harus lokal: localhost atau 127.0.0.1.")
    if parsed.port != 11434:
        raise ValueError("Endpoint Ollama harus memakai port 11434.")

    if parsed.path in ("", "/"):
        parsed = parsed._replace(path="/api/chat")
    if parsed.path != "/api/chat":
        raise ValueError("Endpoint Ollama harus mengarah ke /api/chat.")

    return urlunparse(parsed)


def git_inside_repo(workdir: Path) -> bool:
    code, stdout, _ = run_command(["git", "rev-parse", "--is-inside-work-tree"], workdir)
    return code == 0 and stdout.strip().lower() == "true"


def collect_status_lines(workdir: Path) -> list[str]:
    code, stdout, stderr = run_command(
        ["git", "status", "--short", "--untracked-files=all"],
        workdir,
    )
    if code != 0 or not stdout:
        return []

    lines: list[str] = []
    for raw_line in stdout.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        if line_looks_sensitive(line):
            continue

        path_part = line[3:].strip() if len(line) > 3 else line
        candidate_paths = [path_part]
        if " -> " in path_part:
            candidate_paths = [piece.strip() for piece in path_part.split(" -> ")]

        if any(is_sensitive_path(candidate) for candidate in candidate_paths):
            continue
        lines.append(redact_line(line))

    return lines


def collect_git_text(workdir: Path, args: list[str]) -> str:
    code, stdout, stderr = run_command(["git", *args], workdir)
    if code != 0:
        return ""
    filtered_lines = [line for line in stdout.split("\n") if line and not line_looks_sensitive(line)]
    return redact_text("\n".join(filtered_lines))


def collect_git_context(
    workdir: Path,
    max_diff_lines: int = DEFAULT_MAX_DIFF_LINES,
) -> dict[str, Any]:
    context: dict[str, Any] = {
        "available": False,
        "branch": "unknown",
        "short_commit": "unknown",
        "recent_commits": [],
        "changed_files": [],
        "diff_stat": "",
        "diff_summary": "",
    }

    if not git_inside_repo(workdir):
        return context

    context["available"] = True

    _, branch, _ = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], workdir)
    _, short_commit, _ = run_command(["git", "rev-parse", "--short", "HEAD"], workdir)
    _, recent_commits, _ = run_command(["git", "log", "--oneline", "-n", "5"], workdir)

    context["branch"] = branch or "unknown"
    context["short_commit"] = short_commit or "unknown"
    context["recent_commits"] = [
        redact_line(line)
        for line in recent_commits.split("\n")
        if line.strip()
    ]
    context["changed_files"] = collect_status_lines(workdir)

    staged_stat = collect_git_text(
        workdir,
        ["diff", "--cached", "--stat", "--find-renames", "--no-color"],
    )
    unstaged_stat = collect_git_text(
        workdir,
        ["diff", "--stat", "--find-renames", "--no-color"],
    )
    staged_summary = collect_git_text(
        workdir,
        ["diff", "--cached", "--summary", "--find-renames", "--no-color"],
    )
    unstaged_summary = collect_git_text(
        workdir,
        ["diff", "--summary", "--find-renames", "--no-color"],
    )

    diff_stat_parts = []
    if staged_stat:
        diff_stat_parts.append("=== staged ===\n" + staged_stat)
    if unstaged_stat:
        diff_stat_parts.append("=== unstaged ===\n" + unstaged_stat)
    context["diff_stat"] = line_limit("\n\n".join(diff_stat_parts), max_diff_lines)

    diff_summary_parts = []
    if staged_summary:
        diff_summary_parts.append("=== staged ===\n" + staged_summary)
    if unstaged_summary:
        diff_summary_parts.append("=== unstaged ===\n" + unstaged_summary)
    context["diff_summary"] = line_limit("\n\n".join(diff_summary_parts), max_diff_lines)

    return context


def read_test_log_tail(test_log: str | None, workdir: Path, max_lines: int) -> dict[str, Any] | None:
    if not test_log:
        return None

    log_path = Path(test_log)
    if not log_path.is_absolute():
        log_path = (workdir / log_path).resolve()

    if not log_path.exists():
        raise FileNotFoundError(f"Test log tidak ditemukan: {log_path}")

    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    tail = lines[-max_lines:] if len(lines) > max_lines else lines
    return {
        "path": str(log_path),
        "tail": redact_text("\n".join(tail)),
        "line_count": len(lines),
        "tail_line_count": len(tail),
    }


def collect_context_pack(
    workdir: Path | None = None,
    test_log: str | None = None,
    max_diff_lines: int = DEFAULT_MAX_DIFF_LINES,
    max_test_log_lines: int = DEFAULT_MAX_TEST_LOG_LINES,
) -> dict[str, Any]:
    workdir = (workdir or Path.cwd()).resolve()
    timestamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")

    context: dict[str, Any] = {
        "timestamp": timestamp,
        "working_directory": str(workdir),
        "git": collect_git_context(workdir, max_diff_lines=max_diff_lines),
        "test_log": None,
        "warnings": [],
    }

    if test_log:
        context["test_log"] = read_test_log_tail(test_log, workdir, max_test_log_lines)

    return context


def make_ollama_prompt(context: dict[str, Any], project: str, title: str, status: str) -> tuple[str, str]:
    system_prompt = (
        "Kamu adalah asisten dokumentasi teknis yang menulis ringkasan singkat dalam bahasa Indonesia. "
        "Jangan menyebut rahasia, token, password, API key, cookie, atau isi .env. "
        "Gunakan Markdown dan pakai heading persis berikut, tanpa heading tambahan: "
        "### What changed, ### Why it matters, ### Safety notes, ### Tests/build, ### Risks/next step. "
        "Hanya gunakan fakta yang benar-benar ada di context JSON. Jangan menebak nama fitur, file, commit, atau dampak yang tidak eksplisit."
    )

    payload = {
        "project": project,
        "title": title,
        "status": status,
        "context": context,
        "rules": [
            "Jawab singkat.",
            "Gunakan hanya fakta eksplisit dari context.",
            "Jika informasi tidak ada, tulis 'Tidak ada data'.",
            "Jangan menambahkan pembukaan atau penutup di luar 5 heading wajib.",
        ],
    }

    user_prompt = json.dumps(payload, ensure_ascii=False, indent=2)
    return system_prompt, user_prompt


def normalize_summary_markdown(summary: str) -> str:
    text = normalize_text(summary).strip()
    replacements = [
        (re.compile(r"^###\s*What\s*Changed:?\s*$", re.IGNORECASE), "### What changed"),
        (re.compile(r"^###\s*Why\s*It\s*Matters:?\s*$", re.IGNORECASE), "### Why it matters"),
        (re.compile(r"^###\s*Safety\s*Notes:?\s*$", re.IGNORECASE), "### Safety notes"),
        (re.compile(r"^###\s*Tests\s*/\s*Build:?\s*$", re.IGNORECASE), "### Tests/build"),
        (re.compile(r"^###\s*Risks\s*/\s*Next\s*Step:?\s*$", re.IGNORECASE), "### Risks/next step"),
    ]

    lines = []
    for line in text.split("\n"):
        replaced = line
        for pattern, target in replacements:
            if pattern.match(line.strip()):
                replaced = target
                break
        lines.append(replaced)
    return "\n".join(lines).strip()


def call_ollama_chat(
    context: dict[str, Any],
    project: str,
    title: str,
    status: str,
    model: str = DEFAULT_MODEL,
    endpoint: str = DEFAULT_OLLAMA_ENDPOINT,
    timeout: int = 120,
) -> str:
    normalized_endpoint = local_ollama_endpoint(endpoint)
    system_prompt, user_prompt = make_ollama_prompt(context, project, title, status)

    body = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": {
            "temperature": 0.2,
        },
    }

    request = Request(
        normalized_endpoint,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        raise RuntimeError(f"Ollama HTTP error: {exc.code} {exc.reason}{': ' + detail if detail else ''}") from exc
    except URLError as exc:
        raise RuntimeError(f"Gagal menghubungi Ollama lokal di {normalized_endpoint}: {exc.reason}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Respons Ollama bukan JSON valid: {raw[:500]}") from exc

    message = data.get("message") or {}
    summary = message.get("content") or data.get("response") or ""
    summary = normalize_summary_markdown(redact_text(summary))
    if not summary:
        raise RuntimeError("Ollama tidak mengembalikan ringkasan apa pun.")
    return summary


def render_note(
    *,
    project: str,
    title: str,
    status: str,
    summary: str,
    context: dict[str, Any],
    model: str,
    endpoint: str,
) -> str:
    timestamp = context.get("timestamp", "")
    git_context = context.get("git", {})
    test_log = context.get("test_log")

    changed_files = git_context.get("changed_files") or []
    recent_commits = git_context.get("recent_commits") or []

    lines: list[str] = [
        f"## {timestamp} | {title.strip().replace('|', '/')} | {status.strip().replace('|', '/')}",
        "",
        f"- Project: {project}",
        f"- Model: {model}",
        f"- Endpoint: {endpoint}",
        f"- Branch: {git_context.get('branch', 'unknown')}",
        f"- Commit: {git_context.get('short_commit', 'unknown')}",
        "",
        summary.strip(),
        "",
        "### Context Snapshot",
        "```text",
        f"Working directory: {context.get('working_directory', '')}",
        f"Git available: {'yes' if git_context.get('available') else 'no'}",
        f"Branch: {git_context.get('branch', 'unknown')}",
        f"Commit: {git_context.get('short_commit', 'unknown')}",
        "Recent commits:",
    ]

    if recent_commits:
        for commit in recent_commits:
            lines.append(f"- {commit}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "Changed files:",
        ]
    )

    if changed_files:
        for entry in changed_files:
            lines.append(f"- {entry}")
    else:
        lines.append("- None")

    diff_stat = git_context.get("diff_stat", "")
    lines.append("Diff stat:")
    lines.append(diff_stat if diff_stat else "None")

    if test_log:
        lines.append("Test log:")
        lines.append(test_log.get("path", ""))
        lines.append(f"Tail lines: {test_log.get('tail_line_count', 0)}")
        lines.append(test_log.get("tail", ""))

    lines.extend(
        [
            "```",
            "",
        ]
    )

    return "\n".join(lines).strip() + "\n"


def resolve_vault_path(explicit_vault_path: str | None = None) -> Path:
    vault_path = explicit_vault_path or os.environ.get("OBSIDIAN_VAULT_PATH")
    if not vault_path:
        raise RuntimeError("OBSIDIAN_VAULT_PATH belum diset.")
    path = Path(vault_path).expanduser().resolve()
    if not path.exists():
        raise RuntimeError(f"Path vault Obsidian tidak ditemukan: {path}")
    if not path.is_dir():
        raise RuntimeError(f"Path vault Obsidian bukan folder: {path}")
    return path


def build_note_path(vault_path: Path, project: str) -> Path:
    project_segment = sanitize_path_segment(project)
    note_path = vault_path / DEFAULT_PROJECTS_ROOT / project_segment / DEFAULT_NOTE_FILENAME
    resolved_vault = vault_path.resolve()
    resolved_note_parent = note_path.parent.resolve(strict=False)
    if resolved_vault not in resolved_note_parent.parents and resolved_note_parent != resolved_vault:
        raise RuntimeError("Path catatan keluar dari vault.")
    return note_path


def append_note(note_path: Path, note_text: str) -> None:
    note_path.parent.mkdir(parents=True, exist_ok=True)
    needs_separator = note_path.exists() and note_path.stat().st_size > 0
    with note_path.open("a", encoding="utf-8", newline="\n") as handle:
        if needs_separator:
            handle.write("\n\n---\n\n")
        handle.write(note_text)


def run_pipeline(
    *,
    project: str,
    title: str,
    status: str,
    model: str = DEFAULT_MODEL,
    endpoint: str = DEFAULT_OLLAMA_ENDPOINT,
    vault_path: str | None = None,
    test_log: str | None = None,
    max_diff_lines: int = DEFAULT_MAX_DIFF_LINES,
    max_test_log_lines: int = DEFAULT_MAX_TEST_LOG_LINES,
    dry_run: bool = False,
) -> dict[str, Any]:
    workdir = Path.cwd().resolve()
    note_path = None
    if not dry_run:
        vault = resolve_vault_path(vault_path)
        note_path = build_note_path(vault, project)

    context = collect_context_pack(
        workdir=workdir,
        test_log=test_log,
        max_diff_lines=max_diff_lines,
        max_test_log_lines=max_test_log_lines,
    )
    summary = call_ollama_chat(
        context=context,
        project=project,
        title=title,
        status=status,
        model=model,
        endpoint=endpoint,
    )
    note_text = render_note(
        project=project,
        title=title,
        status=status,
        summary=summary,
        context=context,
        model=model,
        endpoint=local_ollama_endpoint(endpoint),
    )

    if not dry_run:
        append_note(note_path, note_text)

    return {
        "context": context,
        "summary": summary,
        "note_text": note_text,
        "note_path": str(note_path) if note_path else None,
    }


def build_context_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Kumpulkan konteks git/test lokal untuk ringkasan Obsidian.",
    )
    parser.add_argument("--test-log", help="Path log test opsional untuk di-tail.")
    parser.add_argument(
        "--max-diff-lines",
        type=int,
        default=DEFAULT_MAX_DIFF_LINES,
        help="Batas maksimum baris diff summary yang dikumpulkan.",
    )
    parser.add_argument(
        "--max-test-log-lines",
        type=int,
        default=DEFAULT_MAX_TEST_LOG_LINES,
        help="Batas maksimum baris test log tail.",
    )
    parser.add_argument(
        "--output",
        help="Path file output JSON. Jika kosong, cetak ke stdout.",
    )
    return parser


def build_summary_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Kirim context pack lokal ke Ollama lalu keluarkan ringkasan Markdown.",
    )
    parser.add_argument(
        "--context-file",
        default="-",
        help="Path JSON context pack, atau - untuk stdin.",
    )
    parser.add_argument(
        "--project",
        required=True,
        help="Nama proyek yang akan dipakai dalam prompt.",
    )
    parser.add_argument(
        "--title",
        required=True,
        help="Judul catatan/ringkasan.",
    )
    parser.add_argument(
        "--status",
        required=True,
        help="Status ringkasan, misalnya PASS atau FAIL.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model Ollama lokal. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_OLLAMA_ENDPOINT,
        help=f"Endpoint Ollama lokal. Default: {DEFAULT_OLLAMA_ENDPOINT}",
    )
    parser.add_argument(
        "--output",
        help="Path file output Markdown. Jika kosong, cetak ke stdout.",
    )
    return parser


def build_run_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bridge level-3 lokal: pack konteks, ringkas dengan Ollama, lalu append ke Obsidian.",
    )
    parser.add_argument(
        "--project",
        required=True,
        help="Nama proyek untuk folder Projects/<project>/AI_SUMMARIES.md.",
    )
    parser.add_argument(
        "--title",
        required=True,
        help="Judul entry ringkasan.",
    )
    parser.add_argument(
        "--status",
        required=True,
        help="Status entry, misalnya PASS atau FAIL.",
    )
    parser.add_argument(
        "--test-log",
        help="Path log test opsional yang akan dikumpulkan ke context pack.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model Ollama lokal. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_OLLAMA_ENDPOINT,
        help=f"Endpoint Ollama lokal. Default: {DEFAULT_OLLAMA_ENDPOINT}",
    )
    parser.add_argument(
        "--vault-path",
        help="Override path vault Obsidian. Jika kosong, gunakan OBSIDIAN_VAULT_PATH.",
    )
    parser.add_argument(
        "--max-diff-lines",
        type=int,
        default=DEFAULT_MAX_DIFF_LINES,
        help="Batas maksimum baris diff summary yang dikumpulkan.",
    )
    parser.add_argument(
        "--max-test-log-lines",
        type=int,
        default=DEFAULT_MAX_TEST_LOG_LINES,
        help="Batas maksimum baris test log tail.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Kumpulkan konteks dan ringkasan, tetapi jangan append note ke Obsidian.",
    )
    parser.add_argument(
        "--output-context",
        help="Path file JSON context pack untuk disimpan juga.",
    )
    parser.add_argument(
        "--output-summary",
        help="Path file Markdown summary untuk disimpan juga.",
    )
    return parser


def main_context_pack(argv: list[str] | None = None) -> int:
    parser = build_context_parser()
    args = parser.parse_args(argv)
    try:
        context = collect_context_pack(
            test_log=args.test_log,
            max_diff_lines=args.max_diff_lines,
            max_test_log_lines=args.max_test_log_lines,
        )
        output = json.dumps(context, ensure_ascii=False, indent=2)
        if args.output:
            out_path = Path(args.output).expanduser().resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output + "\n", encoding="utf-8")
        else:
            sys.stdout.write(output + "\n")
        return 0
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def main_summary(argv: list[str] | None = None) -> int:
    parser = build_summary_parser()
    args = parser.parse_args(argv)
    try:
        if args.context_file == "-":
            context_raw = sys.stdin.read()
        else:
            context_raw = Path(args.context_file).expanduser().read_text(encoding="utf-8")

        try:
            context = json.loads(context_raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Context pack bukan JSON valid: {exc}") from exc

        summary = call_ollama_chat(
            context=context,
            project=args.project,
            title=args.title,
            status=args.status,
            model=args.model,
            endpoint=args.endpoint,
        )
        if args.output:
            out_path = Path(args.output).expanduser().resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(summary + "\n", encoding="utf-8")
        else:
            sys.stdout.write(summary + "\n")
        return 0
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def main_run(argv: list[str] | None = None) -> int:
    parser = build_run_parser()
    args = parser.parse_args(argv)
    try:
        result = run_pipeline(
            project=args.project,
            title=args.title,
            status=args.status,
            model=args.model,
            endpoint=args.endpoint,
            vault_path=args.vault_path,
            test_log=args.test_log,
            max_diff_lines=args.max_diff_lines,
            max_test_log_lines=args.max_test_log_lines,
            dry_run=args.dry_run,
        )

        if args.output_context:
            out_path = Path(args.output_context).expanduser().resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(result["context"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if args.output_summary:
            out_path = Path(args.output_summary).expanduser().resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(result["summary"] + "\n", encoding="utf-8")

        if args.dry_run:
            print("Dry run selesai. Note tidak ditulis.")
        else:
            print(f"Ringkasan Ollama selesai. Note ditulis ke: {result['note_path']}")
        return 0
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    return main_run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
