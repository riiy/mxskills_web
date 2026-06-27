# 股票综合分析报告生成器

## 功能说明

这个脚本用于快速生成股票的综合分析报告。它从多个数据源获取信息，并整合成一份易于阅读的Markdown格式报告。

### 报告包含内容

1. **基本信息** - 股票名称和市场表现描述
2. **诊断评分** - 总体评分、基础评分、市场评分等多维度评分
3. **涨幅概率** - 股票上涨的概率
4. **情绪评分** - 市场对该股票的情绪评价
5. **热点新闻** - 与股票相关的最新新闻

## 安装和使用

### 快速开始

```bash
# 基本使用 - 输出到控制台
python generate_stock_report.py --stock 000333

# 保存到文件
python generate_stock_report.py --stock 000333 --output report.md

# 指定超时时间（秒）
python generate_stock_report.py --stock 000333 --timeout 60
```

### 使用uv运行（推荐）

```bash
cd backend

# 输出到控制台
uv run --with httpx python scripts/generate_stock_report.py --stock 000333

# 保存到文件
uv run --with httpx python scripts/generate_stock_report.py --stock 000333 --output /path/to/report.md
```

## 参数说明

| 参数 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `--stock` | ✓ | 股票代码（支持 A股/港股/美股） | `000333`, `600000`, `000333.SZ` |
| `--output` | ✗ | 输出文件路径，不指定则打印到控制台 | `/tmp/report.md` |
| `--timeout` | ✗ | API超时时间（秒），默认30秒 | `60` |

## 示例

### 示例1：查看美的集团报告

```bash
python generate_stock_report.py --stock 000333
```

### 示例2：生成报告并保存

```bash
python generate_stock_report.py --stock 600000 --output ./reports/baidu_report.md
```

### 示例3：增加超时时间处理网络慢的情况

```bash
python generate_stock_report.py --stock 000333 --timeout 60 --output report.md
```

## 股票代码格式

脚本支持多种股票代码格式：

- **深圳A股**：`000333` 或 `000333.SZ`
- **上海A股**：`600000` 或 `600000.SH`
- **完整格式**：`000333.SZ`

脚本会自动识别和转换这些格式。

## 数据源

脚本调用以下数据接口：

1. 热点新闻 - `https://np-listapi.eastmoney.com/hotnews-sec/`
2. 股票诊断数据 - `https://datacenter.eastmoney.com/securities/api/data/v1/get`

所有数据均来自东方财富网络接口。

## 报告示例

生成的报告格式如下：

```markdown
# 股票综合分析报告

生成时间：2026-06-05 11:17:39
股票代码：000333 (000333.SZ)

## 基本信息
**股票名称：** 美的集团
**市场表现：** 近期消息面活跃，...

## 诊断评分
**总体评分：** 81.61
**基础评分：** 84.37
...

## 涨幅概率
**涨幅概率：** 47.71%

## 情绪评分
**市场情绪：** 消极(-9)

## 热点新闻
1. **新闻标题**
   时间：2026-06-05 08:08:40
...
```

## 错误处理

如果某个数据源无法访问或返回错误，脚本会：
- 继续获取其他数据源的信息
- 在报告中显示 `N/A` 表示无数据
- 在标准错误输出中记录具体错误信息

## 常见问题

### Q: 为什么有些字段显示 N/A？
A: 说明该数据源无法访问或返回了不预期的数据格式。

### Q: 如何处理网络超时？
A: 使用 `--timeout` 参数增加超时时间，例如 `--timeout 60`。

### Q: 股票代码错误会怎样？
A: 脚本会返回空数据，报告中大部分字段会显示 N/A。

## 扩展建议

可以在以下方面扩展这个脚本：

1. 添加更多数据源（K线数据、财报数据等）
2. 生成PDF格式报告
3. 支持批量生成多个股票的报告
4. 添加数据缓存机制
5. 支持邮件发送报告
6. 集成到网页应用中

## 许可证

内部使用工具
