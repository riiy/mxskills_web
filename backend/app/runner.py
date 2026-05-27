from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .skills import ROOT_DIR, SELECT_TYPES, SKILL_PYTHON_COMMAND, Skill, get_skill


@dataclass(frozen=True)
class FilePattern:
    """Regex pattern for extracting file paths from output text."""

    pattern: re.Pattern = field(
        default_factory=lambda: re.compile(
            r"(?P<path>(?:/[^\s)）]+|(?:\.{0,2}/)?[^\s:：]+)[^\s)）]*\.(?:md|txt|csv|xlsx|pdf|docx?|DOCX?|PDF))"
        )
    )


@dataclass(frozen=True)
class UrlPattern:
    """Regex pattern for extracting URLs from output text."""

    pattern: re.Pattern = field(default_factory=lambda: re.compile(r"https?://[^\s)）]+"))


FILE_PATTERN = FilePattern()
URL_PATTERN = UrlPattern()

OUTPUT_ROOTS: list[Path] = [
    ROOT_DIR / "miaoxiang",
    ROOT_DIR / "workspace",
    ROOT_DIR / "stock_diagnosis",
    ROOT_DIR / "fund_diagnosis",
    ROOT_DIR / "stock_market_hotspot_discovery",
    ROOT_DIR / "mx_finance_search",
]

DEFAULT_TIMEOUT_SECONDS: int = 180


def build_command(skill: Skill, query: str, params: dict[str, Any] | None = None) -> list[str]:
    params = params or {}
    if not query.strip():
        raise ValueError("请输入查询内容。")
    if skill.script_path is None:
        raise ValueError(f"{skill.id} 需要专用编排器。")
    if not skill.script_path.exists():
        raise ValueError(f"脚本不存在: {skill.script_path}")

    command = [*SKILL_PYTHON_COMMAND, str(skill.script_path)]
    if skill.query_position:
        command.append(query)
    else:
        command.extend([skill.query_arg, query])

    if skill.id == "mx-stocks-screener":
        select_type = params.get("selectType")
        if select_type not in SELECT_TYPES:
            raise ValueError(f"selectType 必须是以下之一: {', '.join(SELECT_TYPES)}")
        command.extend(["--select-type", str(select_type)])
    if skill.id == "mx-financial-assistant" and params.get("deepThink"):
        command.append("--deep-think")
    return command


def _json_from_stdout(stdout: str) -> Any | None:
    text = stdout.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def _stringify_json_payload(payload: dict[str, Any]) -> str:
    if payload.get("message"):
        return str(payload["message"])
    parts: list[str] = []
    title = payload.get("title") or payload.get("header")
    content = payload.get("answer") or payload.get("content") or payload.get("truncated_text") or payload.get("summary")
    if title:
        parts.append(f"## {title}")
    if content:
        parts.append(str(content))
    share = payload.get("shareUrl") or payload.get("share_url")
    if share:
        parts.append(f"**分享链接：**\n{share}")
    if not parts:
        return json.dumps(payload, ensure_ascii=False, indent=2)
    return "\n\n".join(parts)


def extract_urls(text: str, payload: Any | None = None) -> list[dict[str, str]]:
    """Extract URLs from text and nested payload structures.

    Args:
        text: Raw stdout text to search for URLs.
        payload: Optional parsed JSON payload to traverse.

    Returns:
        List of unique URL objects with label and url fields.
    """
    found: dict[str, dict[str, str]] = {}
    for url in URL_PATTERN.pattern.findall(text):
        found[url] = {"label": "外部链接", "url": url}

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, str):
            for url in URL_PATTERN.pattern.findall(value):
                found[url] = {"label": "外部链接", "url": url}

    visit(payload)
    return list(found.values())


def extract_files(text: str, payload: Any | None = None) -> list[dict[str, str]]:
    """Extract file paths from text and nested payload structures.

    Args:
        text: Raw stdout text to search for file paths.
        payload: Optional parsed JSON payload to traverse.

    Returns:
        List of unique file objects with path and name fields.
    """
    raw_paths: list[str] = []
    raw_paths.extend(match.group("path").rstrip("。,.，") for match in FILE_PATTERN.pattern.finditer(text))

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, str) and re.search(r"\.(md|txt|csv|xlsx|pdf|docx?|DOCX?|PDF)$", value):
            raw_paths.append(value)

    visit(payload)

    files: dict[str, dict[str, str]] = {}
    for raw_path in raw_paths:
        path = Path(raw_path)
        if not path.is_absolute():
            path = (ROOT_DIR / raw_path).resolve()
        else:
            path = path.resolve()
        files[str(path)] = {"path": str(path), "name": path.name}
    return list(files.values())


def normalize_result(skill_id: str, stdout: str, stderr: str, returncode: int) -> dict[str, Any]:
    """Normalize skill execution output into a consistent response format.

    Args:
        skill_id: The identifier of the executed skill.
        stdout: Standard output from the subprocess.
        stderr: Standard error from the subprocess.
        returncode: Exit code from the subprocess.

    Returns:
        A dictionary containing normalized result with content, files, links, and metadata.
    """
    payload = _json_from_stdout(stdout)
    text = _stringify_json_payload(payload) if isinstance(payload, dict) else stdout.strip()
    files = extract_files(stdout, payload)
    links = extract_urls(stdout, payload)
    ok = returncode == 0
    message = None
    if isinstance(payload, dict):
        ok = bool(payload.get("ok", ok))
        message = payload.get("message") or payload.get("error")
    if not ok and not message:
        message = stderr.strip() or text or f"脚本执行失败，退出码 {returncode}"
    return {
        "ok": ok,
        "skillId": skill_id,
        "content": text,
        "files": files,
        "links": links,
        "raw": payload,
        "stderr": stderr.strip(),
        "message": message,
    }


def _run_subprocess(command: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    """Execute a subprocess synchronously with UTF-8 encoding.

    Args:
        command: Command arguments for subprocess execution.
        timeout: Maximum execution time in seconds.

    Returns:
        CompletedProcess instance with stdout, stderr, and returncode.
    """
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return subprocess.run(
        command,
        cwd=ROOT_DIR,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
        check=False,
    )


async def run_command(skill: Skill, command: list[str]) -> dict[str, Any]:
    """Execute a skill command asynchronously with timeout handling.

    Args:
        skill: The skill configuration containing timeout settings.
        command: Command arguments for subprocess execution.

    Returns:
        Normalized result dictionary from the skill execution.
    """
    try:
        completed = await asyncio.to_thread(_run_subprocess, command, skill.timeout_seconds)
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "skillId": skill.id,
            "content": "",
            "files": [],
            "links": [],
            "raw": None,
            "stderr": "",
            "message": "执行超时，请稍后重试或缩小查询范围。",
        }
    return normalize_result(skill.id, completed.stdout, completed.stderr, completed.returncode)


async def run_regular_skill(skill_id: str, query: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run a standard skill that has an associated script.

    Args:
        skill_id: The identifier of the skill to run.
        query: The user's natural language query.
        params: Optional parameters for the skill.

    Returns:
        Execution result with command details included.
    """
    skill = get_skill(skill_id)
    command = build_command(skill, query, params)
    result = await run_command(skill, command)
    result["command"] = command
    return result


async def run_earnings_review(query: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run the earnings review skill with multi-step orchestration.

    This skill requires three sequential steps:
    1. Validate the entity (company/stock) from the query.
    2. Normalize and select the report period.
    3. Generate the performance review.

    Args:
        query: Natural language query mentioning a company or stock.
        params: Optional parameters including reportDate selection.

    Returns:
        Combined result from all three steps with intermediate data.
    """
    params = params or {}
    skill = get_skill("stock-earnings-review")
    base = ROOT_DIR / "stock-earnings-review" / "scripts"
    entity_cmd = [*SKILL_PYTHON_COMMAND, str(base / "validate_entity.py"), "--query", query]
    entity_result = await run_command(skill, entity_cmd)
    if not entity_result["ok"]:
        return entity_result
    entity = entity_result.get("raw") or {}
    required = ["secuCode", "marketChar", "classCode"]
    if not all(entity.get(key) for key in required):
        entity_result["ok"] = False
        entity_result["message"] = entity.get("message") or "请确认公司名称或股票代码。"
        return entity_result

    period_cmd = [
        *SKILL_PYTHON_COMMAND,
        str(base / "normalize_report_period.py"),
        "--secu-code",
        str(entity["secuCode"]),
        "--market-char",
        str(entity["marketChar"]),
        "--class-code",
        str(entity["classCode"]),
        "--secu-name",
        str(entity.get("secuName") or ""),
    ]
    selected_report_date = str(params.get("reportDate") or "").strip()
    if selected_report_date:
        period_cmd.extend(["--selected-report-date", selected_report_date])
    period_result = await run_command(skill, period_cmd)
    if not period_result["ok"]:
        return period_result
    period_payload = period_result.get("raw") or {}
    matched = period_payload.get("matchedReport") or {}
    report_date = matched.get("reportDate")
    if not report_date:
        period_result["ok"] = False
        period_result["message"] = "暂无该实体的可用报告期数据"
        return period_result

    review_cmd = [
        *SKILL_PYTHON_COMMAND,
        str(base / "call_review_api.py"),
        "--secu-code",
        str(entity["secuCode"]),
        "--market-char",
        str(entity["marketChar"]),
        "--class-code",
        str(entity["classCode"]),
        "--secu-name",
        str(entity.get("secuName") or ""),
        "--report-date",
        str(report_date),
    ]
    review_result = await run_command(skill, review_cmd)
    review_result["steps"] = {"entity": entity, "period": period_payload}
    if review_result["content"]:
        review_result["content"] = f"报告期：{report_date}\n\n{review_result['content']}"
    return review_result


async def run_skill(skill_id: str, query: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Main entry point for running any registered skill.

    Routes special skills (like earnings review) to their custom handlers,
    and delegates regular skills to the standard execution path.

    Args:
        skill_id: The identifier of the skill to run.
        query: The user's natural language query.
        params: Optional parameters for the skill.

    Returns:
        Execution result from the skill.
    """
    if skill_id == "stock-earnings-review":
        return await run_earnings_review(query, params)
    return await run_regular_skill(skill_id, query, params)


def allowed_file_path(path_value: str) -> Path:
    """Validate and resolve a file path for download.

    Ensures the requested file exists within allowed output directories
    to prevent directory traversal attacks.

    Args:
        path_value: The file path requested for download.

    Returns:
        Resolved absolute path to the file.

    Raises:
        ValueError: If the path is outside allowed directories.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT_DIR / path
    resolved = path.resolve()
    roots = [root.resolve() for root in OUTPUT_ROOTS]
    if not any(resolved == root or root in resolved.parents for root in roots):
        raise ValueError("文件路径不在允许下载的输出目录内。")
    if not resolved.exists() or not resolved.is_file():
        raise FileNotFoundError("文件不存在。")
    return resolved
