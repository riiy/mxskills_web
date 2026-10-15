#!/usr/bin/env python3
"""
批量股票报告生成器

使用方法：
1. 编辑 stocks_to_report.json 配置要生成报告的股票列表
2. 运行：python batch_stock_reports.py

或者直接指定股票列表：
python batch_stock_reports.py --stocks 000333 600000 000001
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any
from datetime import datetime

# 导入报告生成器
import importlib.util

spec = importlib.util.spec_from_file_location("advanced_stock_report", "advanced_stock_report.py")
report_module = importlib.util.module_from_spec(spec)


class BatchStockReportGenerator:
    """批量股票报告生成器"""
    
    def __init__(self, output_dir: Path = None, format_type: str = 'markdown'):
        self.output_dir = output_dir or Path('./reports')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.format_type = format_type
        self.results = []
    
    async def generate_report(self, stock_code: str, use_cache: bool = False) -> dict[str, Any]:
        """生成单个股票的报告"""
        try:
            # 导入模块
            spec = importlib.util.spec_from_file_location(
                "advanced_stock_report", 
                Path(__file__).parent / "advanced_stock_report.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 创建输出路径
            if self.format_type == 'html':
                output_file = self.output_dir / f"{stock_code}.html"
            else:
                output_file = self.output_dir / f"{stock_code}.md"
            
            # 使用高级报告生成器
            config = module.ReportConfig(
                cache_enabled=use_cache,
                timeout=30
            )
            
            await module.generate_report(
                stock_code,
                self.format_type,
                output_file,
                config
            )
            
            return {
                'stock_code': stock_code,
                'status': 'success',
                'output_file': str(output_file),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'stock_code': stock_code,
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def generate_batch(self, stock_codes: list[str], use_cache: bool = False) -> list[dict[str, Any]]:
        """批量生成报告"""
        print(f"开始生成 {len(stock_codes)} 个股票的报告...\n", file=sys.stderr)
        
        tasks = [self.generate_report(code, use_cache) for code in stock_codes]
        results = await asyncio.gather(*tasks)
        
        self.results = results
        return results
    
    def print_summary(self):
        """打印统计摘要"""
        successful = [r for r in self.results if r['status'] == 'success']
        failed = [r for r in self.results if r['status'] == 'failed']
        
        print("\n" + "="*60, file=sys.stderr)
        print("报告生成完成", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print(f"\n统计信息：", file=sys.stderr)
        print(f"  总数：{len(self.results)}", file=sys.stderr)
        print(f"  成功：{len(successful)}", file=sys.stderr)
        print(f"  失败：{len(failed)}", file=sys.stderr)
        
        if successful:
            print(f"\n✓ 成功生成的报告：", file=sys.stderr)
            for result in successful:
                print(f"  - {result['stock_code']}: {result['output_file']}", file=sys.stderr)
        
        if failed:
            print(f"\n✗ 失败的报告：", file=sys.stderr)
            for result in failed:
                print(f"  - {result['stock_code']}: {result['error']}", file=sys.stderr)
        
        print(f"\n报告已保存到: {self.output_dir.absolute()}", file=sys.stderr)


def load_config(config_file: Path) -> list[str]:
    """从配置文件加载股票列表"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            return data.get('stocks', [])
        elif isinstance(data, list):
            return data
        else:
            print(f"错误：配置文件格式不正确", file=sys.stderr)
            return []
    except FileNotFoundError:
        print(f"配置文件不存在: {config_file}", file=sys.stderr)
        return []
    except json.JSONDecodeError:
        print(f"JSON解析错误: {config_file}", file=sys.stderr)
        return []


def create_sample_config(config_file: Path):
    """创建示例配置文件"""
    sample_config = {
        "stocks": [
            "000333",  # 美的集团
            "600000",  # 浦发银行
            "000001",  # 平安银行
            "000858",  # 五粮液
            "601398"   # 工商银行
        ],
        "description": "股票报告配置文件"
    }
    
    config_file.write_text(json.dumps(sample_config, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"示例配置文件已生成: {config_file}", file=sys.stderr)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='批量生成股票综合分析报告')
    parser.add_argument('--stocks', nargs='+', help='股票代码列表（空格分隔）')
    parser.add_argument('--config', type=Path, default='stocks_to_report.json', help='配置文件路径')
    parser.add_argument('--output', type=Path, default='./reports', help='输出目录')
    parser.add_argument('--format', choices=['markdown', 'html'], default='markdown', help='输出格式')
    parser.add_argument('--cache', action='store_true', help='启用缓存')
    parser.add_argument('--create-sample', action='store_true', help='创建示例配置文件')
    
    args = parser.parse_args()
    
    # 创建示例配置
    if args.create_sample:
        create_sample_config(args.config)
        return
    
    # 获取股票列表
    stocks = args.stocks
    if not stocks:
        stocks = load_config(args.config)
    
    if not stocks:
        print("错误：没有指定股票代码", file=sys.stderr)
        print("\n使用方法：", file=sys.stderr)
        print("  1. python batch_stock_reports.py --stocks 000333 600000", file=sys.stderr)
        print("  2. 或在 stocks_to_report.json 中配置股票列表", file=sys.stderr)
        print("\n生成示例配置：", file=sys.stderr)
        print("  python batch_stock_reports.py --create-sample", file=sys.stderr)
        sys.exit(1)
    
    # 生成报告
    generator = BatchStockReportGenerator(args.output, args.format)
    results = await generator.generate_batch(stocks, args.cache)
    
    # 打印摘要
    generator.print_summary()
    
    # 返回结果JSON
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    asyncio.run(main())
