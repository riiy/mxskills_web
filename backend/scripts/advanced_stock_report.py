#!/usr/bin/env python3
"""
Advanced Stock Report Generator

高级功能：
- 批量生成多个股票的报告
- 支持多种输出格式（Markdown、HTML）
- 支持数据缓存
- 可配置的API端点和超时
- 详细的错误日志
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from dataclasses import dataclass, asdict

try:
    import httpx
except ImportError:
    print("Error: httpx is required. Install with: pip install httpx")
    sys.exit(1)


@dataclass
class ReportConfig:
    """报告配置"""
    base_url: str = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
    news_base_url: str = "https://np-listapi.eastmoney.com/hotnews-sec"
    timeout: int = 30
    cache_enabled: bool = False
    cache_dir: Path = None
    max_news: int = 5
    
    def __post_init__(self):
        if self.cache_dir is None:
            self.cache_dir = Path("/tmp/stock_report_cache")


def format_stock_code(stock_code: str) -> tuple[str, str]:
    """
    将股票代码转换为所需格式
    返回 (market_stock, secucode)
    """
    code = stock_code.strip().upper()
    
    if '.' in code:
        parts = code.split('.')
        code = parts[0]
        market = parts[1].upper()
    else:
        if code.startswith(('0', '3')):
            market = 'SZ'
        elif code.startswith(('6',)):
            market = 'SH'
        else:
            market = 'SZ'
    
    if market == 'SZ':
        market_stock = f"0.{code}"
    else:
        market_stock = f"1.{code}"
    
    secucode = f"{code}.{market}"
    return market_stock, secucode


class AdvancedStockReportGenerator:
    """高级股票报告生成器"""
    
    def __init__(self, config: ReportConfig = None):
        self.config = config or ReportConfig()
        if self.config.cache_enabled:
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, stock_code: str, data_type: str) -> Path:
        """获取缓存文件路径"""
        return self.config.cache_dir / f"{stock_code}_{data_type}.json"
    
    def _read_cache(self, stock_code: str, data_type: str) -> dict[str, Any] | None:
        """读取缓存"""
        if not self.config.cache_enabled:
            return None
        
        cache_path = self._get_cache_path(stock_code, data_type)
        if cache_path.exists():
            try:
                return json.loads(cache_path.read_text())
            except Exception:
                return None
        return None
    
    def _write_cache(self, stock_code: str, data_type: str, data: dict[str, Any]):
        """写入缓存"""
        if not self.config.cache_enabled:
            return
        
        cache_path = self._get_cache_path(stock_code, data_type)
        try:
            cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"Warning: Failed to write cache: {e}", file=sys.stderr)
    
    async def fetch_data(self, client: httpx.AsyncClient, url: str) -> dict[str, Any] | None:
        """获取API数据"""
        try:
            response = await client.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching data: {e}", file=sys.stderr)
            return None
    
    async def get_hot_news(self, client: httpx.AsyncClient, stock_code: str, market_stock: str) -> dict[str, Any] | None:
        """获取热点新闻"""
        cached = self._read_cache(stock_code, 'hot_news')
        if cached:
            return cached
        
        url = f"{self.config.news_base_url}/stockCompare/listStockHotNews"
        params = {
            'marketStock': market_stock,
            'biz': 'sec_compare',
            'client': 'sec_android'
        }
        url = f"{url}?{urlencode(params)}"
        data = await self.fetch_data(client, url)
        if data:
            self._write_cache(stock_code, 'hot_news', data)
        return data
    
    async def get_stock_info(self, client: httpx.AsyncClient, stock_code: str, secucode: str) -> dict[str, Any] | None:
        """获取股票词汇解释"""
        cached = self._read_cache(stock_code, 'stock_info')
        if cached:
            return cached
        
        params = {
            'reportName': 'RPT_STOCK_WORDS_PK',
            'columns': 'SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,WORDS_EXPLAIN',
            'filter': f'(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '200',
            'source': 'SECURITIES',
            'client': 'APP'
        }
        url = f"{self.config.base_url}?{urlencode(params)}"
        data = await self.fetch_data(client, url)
        if data:
            self._write_cache(stock_code, 'stock_info', data)
        return data
    
    async def get_stock_score(self, client: httpx.AsyncClient, stock_code: str, secucode: str) -> dict[str, Any] | None:
        """获取股票诊断评分"""
        cached = self._read_cache(stock_code, 'stock_score')
        if cached:
            return cached
        
        params = {
            'reportName': 'RPT_STOCK_SCORE_PK',
            'columns': 'SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,DIAGNOSE_DATE,TOTAL_SCORE,'
                      'BASIC_SCORE,MARKET_SCORE,MARKET_FOCUS,TECHNOLOGY_SCORE,FUND_SCORE,'
                      'NEWS_SCORE,CHANGE_RATE,CHANGE_RATE_NEXTDAY,CHANGE_RATE_5DAYS,'
                      'MARKERTNUM,RISEDOWN,DIAGNOSE_TIME',
            'filter': f'(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '200',
            'source': 'SECURITIES',
            'client': 'APP'
        }
        url = f"{self.config.base_url}?{urlencode(params)}"
        data = await self.fetch_data(client, url)
        if data:
            self._write_cache(stock_code, 'stock_score', data)
        return data
    
    async def get_rise_probability(self, client: httpx.AsyncClient, stock_code: str, secucode: str) -> dict[str, Any] | None:
        """获取涨幅概率"""
        cached = self._read_cache(stock_code, 'rise_probability')
        if cached:
            return cached
        
        params = {
            'reportName': 'PRT_STOCK_RISE_PROBABILITY_PK',
            'columns': 'SECUCODE,SECURITY_CODE,SECURITY_INNER_CODE,SECURITY_NAME_ABBR,ORG_CODE,RISECENT',
            'filter': f'(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '200',
            'source': 'SECURITIES',
            'client': 'APP'
        }
        url = f"{self.config.base_url}?{urlencode(params)}"
        data = await self.fetch_data(client, url)
        if data:
            self._write_cache(stock_code, 'rise_probability', data)
        return data
    
    async def get_emotion_score(self, client: httpx.AsyncClient, stock_code: str, secucode: str) -> dict[str, Any] | None:
        """获取情绪评分"""
        cached = self._read_cache(stock_code, 'emotion_score')
        if cached:
            return cached
        
        params = {
            'reportName': 'RPT_YQ_EMOTION_SCORE',
            'columns': 'SECURITY_INNER_CODE,SECURITY_CODE,SECURITY_NAME_ABBR,'
                      'EMOTION_SCORE,START_DATE,END_DATE,SECUCODE',
            'filter': f'(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '200',
            'source': 'SECURITIES',
            'client': 'APP'
        }
        url = f"{self.config.base_url}?{urlencode(params)}"
        data = await self.fetch_data(client, url)
        if data:
            self._write_cache(stock_code, 'emotion_score', data)
        return data
    
    async def fetch_all_data(self, stock_code: str) -> dict[str, Any]:
        """获取所有数据"""
        market_stock, secucode = format_stock_code(stock_code)
        
        async with httpx.AsyncClient() as client:
            results = await asyncio.gather(
                self.get_hot_news(client, stock_code, market_stock),
                self.get_stock_info(client, stock_code, secucode),
                self.get_stock_score(client, stock_code, secucode),
                self.get_rise_probability(client, stock_code, secucode),
                self.get_emotion_score(client, stock_code, secucode),
            )
        
        return {
            'hot_news': results[0],
            'stock_info': results[1],
            'stock_score': results[2],
            'rise_probability': results[3],
            'emotion_score': results[4],
            'stock_code': stock_code,
            'market_stock': market_stock,
            'secucode': secucode,
        }
    
    def generate_markdown(self, data: dict[str, Any]) -> str:
        """生成Markdown格式的报告"""
        lines = []
        lines.append("# 股票综合分析报告")
        lines.append(f"\n生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"股票代码：{data['stock_code']} ({data['secucode']})\n")
        
        # 基本信息
        if data['stock_info'] and data['stock_info'].get('result', {}).get('data'):
            lines.append("## 基本信息")
            stock_data = data['stock_info']['result']['data'][0]
            lines.append(f"**股票名称：** {stock_data.get('SECURITY_NAME_ABBR', 'N/A')}")
            lines.append(f"**市场表现：** {stock_data.get('WORDS_EXPLAIN', 'N/A')}\n")
        
        # 诊断评分
        if data['stock_score'] and data['stock_score'].get('result', {}).get('data'):
            lines.append("## 诊断评分")
            score_data = data['stock_score']['result']['data'][0]
            lines.append(f"**总体评分：** {score_data.get('TOTAL_SCORE', 'N/A')}")
            lines.append(f"**基础评分：** {score_data.get('BASIC_SCORE', 'N/A')}")
            lines.append(f"**市场评分：** {score_data.get('MARKET_SCORE', 'N/A')}")
            lines.append(f"**市场关注：** {score_data.get('MARKET_FOCUS', 'N/A')}")
            lines.append(f"**技术评分：** {score_data.get('TECHNOLOGY_SCORE', 'N/A')}")
            lines.append(f"**资金评分：** {score_data.get('FUND_SCORE', 'N/A')}")
            lines.append(f"**新闻评分：** {score_data.get('NEWS_SCORE', 'N/A')}")
            lines.append(f"**诊断时间：** {score_data.get('DIAGNOSE_TIME', 'N/A')}")
            lines.append(f"**涨跌幅：** {score_data.get('CHANGE_RATE', 'N/A')}%\n")
        
        # 涨幅概率
        if data['rise_probability'] and data['rise_probability'].get('result', {}).get('data'):
            lines.append("## 涨幅概率")
            prob_data = data['rise_probability']['result']['data'][0]
            lines.append(f"**涨幅概率：** {prob_data.get('RISECENT', 'N/A')}%\n")
        
        # 情绪评分
        if data['emotion_score'] and data['emotion_score'].get('result', {}).get('data'):
            lines.append("## 情绪评分")
            emotion_data = data['emotion_score']['result']['data'][0]
            emotion_value = emotion_data.get('EMOTION_SCORE', 'N/A')
            
            if isinstance(emotion_value, (int, float)):
                if emotion_value > 0:
                    emotion_text = f"积极({emotion_value})"
                elif emotion_value < 0:
                    emotion_text = f"消极({emotion_value})"
                else:
                    emotion_text = f"中性({emotion_value})"
            else:
                emotion_text = str(emotion_value)
            
            lines.append(f"**市场情绪：** {emotion_text}")
            lines.append(f"**统计周期：** {emotion_data.get('START_DATE', 'N/A')} 到 {emotion_data.get('END_DATE', 'N/A')}\n")
        
        # 热点新闻
        if data['hot_news'] and data['hot_news'].get('data'):
            lines.append("## 热点新闻")
            news_list = data['hot_news']['data'][:self.config.max_news]
            for idx, news in enumerate(news_list, 1):
                lines.append(f"{idx}. **{news.get('title', 'N/A')}**")
                lines.append(f"   时间：{news.get('showTime', 'N/A')}")
        
        return "\n".join(lines)
    
    def generate_html(self, data: dict[str, Any]) -> str:
        """生成HTML格式的报告"""
        markdown_content = self.generate_markdown(data)
        
        # 简单的Markdown到HTML转换
        html_content = markdown_content.replace('\n\n', '</p><p>')
        html_content = html_content.replace('# ', '<h1>')
        html_content = html_content.replace('## ', '<h2>')
        html_content = html_content.replace('**', '<strong>')
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>股票综合分析报告 - {data['stock_code']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
        h1 {{ color: #0066cc; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }}
        h2 {{ color: #0099ff; margin-top: 20px; }}
        strong {{ color: #cc0000; }}
        p {{ line-height: 1.8; }}
        .header {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>股票综合分析报告</h1>
        <p>股票代码：{data['stock_code']} ({data['secucode']})</p>
        <p>生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    <div class="content">
        {markdown_content}
    </div>
</body>
</html>"""
        return html


async def generate_report(stock_code: str, output_format: str = 'markdown', 
                         output_path: Path = None, config: ReportConfig = None):
    """生成报告"""
    generator = AdvancedStockReportGenerator(config)
    
    print(f"正在获取股票 {stock_code} 的数据...", file=sys.stderr)
    
    try:
        data = await generator.fetch_all_data(stock_code)
        
        if output_format == 'html':
            report = generator.generate_html(data)
        else:
            report = generator.generate_markdown(data)
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report, encoding='utf-8')
            print(f"报告已生成：{output_path}", file=sys.stderr)
            return str(output_path)
        else:
            print(report)
            return None
    
    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        raise


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='高级股票综合分析报告生成器')
    parser.add_argument('--stock', required=True, help='股票代码（如：000333）')
    parser.add_argument('--output', help='输出文件路径')
    parser.add_argument('--format', choices=['markdown', 'html'], default='markdown', help='输出格式')
    parser.add_argument('--timeout', type=int, default=30, help='API超时时间（秒）')
    parser.add_argument('--cache', action='store_true', help='启用数据缓存')
    parser.add_argument('--max-news', type=int, default=5, help='最多显示的新闻条数')
    
    args = parser.parse_args()
    
    stock_code = args.stock.strip()
    if not stock_code:
        print("错误：股票代码不能为空", file=sys.stderr)
        sys.exit(1)
    
    output_path = Path(args.output) if args.output else None
    
    # 检查输出格式和文件扩展名匹配
    if output_path:
        if args.format == 'html' and not output_path.suffix == '.html':
            output_path = output_path.with_suffix('.html')
        elif args.format == 'markdown' and not output_path.suffix in ['.md', '.markdown']:
            output_path = output_path.with_suffix('.md')
    
    config = ReportConfig(
        timeout=args.timeout,
        cache_enabled=args.cache,
        max_news=args.max_news
    )
    
    try:
        result = await generate_report(stock_code, args.format, output_path, config)
        if result:
            print(result)
    except Exception as e:
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
