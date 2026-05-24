from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.runner import allowed_file_path, build_command, normalize_result, run_skill
from app.skills import ROOT_DIR, get_skill, list_skills


def test_registry_returns_configured_skills() -> None:
    ids = {skill["id"] for skill in list_skills()}
    assert "mx-financial-assistant" in ids
    assert "stock-earnings-review" in ids
    assert "mx-stocks-screener" in ids


def test_command_builder_rejects_unknown_and_builds_arg_list() -> None:
    with pytest.raises(ValueError):
        get_skill("unknown")
    skill = get_skill("mx-stocks-screener")
    command = build_command(skill, "股价大于100元", {"selectType": "A股"})
    assert command[-4:] == ["--query", "股价大于100元", "--select-type", "A股"]
    assert command[:2] == ["uv", "run"]
    with pytest.raises(ValueError):
        build_command(skill, "股价大于100元", {"selectType": "债券"})


def test_file_serving_blocks_outside_paths(tmp_path: Path) -> None:
    outside = tmp_path / "secret.txt"
    outside.write_text("nope", encoding="utf-8")
    with pytest.raises(ValueError):
        allowed_file_path(str(outside))


def test_file_serving_allows_known_output_root() -> None:
    output_dir = ROOT_DIR / "miaoxiang" / "test_console"
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / "sample.txt"
    file_path.write_text("ok", encoding="utf-8")
    assert allowed_file_path(str(file_path)) == file_path.resolve()


def test_normalizer_parses_json_text_and_files() -> None:
    json_result = normalize_result(
        "mx-financial-assistant",
        '{"ok": true, "answer": "正文", "files": {"pdf": "/home/riiy/miaoxiang_web/miaoxiang/a.pdf"}}',
        "",
        0,
    )
    assert json_result["ok"] is True
    assert json_result["content"] == "正文"
    assert json_result["files"][0]["name"] == "a.pdf"

    text_result = normalize_result("stock-diagnosis", "Saved: miaoxiang/x.md\n# 报告", "", 0)
    assert text_result["content"].endswith("# 报告")
    assert text_result["files"][0]["name"] == "x.md"


@pytest.mark.asyncio
async def test_run_skill_uses_subprocess_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, "Saved: miaoxiang/out.md\n# ok", "")

    monkeypatch.setattr("app.runner.subprocess.run", fake_run)
    result = await run_skill("stock-diagnosis", "东方财富怎么样")
    assert result["ok"] is True
    assert result["files"][0]["name"] == "out.md"


@pytest.mark.asyncio
async def test_earnings_review_mock_success(monkeypatch: pytest.MonkeyPatch) -> None:
    outputs = [
        '{"classCode":"002001","secuCode":"300059","marketChar":"SZ","secuName":"东方财富"}',
        '{"matchedReport":{"reportDate":"2025-12-31","periodLabel":"2025年报"},"reportOptions":[]}',
        '{"ok":true,"title":"点评","content":"正文","files":{"pdf":"/home/riiy/miaoxiang_web/miaoxiang/stock-earnings-review/a.pdf"}}',
    ]

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, outputs.pop(0), "")

    monkeypatch.setattr("app.runner.subprocess.run", fake_run)
    result = await run_skill("stock-earnings-review", "东方财富业绩点评")
    assert result["ok"] is True
    assert "报告期：2025-12-31" in result["content"]


@pytest.mark.asyncio
async def test_earnings_review_stops_on_entity_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def fake_run(*args, **kwargs):
        nonlocal calls
        calls += 1
        return subprocess.CompletedProcess(args[0], 0, '{"classCode":"","secuCode":"","marketChar":"","secuName":""}', "")

    monkeypatch.setattr("app.runner.subprocess.run", fake_run)
    result = await run_skill("stock-earnings-review", "未知公司业绩点评")
    assert result["ok"] is False
    assert calls == 1
