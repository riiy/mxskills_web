#!/usr/bin/env python3
"""
Stock Report Generator

功能：根据股票代码获取多个API的数据，生成一份可读的综合股票报告
使用方法：python generate_stock_report.py --stock 000333
或：python generate_stock_report.py --stock 000333 --output /path/to/output.md
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

try:
    import httpx
except ImportError:
    print("Error: httpx is required. Install with: pip install httpx")
    sys.exit(1)


# 股票代码格式转换
def format_stock_code(stock_code: str) -> tuple[str, str]:
    """
    将股票代码转换为所需格式
    返回 (market_stock, secucode)
    例如：'000333' -> ('0.000333', '000333.SZ')
    """
    code = stock_code.strip().upper()
    
    # 如果已经包含市场标识，则直接使用
    if '.' in code:
        parts = code.split('.')
        code = parts[0]
        market = parts[1].upper()
    else:
        # 根据开头数字判断市场
        if code.startswith(('0', '3')):
            market = 'SZ'
        elif code.startswith(('6',)):
            market = 'SH'
        else:
            market = 'SZ'
    
    # market_stock 格式：市场代码.代码
    if market == 'SZ':
        market_stock = f"0.{code}"
    else:  # SH
        market_stock = f"1.{code}"
    
    secucode = f"{code}.{market}"
    return market_stock, secucode


REPORT_QUERIES = [
    {
        'key': 'hot_news',
        'name': '热点新闻',
        'base_url': 'https://np-listapi.eastmoney.com/hotnews-sec/stockCompare/listStockHotNews',
        'params': {
            'marketStock': '{market_stock}',
            'biz': 'sec_compare',
            'client': 'sec_android'
        }
    },
    {
        'key': 'stock_info',
        'name': '股票基本信息',
        'params': {
            'reportName': 'RPT_STOCK_WORDS_PK',
            'columns': 'SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,WORDS_EXPLAIN',
            'filter': '(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '200',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'stock_score',
        'name': '诊断评分',
        'params': {
            'reportName': 'RPT_STOCK_SCORE_PK',
            'columns': 'SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,DIAGNOSE_DATE,TOTAL_SCORE,BASIC_SCORE,MARKET_SCORE,MARKET_FOCUS,TECHNOLOGY_SCORE,FUND_SCORE,NEWS_SCORE,CHANGE_RATE,CHANGE_RATE_NEXTDAY,CHANGE_RATE_5DAYS,MARKERTNUM,RISEDOWN,DIAGNOSE_TIME',
            'filter': '(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '200',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'rise_probability',
        'name': '涨幅概率',
        'params': {
            'reportName': 'PRT_STOCK_RISE_PROBABILITY_PK',
            'columns': 'SECUCODE,SECURITY_CODE,SECURITY_INNER_CODE,SECURITY_NAME_ABBR,ORG_CODE,RISECENT',
            'filter': '(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '200',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'emotion_score',
        'name': '情绪评分',
        'params': {
            'reportName': 'RPT_YQ_EMOTION_SCORE',
            'columns': 'SECURITY_INNER_CODE,SECURITY_CODE,SECURITY_NAME_ABBR,EMOTION_SCORE,START_DATE,END_DATE,SECUCODE',
            'filter': '(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '200',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'industry_rank',
        'name': '行业排名',
        'params': {
            'reportName': 'RPT_STCOK_SCORE_INDUSTRY',
            'columns': 'SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,BOARD_CODE,BOARD_NAME,INDUSTRY_RANK',
            'filter': '(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '200',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'concept_list',
        'name': '概念列表',
        'params': {
            'reportName': 'RPTA_APP_CONCEPTLIST',
            'columns': 'CONCEPT,CONCEPT_BOARD_CODE,BOARD_CODE',
            'quoteColumns': 'f3~05~BOARD_CODE~YIELD',
            'pageNumber': '1',
            'pageSize': '1',
            'sortTypes': '-1',
            'sortColumns': 'YIELD',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'attention_labels',
        'name': '关注标签',
        'params': {
            'reportName': 'RPT_STOCK_ATTENTIONLABEL',
            'columns': 'SECUCODE,LABEL_NUM,LABEL_NAME,IS_PERMANMENT,IS_JUMP,GOODBAD',
            'filter': '(SECUCODE="{secucode}")',
            'sortColumns': 'GOODBAD',
            'pageNumber': '1',
            'pageSize': '200',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'market_focus',
        'name': '市场关注趋势',
        'params': {
            'reportName': 'RPT_STOCK_MARKETFOCUS',
            'columns': 'SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,TRADE_DATE,MARKET_FOCUS,MARKET_FOCUS_RANK,TOTAL_MARKET,MARKET_FOCUS_CHANGE,CLOSE_PRICE',
            'filter': '(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '30',
            'sortColumns': 'TRADE_DATE',
            'sortTypes': '-1',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'stock_satisfy',
        'name': '是否满足条件',
        'params': {
            'reportName': 'PRT_STOCK_IS_SATISFY',
            'columns': 'SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,SECURITY_INNER_CODE,ORG_CODE,LISTING_STATE,IS_SATISFY,LISTING_DATE',
            'filter': '(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '200',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'participation',
        'name': '市场参与度',
        'params': {
            'reportName': 'RPT_STOCK_PARTICIPATION',
            'columns': 'SECURITY_CODE,TRADE_DATE,PARTICIPATION_WISH,PARTICIPATION_WISH_5DAYS,PARTICIPATION_WISH_CHANGE,PARTICIPATION_WISH_5DAYSCHANGE',
            'filter': '(SECURITY_CODE="{security_code}")',
            'sortColumns': 'TRADE_DATE',
            'sortTypes': '1',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'trend_volume',
        'name': '趋势成交量',
        'params': {
            'reportName': 'RPT_STOCK_TRENDVOLUME_PK',
            'columns': 'SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,PRICE_AVG_RELATION,VOLUME_JUDGE,PAR_FOCUS,PRESSURE_LEVEL,SUPPORT_LEVEL,AVG_PRICE,DEAL_AMOUNT,AVG_AMOUNT_5DAYS,DAILY_TRADE_60TD,WORDS_EXPLAIN,TRADE_DATE',
            'filter': '(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '200',
            'sortTypes': '1',
            'sortColumns': 'TRADE_DATE',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'macd',
        'name': 'MACD等技术指标',
        'params': {
            'reportName': 'PRT_STOCK_MACD_PK',
            'columns': 'MACD,MACDCOUT,MACDCLOR,KDJOUT,KDJCLOR,RSIOUT,RSICLOR,BOLLOUT,BOLLCLOR,BIASOUT,BIASCLOR,WROUT,WRCLOR',
            'filter': '(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '60',
            'sortTypes': '-1',
            'sortColumns': 'TRADEDATE',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'concept_board',
        'name': '概念板块排名',
        'params': {
            'reportName': 'RPT_YQ_CONCEPT_BOARD',
            'columns': 'SECUCODE,BOARD_CODE,BOARD_CODE_APP,BOARD_NAME,RN',
            'quoteColumns': 'THREE_INCREASE~17~BOARD_CODE,OVER_CSI300~17~BOARD_CODE,HIGHDAYSN~17~BOARD_CODE',
            'filter': '(SECUCODE="{secucode}")',
            'sortColumns': 'THREE_INCREASE',
            'sortTypes': '-1',
            'pageNumber': '1',
            'pageSize': '6',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'capitalflows_trade',
        'name': '资金流向（历史）',
        'params': {
            'reportName': 'PRT_STOCK_CAPITALFLOWS',
            'columns': 'SECUCODE,TRADE_DATE,CAPITAL_FLOWS,CAPITAL_FLOWS_5DAYS,CAPITAL_FLOWS_RATIO,CAPITAL_FLOWS_5DAYSRATIO',
            'filter': '(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '5',
            'sortTypes': '-1',
            'sortColumns': 'TRADE_DATE',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'capitalflows_board',
        'name': '资金流向（板块）',
        'params': {
            'reportName': 'PRT_STOCK_CAPITALFLOWS',
            'columns': 'SECUCODE,TRADE_DATE,BOARD_CAPITAL_FLOWS,BOARD_CAPITAL_5FLOWS,BOARD_CODE,BOARD_NAME',
            'filter': '(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '5',
            'sortTypes': '-1',
            'sortColumns': 'TRADE_DATE',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'active_region',
        'name': '活跃区域',
        'params': {
            'reportName': 'RPT_STOCK_ACTIVEREGION',
            'columns': 'SECURITY_CODE,ACTIVE_REGION,REGION_CHANGERATE,VOLUME_RATIO,BUYER_VOLUME,CHANGE_RATE,ACTIVE_PRICE,AVERAGE_PRICE',
            'filter': '(SECURITY_CODE="{security_code}")',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'lhr_5days',
        'name': '龙虎榜5日',
        'params': {
            'reportName': 'RPT_STOCK_LHB5DAYS',
            'columns': 'SECUCODE,TRADE_DATE,BUY_AMT,SELL_AMT,NET_AMT,FIRST_BUY_AMT,FIRST_SELL_AMT,BUY_FREERATIO,SELL_FREERATIO,BUY_ORG,SELL_ORG',
            'filter': '(SECUCODE="{secucode}")',
            'sortTypes': '1',
            'sortColumns': 'TRADE_DATE',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'fn_radar',
        'name': '财务雷达',
        'params': {
            'reportName': 'RPT_STOCK_FNRADAR_PK',
            'columns': 'SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,REPORT_DATE,REPORT_TYPE,WEIGHT_ROE,WEIGHT_ROE_RANK,NETPROFIT_YOY_RATIO,NYR_RANK,TOTAL_ASSETS_TR,TATR_RANK,SALE_CASH_RATIO,SCR_RANK,DEBT_ASSET_RATIO,DAR_RANK,LABEL_EXPLAIN',
            'filter': '(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '200',
            'sortTypes': '-1',
            'sortColumns': 'REPORT_DATE',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'billboard_times',
        'name': '公告板块热度',
        'params': {
            'reportName': 'RPT_STOCK_BILLBOARDTIMES',
            'columns': 'SECUCODE,BILLBOARD_FREQUENCY,BILLBOARD_BUY_AMT,BILLBOARD_SELL_AMT,BILLBOARD_NET_AMT',
            'filter': '(SECUCODE="{secucode}")',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'margin_trend_explain',
        'name': '融资融券趋势说明',
        'params': {
            'reportName': 'RPT_STOCK_MARGINTRENDEXPLAIN',
            'columns': 'SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,EXPLAIN',
            'filter': '(SECUCODE="{secucode}")',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'minesweeper_summarize_v1',
        'name': '风险扫雷汇总1',
        'params': {
            'reportName': 'RPT_CUSTOM_RISK_MINESWEEPER_SUMMARIZE',
            'filter': '(SECUCODE="{secucode}")',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'minesweeper_summarize_v2',
        'name': '风险扫雷汇总2',
        'params': {
            'reportName': 'RPT_CUSTOM_RISK_MINESWEEPER_SUMMARIZE',
            'filter': '(SECUCODE="{secucode}")',
            'source': 'SECURITIES',
            'client': 'APP',
            'v': '06365503481874877'
        }
    },
    {
        'key': 'margin_trend',
        'name': '融资融券趋势',
        'params': {
            'reportName': 'RPT_STOCK_MARGINTREND',
            'columns': 'SECUCODE,TRADE_DATE,FIN_BALANCE_DIFF,FREE_RATIO,FINBALANCE_DIFF_CHANGE,AVG_FREE_RATIO,FIN_BALANCE,LOAN_BALANCE,EXPLAIN',
            'filter': '(SECUCODE="{secucode}")',
            'sortTypes': '1',
            'sortColumns': 'TRADE_DATE',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'minesweeper',
        'name': '风险扫雷明细',
        'params': {
            'reportName': 'RPT_CUSTOM_RISK_MINESWEEPER',
            'filter': '(SECUCODE="{secucode}")',
            'client': 'APP',
            'source': 'SECURITIES',
            'v': '004491793660595722'
        }
    },
    {
        'key': 'balanced_picture',
        'name': '资金平衡图',
        'params': {
            'reportName': 'RPT_APP_BALANCED_PICTURE',
            'columns': 'SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,LABEL_DATE,SIGNAL_OTHER_NAME,SIGNAL_RISK_SCORE,TYPE,SIGNAL_NAME_EXPLAIN',
            'filter': '(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '200',
            'sortTypes': '1',
            'sortColumns': 'SECUCODE',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'f10_org_basicinfo_v1',
        'name': '公司基本信息1',
        'params': {
            'reportName': 'RPT_F10_ORG_BASICINFO',
            'columns': 'SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,SECURITY_TYPE_CODE,SECURITY_PINYIN,LISTING_DATE,TRADE_MARKET,TRADE_MARKET_CODE,SECURITY_INNER_CODE,ORG_CODE,LISTING_STATE,SECURITY_TYPE,ORG_TYPE,CODE_TYPE,ORG_TYPE_CODE',
            'filter': '(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '200',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'f10_org_basicinfo_v2',
        'name': '公司基本信息2',
        'params': {
            'reportName': 'RPT_F10_ORG_BASICINFO',
            'columns': 'SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,SECURITY_TYPE_CODE,SECURITY_PINYIN,LISTING_DATE,TRADE_MARKET,TRADE_MARKET_CODE,SECURITY_INNER_CODE,ORG_CODE,LISTING_STATE,SECURITY_TYPE,ORG_TYPE,CODE_TYPE,ORG_TYPE_CODE',
            'filter': '(SECUCODE="{secucode}")',
            'client': 'APP',
            'source': 'SECURITIES',
            'pageNumber': '1',
            'pageSize': '200',
            'sr': '-1',
            'v': '08407980787603606'
        }
    },
    {
        'key': 'stockboard_rank_board',
        'name': '板块资金排名（板块）',
        'params': {
            'reportName': 'RPT_STOCKBOARD_RANK',
            'columns': 'BOARD_CODE,BOARD_NAME,SECUCODE,SECURITY_NAME_ABBR,CAPITAL_FLOWS,CAPITAL_FLOWS_RANK',
            'filter': '(BOARD_CODE="{board_code}")',
            'pageNumber': '1',
            'pageSize': '3',
            'sortTypes': '1',
            'sortColumns': 'CAPITAL_FLOWS_RANK',
            'source': 'SECURITIES',
            'client': 'APP'
        },
        'needs_board_code': True
    },
    {
        'key': 'stockboard_rank_stock',
        'name': '板块资金排名（标的）',
        'params': {
            'reportName': 'RPT_STOCKBOARD_RANK',
            'columns': 'BOARD_CODE,BOARD_NAME,SECUCODE,SECURITY_NAME_ABBR,CAPITAL_FLOWS,CAPITAL_FLOWS_RANK',
            'filter': '(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '1',
            'source': 'SECURITIES',
            'client': 'APP'
        }
    },
    {
        'key': 'risk_minesweeper_fnview',
        'name': '风险扫雷视图',
        'params': {
            'reportName': 'RPT_RISK_MINESWEEPER_FNVIEW',
            'columns': 'SECUCODE,SECURITY_CODE,REPORT_DATE,REPORT_LABEL,REPORT_LABEL_DETAILS,GOODWILL,GW_NA_RATIO',
            'filter': '(SECUCODE="{secucode}")',
            'client': 'APP',
            'source': 'SECURITIES',
            'sortTypes': '1',
            'sortColumns': 'REPORT_DATE',
            'v': '009224708917091584'
        }
    }
]


class StockReportGenerator:
    """股票报告生成器"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.base_url = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
        self.news_base_url = "https://np-listapi.eastmoney.com/hotnews-sec"
        
    async def fetch_data(self, client: httpx.AsyncClient, url: str) -> dict[str, Any] | None:
        """获取API数据"""
        try:
            response = await client.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching {url}: {e}", file=sys.stderr)
            return None
    
    async def get_hot_news(self, client: httpx.AsyncClient, market_stock: str) -> dict[str, Any] | None:
        """获取热点新闻"""
        url = f"{self.news_base_url}/stockCompare/listStockHotNews"
        params = {
            'marketStock': market_stock,
            'biz': 'sec_compare',
            'client': 'sec_android'
        }
        url = f"{url}?{urlencode(params)}"
        return await self.fetch_data(client, url)
    
    async def get_stock_info(self, client: httpx.AsyncClient, secucode: str) -> dict[str, Any] | None:
        """获取股票词汇解释"""
        params = {
            'reportName': 'RPT_STOCK_WORDS_PK',
            'columns': 'SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,WORDS_EXPLAIN',
            'filter': f'(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '200',
            'source': 'SECURITIES',
            'client': 'APP'
        }
        url = f"{self.base_url}?{urlencode(params)}"
        return await self.fetch_data(client, url)
    
    async def get_stock_score(self, client: httpx.AsyncClient, secucode: str) -> dict[str, Any] | None:
        """获取股票诊断评分"""
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
        url = f"{self.base_url}?{urlencode(params)}"
        return await self.fetch_data(client, url)
    
    async def get_rise_probability(self, client: httpx.AsyncClient, secucode: str) -> dict[str, Any] | None:
        """获取涨幅概率"""
        params = {
            'reportName': 'PRT_STOCK_RISE_PROBABILITY_PK',
            'columns': 'SECUCODE,SECURITY_CODE,SECURITY_INNER_CODE,SECURITY_NAME_ABBR,ORG_CODE,RISECENT',
            'filter': f'(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '200',
            'source': 'SECURITIES',
            'client': 'APP'
        }
        url = f"{self.base_url}?{urlencode(params)}"
        return await self.fetch_data(client, url)
    
    async def get_emotion_score(self, client: httpx.AsyncClient, secucode: str) -> dict[str, Any] | None:
        """获取情绪评分"""
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
        url = f"{self.base_url}?{urlencode(params)}"
        return await self.fetch_data(client, url)

    async def get_industry_rank(self, client: httpx.AsyncClient, secucode: str) -> dict[str, Any] | None:
        """获取行业排名"""
        params = {
            'reportName': 'RPT_STCOK_SCORE_INDUSTRY',
            'columns': 'SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,BOARD_CODE,BOARD_NAME,INDUSTRY_RANK',
            'filter': f'(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '200',
            'source': 'SECURITIES',
            'client': 'APP'
        }
        url = f"{self.base_url}?{urlencode(params)}"
        return await self.fetch_data(client, url)

    async def get_attention_labels(self, client: httpx.AsyncClient, secucode: str) -> dict[str, Any] | None:
        """获取关注标签"""
        params = {
            'reportName': 'RPT_STOCK_ATTENTIONLABEL',
            'columns': 'SECUCODE,LABEL_NUM,LABEL_NAME,IS_PERMANMENT,IS_JUMP,GOODBAD',
            'filter': f'(SECUCODE="{secucode}")',
            'sortColumns': 'GOODBAD',
            'pageNumber': '1',
            'pageSize': '200',
            'source': 'SECURITIES',
            'client': 'APP'
        }
        url = f"{self.base_url}?{urlencode(params)}"
        return await self.fetch_data(client, url)

    async def get_market_focus(self, client: httpx.AsyncClient, secucode: str) -> dict[str, Any] | None:
        """获取市场关注趋势"""
        params = {
            'reportName': 'RPT_STOCK_MARKETFOCUS',
            'columns': 'SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,TRADE_DATE,MARKET_FOCUS,MARKET_FOCUS_RANK,TOTAL_MARKET,MARKET_FOCUS_CHANGE,CLOSE_PRICE',
            'filter': f'(SECUCODE="{secucode}")',
            'pageNumber': '1',
            'pageSize': '30',
            'sortColumns': 'TRADE_DATE',
            'sortTypes': '-1',
            'source': 'SECURITIES',
            'client': 'APP'
        }
        url = f"{self.base_url}?{urlencode(params)}"
        return await self.fetch_data(client, url)
    
    async def fetch_report(self, client: httpx.AsyncClient, query: dict[str, Any], context: dict[str, str]) -> dict[str, Any] | None:
        params = {}
        for key, value in query['params'].items():
            if isinstance(value, str):
                params[key] = value.format(**context)
            else:
                params[key] = value

        url = f"{query.get('base_url', self.base_url)}?{urlencode(params)}"
        return await self.fetch_data(client, url)

    async def fetch_all_data(self, stock_code: str) -> dict[str, Any]:
        """获取所有数据"""
        market_stock, secucode = format_stock_code(stock_code)
        security_code = stock_code.strip().split('.')[0]
        context = {
            'market_stock': market_stock,
            'secucode': secucode,
            'security_code': security_code,
            'board_code': ''
        }

        results: dict[str, Any] = {}
        queries_to_fetch = [q for q in REPORT_QUERIES if not q.get('needs_board_code')]

        async with httpx.AsyncClient() as client:
            tasks = [self.fetch_report(client, query, context) for query in queries_to_fetch]
            responses = await asyncio.gather(*tasks)

        for query, response in zip(queries_to_fetch, responses):
            results[query['key']] = response

        board_query = next((q for q in REPORT_QUERIES if q.get('key') == 'stockboard_rank_board'), None)
        industry_rank = results.get('industry_rank')
        board_code = None
        if industry_rank and isinstance(industry_rank, dict):
            data = industry_rank.get('result', {}).get('data')
            if isinstance(data, list) and data:
                board_code = data[0].get('BOARD_CODE')
                context['board_code'] = board_code

        if board_query and board_code:
            async with httpx.AsyncClient() as client:
                results[board_query['key']] = await self.fetch_report(client, board_query, context)

        results['stock_code'] = stock_code
        results['market_stock'] = market_stock
        results['secucode'] = secucode
        results['security_code'] = security_code

        return results
    
    def _describe_score(self, name: str, score: Any) -> str:
        if score is None or score == 'N/A':
            return f"**{name}：** N/A"
        try:
            value = float(score)
        except (TypeError, ValueError):
            return f"**{name}：** {score}"

        if value >= 85:
            level = '很强'
        elif value >= 70:
            level = '较好'
        elif value >= 55:
            level = '一般'
        else:
            level = '偏弱'
        return f"**{name}：** {value} ({level})"

    def _describe_probability(self, value: Any) -> str:
        if value is None or value == 'N/A':
            return '**涨幅概率：** N/A'
        try:
            rate = float(value)
        except (TypeError, ValueError):
            return f'**涨幅概率：** {value}'
        if rate >= 60:
            desc = '偏高，短期看多情绪较强'
        elif rate >= 45:
            desc = '中性，市场预期较为平衡'
        else:
            desc = '偏低，市场谨慎情绪较浓'
        return f'**涨幅概率：** {rate}% ({desc})'

    def _describe_emotion(self, emotion_value: Any) -> str:
        if emotion_value is None or emotion_value == 'N/A':
            return '**市场情绪：** N/A'
        try:
            value = float(emotion_value)
        except (TypeError, ValueError):
            return f'**市场情绪：** {emotion_value}'
        if value > 5:
            label = '积极'
        elif value > 0:
            label = '偏积极'
        elif value == 0:
            label = '中性'
        elif value >= -5:
            label = '偏消极'
        else:
            label = '消极'
        return f'**市场情绪：** {label} ({value})'

    def _summarize_attention(self, labels: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
        positive = []
        negative = []
        for item in labels:
            label_name = item.get('LABEL_NAME', 'N/A')
            goodbad = str(item.get('GOODBAD', '')).strip()
            text = f"{label_name} ({'常驻' if item.get('IS_PERMANMENT') == '1' else '临时'} / {'跳转' if item.get('IS_JUMP') == '1' else '常规'})"
            if goodbad == '正面':
                positive.append(text)
            elif goodbad == '负面':
                negative.append(text)
            else:
                positive.append(text)
        return positive, negative

    def _join_labels(self, labels: list[str]) -> str:
        if not labels:
            return '无'
        return '、'.join(labels[:5])

    def generate_llm_evaluation(self, data: dict[str, Any]) -> str:
        """生成更结构化的LLM评估段落"""
        rows = []
        stock_name = 'N/A'
        if data['stock_info'] and data['stock_info'].get('result', {}).get('data'):
            stock_name = data['stock_info']['result']['data'][0].get('SECURITY_NAME_ABBR', 'N/A')

        rows.append(f"标的名称：{stock_name}")
        rows.append(f"标的代码：{data['secucode']}")

        score_data = None
        if data['stock_score'] and data['stock_score'].get('result', {}).get('data'):
            score_data = data['stock_score']['result']['data'][0]
            rows.append(f"总体评分：{score_data.get('TOTAL_SCORE', 'N/A')}，基础评分：{score_data.get('BASIC_SCORE', 'N/A')}，市场评分：{score_data.get('MARKET_SCORE', 'N/A')}，技术评分：{score_data.get('TECHNOLOGY_SCORE', 'N/A')}，资金评分：{score_data.get('FUND_SCORE', 'N/A')}，新闻评分：{score_data.get('NEWS_SCORE', 'N/A')}")
            rows.append(f"诊断时间：{score_data.get('DIAGNOSE_TIME', 'N/A')}，今日涨跌：{score_data.get('CHANGE_RATE', 'N/A')}%，近1日/5日变化：{score_data.get('CHANGE_RATE_NEXTDAY', 'N/A')}% / {score_data.get('CHANGE_RATE_5DAYS', 'N/A')}%")
            rows.append(f"市场关注排名：{score_data.get('MARKERTNUM', 'N/A')}，涨跌趋势：{'上涨' if str(score_data.get('RISEDOWN')) == '1' else '下跌' if str(score_data.get('RISEDOWN')) == '-1' else '未知'}")

        if data['industry_rank'] and data['industry_rank'].get('result', {}).get('data'):
            industry_data = data['industry_rank']['result']['data'][0]
            rows.append(f"所属板块：{industry_data.get('BOARD_NAME', 'N/A')}，行业排名：{industry_data.get('INDUSTRY_RANK', 'N/A')}")

        if data['attention_labels'] and data['attention_labels'].get('result', {}).get('data'):
            labels = data['attention_labels']['result']['data']
            positive, negative = self._summarize_attention(labels)
            rows.append(f"正面标签：{self._join_labels(positive)}")
            rows.append(f"负面标签：{self._join_labels(negative)}")

        if data['market_focus'] and data['market_focus'].get('result', {}).get('data'):
            focus_rows = data['market_focus']['result']['data'][:5]
            focus_summary = []
            for row in focus_rows:
                focus_summary.append(f"{row.get('TRADE_DATE', 'N/A')}关注度{row.get('MARKET_FOCUS', 'N/A')}排名{row.get('MARKET_FOCUS_RANK', 'N/A')}收盘{row.get('CLOSE_PRICE', 'N/A')}")
            rows.append(f"市场关注趋势：{'; '.join(focus_summary)}")

        if data['rise_probability'] and data['rise_probability'].get('result', {}).get('data'):
            prob = data['rise_probability']['result']['data'][0].get('RISECENT', 'N/A')
            rows.append(f"涨幅概率：{prob}%")

        if data['emotion_score'] and data['emotion_score'].get('result', {}).get('data'):
            emotion_value = data['emotion_score']['result']['data'][0].get('EMOTION_SCORE', 'N/A')
            rows.append(f"市场情绪：{emotion_value}（{'消极' if isinstance(emotion_value, (int, float)) and emotion_value < 0 else '积极' if isinstance(emotion_value, (int, float)) and emotion_value > 0 else '中性' if emotion_value == 0 else emotion_value}）")

        if data['hot_news'] and data['hot_news'].get('data'):
            news_titles = [news.get('title', 'N/A') for news in data['hot_news']['data'][:5]]
            rows.append(f"热点新闻：{'; '.join(news_titles)}")

        result = '；'.join(rows)
        if score_data:
            result += '。请基于上述信息直接给出一句简明诊断。'
        return result

    def _render_rows(self, title: str, result: dict[str, Any] | None, max_items: int = 5) -> list[str]:
        report = [f'## {title}']
        if not result:
            report.append('无数据')
            report.append('')
            return report

        rows = None
        if isinstance(result, dict):
            rows = (result.get('result') or {}).get('data') or result.get('data')
        if rows is None:
            report.append('无数据')
            report.append('')
            return report

        if isinstance(rows, dict):
            rows = [rows]
        if not isinstance(rows, list) or len(rows) == 0:
            report.append('无数据')
            report.append('')
            return report

        display_rows = rows[:max_items]
        for idx, row in enumerate(display_rows, 1):
            report.append(f'### 条目 {idx}')
            for key, value in row.items():
                report.append(f'- **{key}**: {value}')
        if len(rows) > max_items:
            report.append(f'...共 {len(rows)} 条记录，仅展示前 {max_items} 条。')
        report.append('')
        return report

    def generate_report(self, data: dict[str, Any]) -> str:
        """生成Markdown格式的报告"""
        report = []
        report.append('# 股票综合分析报告')
        report.append(f'生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        report.append(f'股票代码：{data.get("stock_code", "N/A")} ({data.get("secucode", "N/A")})')

        stock_name = 'N/A'
        if data.get('stock_info') and data['stock_info'].get('result', {}).get('data'):
            stock_data = data['stock_info']['result']['data'][0]
            stock_name = stock_data.get('SECURITY_NAME_ABBR', 'N/A')
        report.append(f'**标的名称：** {stock_name}')
        report.append(f'**标的代码：** {data.get("secucode", "N/A")}')
        report.append('')

        if data.get('stock_score') and data['stock_score'].get('result', {}).get('data'):
            score_data = data['stock_score']['result']['data'][0]
            report.append('## 核心结论')
            report.append(self._describe_score('总体评分', score_data.get('TOTAL_SCORE', 'N/A')))
            report.append(self._describe_score('基础评分', score_data.get('BASIC_SCORE', 'N/A')))
            report.append(self._describe_score('市场评分', score_data.get('MARKET_SCORE', 'N/A')))
            report.append(self._describe_score('技术评分', score_data.get('TECHNOLOGY_SCORE', 'N/A')))
            report.append(self._describe_score('资金评分', score_data.get('FUND_SCORE', 'N/A')))
            report.append(self._describe_score('新闻评分', score_data.get('NEWS_SCORE', 'N/A')))
            report.append(self._describe_probability(data.get('rise_probability', {}).get('result', {}).get('data', [{}])[0].get('RISECENT', 'N/A') if data.get('rise_probability') else 'N/A'))
            report.append(self._describe_emotion(data.get('emotion_score', {}).get('result', {}).get('data', [{}])[0].get('EMOTION_SCORE', 'N/A') if data.get('emotion_score') else 'N/A'))
            report.append('')

        if data.get('stock_info') and data['stock_info'].get('result', {}).get('data'):
            report.append('## 基本信息')
            stock_data = data['stock_info']['result']['data'][0]
            report.append(f'**股票名称：** {stock_data.get("SECURITY_NAME_ABBR", "N/A")}')
            report.append(f'**市场描述：** {stock_data.get("WORDS_EXPLAIN", "N/A")}')
            report.append('')

        report.append('## 全量数据列表')
        for query in REPORT_QUERIES:
            report.extend(self._render_rows(query['name'], data.get(query['key']), max_items=5))

        return '\n'.join(report)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成股票综合分析报告')
    parser.add_argument('--stock', required=True, help='股票代码（如：000333）')
    parser.add_argument('--output', help='输出文件路径（如不指定则打印到控制台）')
    parser.add_argument('--timeout', type=int, default=30, help='API超时时间（秒）')
    parser.add_argument('--mode', choices=['llm', 'full'], default='full', help='输出模式，默认 full，输出完整Markdown数据报告；llm 输出结构化LLM评估段落')
    
    args = parser.parse_args()
    
    # 验证股票代码
    stock_code = args.stock.strip()
    if not stock_code:
        print("错误：股票代码不能为空", file=sys.stderr)
        sys.exit(1)
    
    print(f"正在获取股票 {stock_code} 的数据...", file=sys.stderr)
    
    generator = StockReportGenerator(timeout=args.timeout)
    
    try:
        # 获取所有数据
        data = await generator.fetch_all_data(stock_code)
        
        # 生成报告
        if args.mode == 'full':
            report = generator.generate_report(data)
        else:
            report = generator.generate_llm_evaluation(data)
        
        # 输出报告
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report, encoding='utf-8')
            print(f"报告已生成：{output_path}", file=sys.stderr)
            print(output_path)
        else:
            print(report)
    
    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
