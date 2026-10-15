from __future__ import annotations

from collections import defaultdict
from typing import Iterable
from urllib.parse import parse_qs, urlparse


urls = '''
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=PRT_STOCK_IS_SATISFY&columns=SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,SECURITY_INNER_CODE,ORG_CODE,LISTING_STATE,IS_SATISFY,LISTING_DATE&filter=(SECUCODE%3D%22000333.SZ%22)&pageNumber=1&pageSize=200&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_STOCK_SCORE_PK&columns=SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,DIAGNOSE_DATE,TOTAL_SCORE,BASIC_SCORE,MARKET_SCORE,MARKET_FOCUS,TECHNOLOGY_SCORE,FUND_SCORE,NEWS_SCORE,CHANGE_RATE,CHANGE_RATE_NEXTDAY,CHANGE_RATE_5DAYS,MARKERTNUM,RISEDOWN,DIAGNOSE_TIME&filter=(SECUCODE%3D%22000333.SZ%22)&pageNumber=1&pageSize=200&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_STCOK_SCORE_INDUSTRY&columns=SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,BOARD_CODE,BOARD_NAME,INDUSTRY_RANK&filter=(SECUCODE%3D%22000333.SZ%22)&pageNumber=1&pageSize=200&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_STOCK_WORDS_PK&columns=SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,WORDS_EXPLAIN&filter=(SECUCODE%3D%22000333.SZ%22)&pageNumber=1&pageSize=200&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=PRT_STOCK_RISE_PROBABILITY_PK&columns=SECUCODE,SECURITY_CODE,SECURITY_INNER_CODE,SECURITY_NAME_ABBR,ORG_CODE,RISECENT&filter=(SECUCODE%3D%22000333.SZ%22)&pageNumber=1&pageSize=200&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_STOCK_ATTENTIONLABEL&columns=SECUCODE,LABEL_NUM,LABEL_NAME,IS_PERMANMENT,IS_JUMP,GOODBAD&filter=(SECUCODE%3D%22000333.SZ%22)&sortColumns=GOODBAD&pageNumber=1&pageSize=200&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_YQ_EMOTION_SCORE&columns=SECURITY_INNER_CODE,SECURITY_CODE,SECURITY_NAME_ABBR,EMOTION_SCORE,START_DATE,END_DATE,SECUCODE&filter=(SECUCODE%3D%22000333.SZ%22)&pageNumber=1&pageSize=200&source=SECURITIES&client=APP
https://np-listapi.eastmoney.com/hotnews-sec/stockCompare/listStockHotNews?marketStock=0.000333&biz=sec_compare&client=sec_android&req_trace=gp5lC0mN0y8o9mImcUCpP3VC1Sz2yFg9
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_YQ_CONCEPT_BOARD&columns=SECUCODE,BOARD_CODE,BOARD_CODE_APP,BOARD_NAME,RN&quoteColumns=THREE_INCREASE~17~BOARD_CODE,OVER_CSI300~17~BOARD_CODE,HIGHDAYSN~17~BOARD_CODE&filter=(SECUCODE%3D%22000333.SZ%22)&sortColumns=THREE_INCREASE&sortTypes=-1&pageNumber=1&pageSize=6&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPTA_APP_CONCEPTLIST&columns=CONCEPT,CONCEPT_BOARD_CODE,BOARD_CODE&quoteColumns=f3~05~BOARD_CODE~YIELD&pageNumber=1&pageSize=1&sortTypes=-1&sortColumns=YIELD&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_STOCK_MARKETFOCUS&columns=SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,TRADE_DATE,MARKET_FOCUS,MARKET_FOCUS_RANK,TOTAL_MARKET,MARKET_FOCUS_CHANGE,CLOSE_PRICE&filter=(SECUCODE%3D%22000333.SZ%22)&pageNumber=1&pageSize=30&sortColumns=TRADE_DATE&sortTypes=-1&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_STOCK_PARTICIPATION&columns=SECURITY_CODE,TRADE_DATE,PARTICIPATION_WISH,PARTICIPATION_WISH_5DAYS,PARTICIPATION_WISH_CHANGE,PARTICIPATION_WISH_5DAYSCHANGE&filter=(SECURITY_CODE%3D%22000333%22)&sortColumns=TRADE_DATE&sortTypes=1&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_STOCK_TRENDVOLUME_PK&columns=SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,PRICE_AVG_RELATION,VOLUME_JUDGE,PAR_FOCUS,PRESSURE_LEVEL,SUPPORT_LEVEL,AVG_PRICE,DEAL_AMOUNT,AVG_AMOUNT_5DAYS,DAILY_TRADE_60TD,WORDS_EXPLAIN,TRADE_DATE&filter=(SECUCODE%3D%22000333.SZ%22)&pageNumber=1&pageSize=200&sortTypes=1&sortColumns=TRADE_DATE&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=PRT_STOCK_MACD_PK&columns=MACD,MACDCOUT,MACDCLOR,KDJOUT,KDJCLOR,RSIOUT,RSICLOR,BOLLOUT,BOLLCLOR,BIASOUT,BIASCLOR,WROUT,WRCLOR&filter=(SECUCODE%3D%22000333.SZ%22)&pageNumber=1&pageSize=60&sortTypes=-1&sortColumns=TRADEDATE&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=PRT_STOCK_CAPITALFLOWS&columns=SECUCODE,TRADE_DATE,CAPITAL_FLOWS,CAPITAL_FLOWS_5DAYS,CAPITAL_FLOWS_RATIO,CAPITAL_FLOWS_5DAYSRATIO&filter=(SECUCODE%3D%22000333.SZ%22)&pageNumber=1&pageSize=5&sortTypes=-1&sortColumns=TRADE_DATE&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=PRT_STOCK_CAPITALFLOWS&columns=SECUCODE,TRADE_DATE,BOARD_CAPITAL_FLOWS,BOARD_CAPITAL_5FLOWS,BOARD_CODE,BOARD_NAME&filter=(SECUCODE%3D%22000333.SZ%22)&pageNumber=1&pageSize=5&sortTypes=-1&sortColumns=TRADE_DATE&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_STOCK_ACTIVEREGION&columns=SECURITY_CODE,ACTIVE_REGION,REGION_CHANGERATE,VOLUME_RATIO,BUYER_VOLUME,CHANGE_RATE,ACTIVE_PRICE,AVERAGE_PRICE&filter=(SECURITY_CODE%3D%22000333%22)&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_STOCK_LHB5DAYS&columns=SECUCODE,TRADE_DATE,BUY_AMT,SELL_AMT,NET_AMT,FIRST_BUY_AMT,FIRST_SELL_AMT,BUY_FREERATIO,SELL_FREERATIO,BUY_ORG,SELL_ORG&filter=(SECUCODE%3D%22000333.SZ%22)&sortTypes=1&sortColumns=TRADE_DATE&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_STOCK_BILLBOARDTIMES&columns=SECUCODE,BILLBOARD_FREQUENCY,BILLBOARD_BUY_AMT,BILLBOARD_SELL_AMT,BILLBOARD_NET_AMT&filter=(SECUCODE%3D%22000333.SZ%22)&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_STOCK_MARGINTRENDEXPLAIN&columns=SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,EXPLAIN&filter=(SECUCODE%3D%22000333.SZ%22)&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_STOCK_MARGINTREND&columns=SECUCODE,TRADE_DATE,FIN_BALANCE_DIFF,FREE_RATIO,FINBALANCE_DIFF_CHANGE,AVG_FREE_RATIO,FIN_BALANCE,LOAN_BALANCE,EXPLAIN&filter=(SECUCODE%3D%22000333.SZ%22)&sortTypes=1&sortColumns=TRADE_DATE&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_STOCK_FNRADAR_PK&columns=SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,REPORT_DATE,REPORT_TYPE,WEIGHT_ROE,WEIGHT_ROE_RANK,NETPROFIT_YOY_RATIO,NYR_RANK,TOTAL_ASSETS_TR,TATR_RANK,SALE_CASH_RATIO,SCR_RANK,DEBT_ASSET_RATIO,DAR_RANK,LABEL_EXPLAIN&filter=(SECUCODE%3D%22000333.SZ%22)&pageNumber=1&sortTypes=-1&sortColumns=REPORT_DATE&pageSize=200&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_APP_BALANCED_PICTURE&columns=SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,LABEL_DATE,SIGNAL_OTHER_NAME,SIGNAL_RISK_SCORE,TYPE,SIGNAL_NAME_EXPLAIN&filter=(SECUCODE%3D%22000333.SZ%22)&pageNumber=1&pageSize=200&sortTypes=1&sortColumns=SECUCODE&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_F10_ORG_BASICINFO&columns=SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,SECURITY_TYPE_CODE,SECURITY_PINYIN,LISTING_DATE,TRADE_MARKET,TRADE_MARKET_CODE,SECURITY_INNER_CODE,ORG_CODE,LISTING_STATE,SECURITY_TYPE,ORG_TYPE,CODE_TYPE,ORG_TYPE_CODE&filter=(SECUCODE%3D%22000333.SZ%22)&pageNumber=1&pageSize=200&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_STOCKBOARD_RANK&columns=BOARD_CODE,BOARD_NAME,SECUCODE,SECURITY_NAME_ABBR,CAPITAL_FLOWS,CAPITAL_FLOWS_RANK&filter=(BOARD_CODE%3D%221239%22)&pageNumber=1&pageSize=3&sortTypes=1&sortColumns=CAPITAL_FLOWS_RANK&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_STOCKBOARD_RANK&columns=BOARD_CODE,BOARD_NAME,SECUCODE,SECURITY_NAME_ABBR,CAPITAL_FLOWS,CAPITAL_FLOWS_RANK&filter=(SECUCODE%3D%22000333.SZ%22)&pageNumber=1&pageSize=1&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_CUSTOM_RISK_MINESWEEPER_SUMMARIZE&filter=(SECUCODE%3D%22000333.SZ%22)&source=SECURITIES&client=APP
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_F10_ORG_BASICINFO&columns=SECUCODE%2CSECURITY_CODE%2CSECURITY_NAME_ABBR%2CSECURITY_TYPE_CODE%2CSECURITY_PINYIN%2CLISTING_DATE%2CTRADE_MARKET%2CTRADE_MARKET_CODE%2CSECURITY_INNER_CODE%2CORG_CODE%2CLISTING_STATE%2CSECURITY_TYPE%2CORG_TYPE%2CCODE_TYPE%2CORG_TYPE_CODE&filter=(SECUCODE%3D%22000333.SZ%22)&client=APP&source=SECURITIES&pageNumber=1&pageSize=200&sr=-1&v=08407980787603606
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_CUSTOM_RISK_MINESWEEPER_SUMMARIZE&filter=(SECUCODE%3D%22000333.SZ%22)&client=APP&source=SECURITIES&v=06365503481874877
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_CUSTOM_RISK_MINESWEEPER&filter=(SECUCODE%3D%22000333.SZ%22)&client=APP&source=SECURITIES&v=004491793660595722
https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_RISK_MINESWEEPER_FNVIEW&columns=SECUCODE%2CSECURITY_CODE%2CREPORT_DATE%2CREPORT_LABEL%2CREPORT_LABEL_DETAILS%2CGOODWILL%2CGW_NA_RATIO&filter=(SECUCODE%3D%22000333.SZ%22)&client=APP&source=SECURITIES&sortTypes=1&sortColumns=REPORT_DATE&v=009224708917091584
'''.strip().splitlines()


def group_urls_by_report_name(urls: Iterable[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for url in urls:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        report_name = query_params.get('reportName', [None])[0] or 'UNKNOWN'
        grouped[report_name].append(url)
    return dict(grouped)


def main() -> None:
    grouped_urls = group_urls_by_report_name(urls)
    for report_name, items in grouped_urls.items():
        if report_name == 'UNKNOWN':
            continue
        if len(items) == 1:
            continue
        print(f'=== reportName={report_name} ({len(items)} urls) ===')
        for item in items:
            print(item)
        print()


if __name__ == '__main__':
    main()
