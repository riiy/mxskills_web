# 股票综合分析报告生成系统

## 📋 项目概述

这是一个完整的股票综合分析报告生成系统，可以快速获取股票数据并生成专业的分析报告。系统包含多个脚本，支持单股票、批量生成、多格式输出等功能。

### 核心功能

✓ 快速生成股票分析报告  
✓ 多数据源聚合（热点新闻、诊断评分、情绪分析等）  
✓ 多格式输出（Markdown、HTML）  
✓ 数据缓存优化  
✓ 批量生成能力  
✓ 异步并发处理  

---

## 📁 文件结构

```
backend/scripts/
├── generate_stock_report.py       # 基础报告生成脚本
├── advanced_stock_report.py       # 高级报告生成脚本（支持缓存、HTML）
├── batch_stock_reports.py         # 批量生成脚本
├── stocks_to_report.json          # 批量生成的股票配置文件
├── STOCK_REPORT_GUIDE.md          # 基础脚本使用指南
├── README_STOCK_REPORT.md         # 完整使用文档
└── SYSTEM_OVERVIEW.md             # 本文件
```

---

## 🚀 快速开始

### 1. 单个股票报告

**基础版本**
```bash
cd backend
uv run --with httpx python scripts/generate_stock_report.py --stock 000333
```

**高级版本（带缓存和HTML支持）**
```bash
uv run --with httpx python scripts/advanced_stock_report.py --stock 000333 --cache
```

### 2. 保存为文件

```bash
# Markdown格式
uv run --with httpx python scripts/advanced_stock_report.py \
  --stock 000333 \
  --format markdown \
  --output /tmp/report.md

# HTML格式
uv run --with httpx python scripts/advanced_stock_report.py \
  --stock 000333 \
  --format html \
  --output /tmp/report.html
```

### 3. 批量生成

编辑 `stocks_to_report.json`，添加要生成的股票代码：

```json
{
  "stocks": [
    "000333",
    "600000",
    "000001"
  ]
}
```

然后运行：
```bash
uv run --with httpx python scripts/batch_stock_reports.py
```

或直接指定股票：
```bash
uv run --with httpx python scripts/batch_stock_reports.py --stocks 000333 600000 000001
```

---

## 📊 报告内容

生成的报告包含以下部分：

| 部分 | 说明 | 数据来源 |
|------|------|--------|
| **基本信息** | 股票名称、市场表现 | RPT_STOCK_WORDS_PK |
| **诊断评分** | 多维度评分和指标 | RPT_STOCK_SCORE_PK |
| **涨幅概率** | 股票上涨的概率 | PRT_STOCK_RISE_PROBABILITY_PK |
| **情绪评分** | 市场情绪评价 | RPT_YQ_EMOTION_SCORE |
| **热点新闻** | 相关新闻和资讯 | 东方财富热点新闻接口 |

### 示例报告

```markdown
# 股票综合分析报告

生成时间：2026-06-05 11:17:39
股票代码：000333 (000333.SZ)

## 基本信息
**股票名称：** 美的集团
**市场表现：** 近期消息面活跃，主力资金有大幅介入迹象，短期呈现震荡趋势

## 诊断评分
**总体评分：** 81.61
**基础评分：** 84.37
**市场评分：** 91.65
...

## 热点新闻
1. **612家A股公司年内发力回购 计划上限1114亿元**
   时间：2026-06-05 08:08:40
```

---

## 🔧 脚本对比

### generate_stock_report.py（基础版）

**优点**：
- 功能简洁，易于理解
- 依赖少，启动快
- 适合简单使用

**用途**：
- 快速查询单个股票
- 学习和参考
- 轻量级部署

**示例**：
```bash
python scripts/generate_stock_report.py --stock 000333 --output report.md
```

### advanced_stock_report.py（高级版）

**优点**：
- 支持多格式输出（Markdown、HTML）
- 数据缓存优化性能
- 灵活配置选项
- 适合生产环境

**用途**：
- 批量生成报告
- 频繁查询同一股票
- HTML报告展示
- 性能优化场景

**示例**：
```bash
python scripts/advanced_stock_report.py \
  --stock 000333 \
  --format html \
  --cache \
  --output report.html
```

### batch_stock_reports.py（批量版）

**优点**：
- 批量生成多个股票报告
- 并发处理提高效率
- JSON配置文件管理
- 生成统计摘要

**用途**：
- 定期生成行业报告
- 监控股票池
- 自动化报告生成
- 定时任务集成

**示例**：
```bash
python scripts/batch_stock_reports.py \
  --stocks 000333 600000 000001 \
  --format html \
  --cache
```

---

## 📈 使用场景

### 场景1：快速查询单个股票

```bash
# 查看美的集团的实时分析
python scripts/generate_stock_report.py --stock 000333
```

### 场景2：生成可分享的HTML报告

```bash
# 生成漂亮的HTML报告分享给同事
python scripts/advanced_stock_report.py \
  --stock 000333 \
  --format html \
  --output ./reports/meidi_2024.html
```

### 场景3：每天监控10个股票

```bash
# 配置stocks_to_report.json
# 然后在cron中定时运行
python scripts/batch_stock_reports.py --output ./daily_reports
```

### 场景4：高频查询优化

```bash
# 使用缓存加速重复查询
python scripts/advanced_stock_report.py --stock 000333 --cache
```

---

## 💾 数据源

系统从以下API获取数据：

### 1. 股票基本信息和评分
- **URL**: https://datacenter.eastmoney.com/securities/api/data/v1/get
- **数据**: 股票名称、诊断评分、情绪分析等

### 2. 热点新闻
- **URL**: https://np-listapi.eastmoney.com/hotnews-sec/
- **数据**: 与股票相关的最新新闻资讯

---

## 🔄 工作流程

```
用户输入股票代码
        ↓
验证代码格式
        ↓
并发获取多个API的数据
        ↓
收集并整理数据
        ↓
生成格式化报告
        ↓
输出（控制台/文件）
```

### 数据流

```
API数据 → 缓存检查 → JSON解析 → 字段提取 → 格式化 → 报告输出
```

---

## ⚙️ 配置和定制

### 修改输出样式

**Markdown报告**：编辑 `generate_markdown()` 方法

**HTML报告**：编辑 `generate_html()` 方法的CSS样式

### 添加新的数据源

```python
async def get_new_data(self, client: httpx.AsyncClient, secucode: str):
    """添加新的数据源"""
    params = {...}
    url = f"{self.base_url}?{urlencode(params)}"
    return await self.fetch_data(client, url)
```

### 修改缓存位置

```python
config = ReportConfig(
    cache_enabled=True,
    cache_dir=Path('/custom/cache/path')
)
```

---

## 🚨 常见问题

### Q: 如何处理网络慢的情况？

A: 增加超时时间：
```bash
python scripts/advanced_stock_report.py --stock 000333 --timeout 60
```

### Q: 缓存数据过期了怎么办？

A: 清除缓存重新获取：
```bash
rm -rf /tmp/stock_report_cache/
```

### Q: 如何在web应用中集成？

A: 可以通过调用Python脚本或改写为API服务：
1. 将脚本改写为FastAPI应用
2. 添加到backend/app/main.py的路由中
3. 前端调用API获取报告

### Q: 支持哪些股票市场？

A: 目前支持：
- A股（深圳、上海）
- 可扩展支持港股、美股等

### Q: 能否定时自动生成报告？

A: 可以，使用cron任务：
```bash
# 每天上午10点生成报告
0 10 * * * cd /path/to/backend && uv run --with httpx python scripts/batch_stock_reports.py
```

---

## 📝 扩展建议

### 短期改进

1. **数据验证** - 添加输入验证和数据检查
2. **错误处理** - 更详细的错误信息和日志
3. **配置文件** - 支持更复杂的配置选项
4. **单元测试** - 添加测试覆盖

### 中期功能

1. **数据库** - 存储历史数据进行对比分析
2. **邮件通知** - 生成后自动发送邮件
3. **定时任务** - 集成调度器自动执行
4. **多语言** - 支持中英文切换

### 长期规划

1. **Web UI** - 创建web界面
2. **移动应用** - 移动端支持
3. **实时推送** - WebSocket实时更新
4. **AI分析** - 添加机器学习分析
5. **更多数据** - K线、财报、行业数据等

---

## 🔐 安全和性能

### 安全考虑

- 验证所有用户输入（股票代码）
- 限制并发请求数量
- 不存储敏感个人信息
- 定期检查API访问权限

### 性能优化

- 使用异步IO处理网络请求
- 实现数据缓存机制
- 并发获取多个数据源
- 减少不必要的API调用

### 限流建议

```python
# 添加速率限制
MAX_REQUESTS_PER_MINUTE = 60
MAX_CONCURRENT_REQUESTS = 5
```

---

## 📖 开发指南

### 添加新脚本

1. 继承 `StockReportGenerator` 或 `AdvancedStockReportGenerator`
2. 实现新的 `get_*` 方法
3. 更新 `generate_markdown()` 或 `generate_html()` 方法
4. 测试新功能

### 代码规范

- Python 3.7+ 兼容
- 使用类型注解
- 遵循PEP 8风格
- 添加文档字符串

---

## 📊 性能指标

| 操作 | 时间 | 备注 |
|------|------|------|
| 单个股票报告 | 1-5秒 | 无缓存 |
| 单个股票报告 | 0.1秒 | 使用缓存 |
| 5个股票报告 | 3-8秒 | 并发获取 |
| HTML生成 | +0.5秒 | 额外格式化 |

---

## 📞 支持和反馈

- 问题报告：提交issue
- 功能建议：提交feature request
- 性能优化：欢迎PR

---

## 📄 许可证

内部使用工具

---

## 🙏 致谢

感谢东方财富提供的数据接口支持。

---

**最后更新**：2026-06-05  
**版本**：1.0  
**作者**：Finance Team
