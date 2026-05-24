from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


ROOT_DIR = Path(__file__).resolve().parents[2]
SKILL_PYTHON_COMMAND = [
    "uv",
    "run",
    "--with",
    "httpx",
    "--with",
    "pandas",
    "--with",
    "openpyxl",
    "python3",
]

SelectType = Literal["A股", "港股", "美股", "基金", "ETF", "可转债", "板块"]
SELECT_TYPES: tuple[SelectType, ...] = ("A股", "港股", "美股", "基金", "ETF", "可转债", "板块")


@dataclass(frozen=True)
class Skill:
    id: str
    title: str
    group: str
    description: str
    script: str | None
    query_arg: str = "--query"
    query_position: bool = False
    output_type: str = "markdown"
    examples: list[str] = field(default_factory=list)
    required_fields: list[str] = field(default_factory=lambda: ["query"])
    controls: list[dict[str, Any]] = field(default_factory=list)
    timeout_seconds: int = 180

    @property
    def script_path(self) -> Path | None:
        if self.script is None:
            return None
        return ROOT_DIR / self.id / self.script

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "group": self.group,
            "description": self.description,
            "requiredFields": self.required_fields,
            "controls": self.controls,
            "examples": self.examples,
            "outputType": self.output_type,
        }


SKILLS: dict[str, Skill] = {
    "mx-financial-assistant": Skill(
        id="mx-financial-assistant",
        title="金融问答",
        group="问答",
        description="自然语言金融问答，覆盖查数、资讯、宏观、筛选、知识与市场分析，可选深度思考。",
        script="scripts/generate_answer.py",
        output_type="json-markdown",
        examples=["分析一下今天A股市场情绪", "深度分析半导体板块近期机会"],
        controls=[{"id": "deepThink", "label": "深度思考", "type": "boolean"}],
        timeout_seconds=240,
    ),
    "mx-finance-data": Skill(
        id="mx-finance-data",
        title="金融数据查询",
        group="查数/筛选",
        description="查询A港美股、基金、债券等结构化金融数据，输出Excel和说明文件。",
        script="scripts/get_data.py",
        output_type="files",
        examples=["贵州茅台最近一年的营业收入和净利润", "英伟达现在的最新价和涨跌幅"],
    ),
    "mx-finance-search": Skill(
        id="mx-finance-search",
        title="金融资讯搜索",
        group="问答",
        description="检索公告、研报、新闻、政策等金融资讯并返回可追溯文本。",
        script="scripts/get_data.py",
        query_position=True,
        output_type="text",
        examples=["寒武纪 688256 最新研报与公告", "商业航天板块近期新闻"],
    ),
    "mx-macro-data": Skill(
        id="mx-macro-data",
        title="宏观数据查询",
        group="查数/筛选",
        description="查询全球宏观经济指标，生成CSV与数据说明文件。",
        script="scripts/get_data.py",
        output_type="files",
        examples=["查询中国过去五年的M2增速", "查询美国制造业PMI"],
    ),
    "mx-stocks-screener": Skill(
        id="mx-stocks-screener",
        title="选股/选基/选板块",
        group="查数/筛选",
        description="按自然语言条件筛选A股、港股、美股、基金、ETF、可转债或板块。",
        script="scripts/get_data.py",
        output_type="files",
        examples=["股价大于500元的股票", "规模超2亿的电力ETF"],
        required_fields=["query", "selectType"],
        controls=[{"id": "selectType", "label": "查询领域", "type": "select", "options": list(SELECT_TYPES)}],
    ),
    "stock-diagnosis": Skill(
        id="stock-diagnosis",
        title="股票综合诊断",
        group="诊断",
        description="面向单只沪深京A股生成综合Markdown诊断报告。",
        script="scripts/get_data.py",
        output_type="markdown",
        examples=["东方财富股票咋样", "全面分析一下中国平安"],
    ),
    "fund-diagnosis": Skill(
        id="fund-diagnosis",
        title="基金综合诊断",
        group="诊断",
        description="面向单只公募基金生成收益、风险和持仓结构诊断报告。",
        script="scripts/get_data.py",
        output_type="markdown",
        examples=["华夏成长混合基金怎么样", "这只基金适合长期持有吗"],
    ),
    "stock-market-hotspot-discovery": Skill(
        id="stock-market-hotspot-discovery",
        title="股市热点发现",
        group="点评/分析",
        description="发现A股市场热点资讯、热门股票和活跃方向。",
        script="scripts/get_data.py",
        output_type="markdown",
        examples=["今日热点是什么", "今天最热的股票有哪些"],
    ),
    "topic-research-report": Skill(
        id="topic-research-report",
        title="专题研究报告",
        group="报告",
        description="生成事件、政策、主题投资等跨行业专题研究报告及附件。",
        script="scripts/get_data.py",
        output_type="report",
        examples=["AI Agent产业链专题", "美联储降息对A股影响"],
        timeout_seconds=420,
    ),
    "industry-research-report": Skill(
        id="industry-research-report",
        title="行业研究报告",
        group="报告",
        description="为指定行业或产业生成深度研究报告及PDF/DOCX附件。",
        script="scripts/get_data.py",
        output_type="report",
        examples=["半导体行业研究报告", "新能源汽车产业发展趋势"],
        timeout_seconds=420,
    ),
    "industry-stock-tracker": Skill(
        id="industry-stock-tracker",
        title="行业/个股跟踪报告",
        group="报告",
        description="生成行业、板块、指数或个股的近况跟踪报告。",
        script="scripts/generate_industry_stock_tracker_report.py",
        output_type="report",
        examples=["写一份半导体行业日报", "跟踪东方财富最近变化"],
        timeout_seconds=420,
    ),
    "initiation-of-coverage-or-deep-dive": Skill(
        id="initiation-of-coverage-or-deep-dive",
        title="首次覆盖/深度研究",
        group="报告",
        description="为沪深京港美上市公司生成首次覆盖或深度研究报告。",
        script="scripts/generate_deep_research_report.py",
        output_type="report",
        examples=["帮我写一份东方财富公司的深度研究报告", "英伟达首次覆盖报告"],
        timeout_seconds=420,
    ),
    "comparable-company-analysis": Skill(
        id="comparable-company-analysis",
        title="可比公司分析",
        group="点评/分析",
        description="针对A股上市公司生成经营、财务、估值可比公司Excel报告。",
        script="scripts/excel_theme.py",
        output_type="files",
        examples=["东方财富可比公司分析", "比亚迪同业对比"],
        timeout_seconds=240,
    ),
    "stock-earnings-review": Skill(
        id="stock-earnings-review",
        title="上市公司业绩点评",
        group="点评/分析",
        description="对沪深京港美上市公司已发布报告期生成业绩点评、附件和分享链接。",
        script=None,
        output_type="report",
        examples=["东方财富 业绩点评", "英伟达最新财报点评"],
        controls=[{"id": "reportDate", "label": "报告期", "type": "text", "placeholder": "可留空，默认最新一期"}],
        timeout_seconds=420,
    ),
}


def get_skill(skill_id: str) -> Skill:
    try:
        return SKILLS[skill_id]
    except KeyError as exc:
        raise ValueError(f"未知技能: {skill_id}") from exc


def list_skills() -> list[dict[str, Any]]:
    return [skill.to_public_dict() for skill in SKILLS.values()]
