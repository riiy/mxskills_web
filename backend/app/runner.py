from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from .skills import ROOT_DIR, SELECT_TYPES, SKILL_PYTHON_COMMAND, Skill, get_skill


FILE_RE = re.compile(r"(?P<path>(?:/[^\s)）]+|(?:\.{0,2}/)?[^\s:：]+)[^\s)）]*\.(?:md|txt|csv|xlsx|pdf|docx?|DOCX?|PDF))")
URL_RE = re.compile(r"https?://[^\s)）]+")

OUTPUT_ROOTS = [
    ROOT_DIR / "miaoxiang",
    ROOT_DIR / "workspace",
    ROOT_DIR / "stock_diagnosis",
    ROOT_DIR / "fund_diagnosis",
    ROOT_DIR / "stock_market_hotspot_discovery",
    ROOT_DIR / "mx_finance_search",
]


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
    found: dict[str, dict[str, str]] = {}
    for url in URL_RE.findall(text):
        found[url] = {"label": "外部链接", "url": url}

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, str):
            for url in URL_RE.findall(value):
                found[url] = {"label": "外部链接", "url": url}

    visit(payload)
    return list(found.values())


def extract_files(text: str, payload: Any | None = None) -> list[dict[str, str]]:
    raw_paths: list[str] = []
    raw_paths.extend(match.group("path").rstrip("。,.，") for match in FILE_RE.finditer(text))

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
    skill = get_skill(skill_id)
    command = build_command(skill, query, params)
    result = await run_command(skill, command)
    result["command"] = command
    return result


async def run_earnings_review(query: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
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
    if skill_id == "stock-earnings-review":
        return await run_earnings_review(query, params)
    return await run_regular_skill(skill_id, query, params)


def allowed_file_path(path_value: str) -> Path:
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
