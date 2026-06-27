from __future__ import annotations

import asyncio
import json
import os
import runpy
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx


OUTPUT_DIR = Path(__file__).resolve().parents[2] / "miaoxiang" / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_urls_from_main(main_path: str = "backend/main.py") -> list[str]:
    namespace = runpy.run_path(main_path)
    urls = namespace.get("urls")
    if not urls:
        raise RuntimeError("No 'urls' variable found in backend/main.py")
    return list(urls)


def report_name_from_url(url: str) -> str:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    return params.get("reportName", [None])[0] or "UNKNOWN"


async def fetch_url(client: httpx.AsyncClient, url: str, timeout: int = 15) -> dict[str, Any]:
    result: dict[str, Any] = {"url": url, "ok": False, "status_code": None, "error": None, "json": None, "text": None}
    try:
        resp = await client.get(url, timeout=timeout)
        result["status_code"] = resp.status_code
        content_type = resp.headers.get("content-type", "")
        text = resp.text
        result["text"] = text
        if "json" in content_type or text.strip().startswith("{") or text.strip().startswith("["):
            try:
                result["json"] = resp.json()
            except Exception:
                try:
                    result["json"] = json.loads(text)
                except Exception:
                    result["json"] = None
        result["ok"] = resp.status_code == 200
    except Exception as exc:
        result["error"] = str(exc)
    return result


async def fetch_all(urls: list[str], concurrency: int = 8) -> list[dict[str, Any]]:
    timeout = httpx.Timeout(15.0, read=30.0)
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=50)
    results: list[dict[str, Any]] = []
    sem = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=True) as client:
        async def _bound_fetch(u: str) -> None:
            async with sem:
                res = await fetch_url(client, u)
                results.append(res)

        await asyncio.gather(*[_bound_fetch(u) for u in urls])
    return results


def aggregate_by_report_name(fetch_results: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in fetch_results:
        rn = report_name_from_url(r.get("url", ""))
        grouped[rn].append(r)
    return dict(grouped)


def summarize_group(items: list[dict[str, Any]]) -> str:
    ok_count = sum(1 for i in items if i.get("ok"))
    parts = [f"- URLs: {len(items)}", f"- Successes: {ok_count}"]
    sample_texts = []
    sample_json_keys = set()
    for i in items:
        if i.get("json") is not None:
            j = i.get("json")
            if isinstance(j, dict):
                sample_json_keys.update(j.keys())
            elif isinstance(j, list) and j:
                if isinstance(j[0], dict):
                    sample_json_keys.update(j[0].keys())
        else:
            txt = i.get("text") or ""
            if txt:
                sample_texts.append(txt.strip()[:300].replace("\n", " "))
    if sample_json_keys:
        parts.append(f"- Sample JSON keys: {', '.join(sorted(list(sample_json_keys))[:20])}")
    if sample_texts:
        parts.append("- Sample text snippets:")
        for s in sample_texts[:3]:
            parts.append(f"  - {s}")
    return "\n".join(parts)


def build_markdown_report(grouped: dict[str, list[dict[str, Any]]]) -> str:
    lines: list[str] = []
    lines.append(f"# Aggregated Report\nGenerated: {datetime.utcnow().isoformat()}Z\n")
    for rn, items in grouped.items():
        lines.append(f"## reportName: {rn} ({len(items)} urls)\n")
        lines.append(summarize_group(items))
        lines.append("")
        lines.append("### Individual results\n")
        for it in items:
            lines.append(f"- URL: {it.get('url')}")
            if it.get("ok"):
                lines.append(f"  - status: {it.get('status_code')}")
                if it.get("json") is not None:
                    try:
                        pretty = json.dumps(
                            it.get("json") if not isinstance(it.get("json"), (str, int)) else {"value": it.get("json")},
                            ensure_ascii=False,
                            indent=2,
                        )
                        lines.append("  - json_sample:\n\n```")
                        lines.append(pretty)
                        lines.append("```")
                    except Exception:
                        lines.append("  - json_sample: (unserializable)")
                else:
                    txt = (it.get("text") or "")[:600]
                    if txt:
                        lines.append("  - text_snippet: >")
                        lines.append(f"    {txt.replace('\n', ' ')}")
            else:
                lines.append(f"  - error: {it.get('error')}")
        lines.append("\n---\n")
    return "\n".join(lines)


def write_report(markdown: str) -> Path:
    name = f"aggregate_report_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.md"
    path = OUTPUT_DIR / name
    path.write_text(markdown, encoding="utf-8")
    return path


def run_sync() -> Path:
    urls = load_urls_from_main()
    fetch_results = asyncio.run(fetch_all(urls))
    grouped = aggregate_by_report_name(fetch_results)
    md = build_markdown_report(grouped)
    out = write_report(md)
    print(f"Wrote report: {out}")
    return out


if __name__ == "__main__":
    run_sync()
