# 股票报告生成工具完整指南

## 概述

这个项目包含两个股票报告生成脚本：

1. **generate_stock_report.py** - 基础版本
2. **advanced_stock_report.py** - 高级版本（支持缓存、HTML格式等）

两个脚本都能从多个数据源获取股票信息，并生成可读的综合报告。

---

## 基础版本 (generate_stock_report.py)

### 快速开始

```bash
# 基本用法
uv run --with httpx python scripts/generate_stock_report.py --stock 000333

# 保存到文件
uv run --with httpx python scripts/generate_stock_report.py --stock 000333 --output report.md

# 自定义超时
uv run --with httpx python scripts/generate_stock_report.py --stock 000333 --timeout 60 --output report.md
```

### 参数

| 参数 | 必需 | 说明 | 默认值 |
|------|------|------|--------|
| `--stock` | ✓ | 股票代码 | - |
| `--output` | ✗ | 输出文件路径 | 控制台输出 |
| `--timeout` | ✗ | API超时（秒） | 30 |

### 示例

```bash
# 获取美的集团报告
python scripts/generate_stock_report.py --stock 000333

# 保存为Markdown文件
python scripts/generate_stock_report.py --stock 600000 --output ./reports/baidu.md

# 增加超时时间
python scripts/generate_stock_report.py --stock 000333 --timeout 60
```

---

## 高级版本 (advanced_stock_report.py)

### 快速开始

```bash
# Markdown输出（默认）
uv run --with httpx python scripts/advanced_stock_report.py --stock 000333 --output report.md

# HTML输出
uv run --with httpx python scripts/advanced_stock_report.py --stock 000333 --format html --output report.html

# 启用缓存
uv run --with httpx python scripts/advanced_stock_report.py --stock 000333 --cache

# 控制新闻数量
uv run --with httpx python scripts/advanced_stock_report.py --stock 000333 --max-news 10
```

### 参数

| 参数 | 必需 | 说明 | 默认值 |
|------|------|------|--------|
| `--stock` | ✓ | 股票代码 | - |
| `--output` | ✗ | 输出文件路径 | 控制台输出 |
| `--format` | ✗ | 输出格式 (markdown/html) | markdown |
| `--timeout` | ✗ | API超时（秒） | 30 |
| `--cache` | ✗ | 启用数据缓存 | 禁用 |
| `--max-news` | ✗ | 最多显示新闻数 | 5 |

### 特性

#### 1. 多格式输出

**Markdown格式**（默认）
```bash
python scripts/advanced_stock_report.py --stock 000333 --format markdown --output report.md
```

**HTML格式**
```bash
python scripts/advanced_stock_report.py --stock 000333 --format html --output report.html
```

#### 2. 数据缓存

缓存数据到本地，提高重复查询速度：

```bash
# 第一次：从API获取数据并缓存
python scripts/advanced_stock_report.py --stock 000333 --cache --output report1.md

# 第二次：从缓存读取（速度快）
python scripts/advanced_stock_report.py --stock 000333 --cache --output report2.md
```

缓存位置：`/tmp/stock_report_cache/`

#### 3. 灵活配置

```bash
# 显示15条新闻
python scripts/advanced_stock_report.py --stock 000333 --max-news 15

# 30秒超时 + 缓存
python scripts/advanced_stock_report.py --stock 000333 --timeout 30 --cache --output report.md
```

### 示例

```bash
# 生成美的集团的HTML报告（带缓存）
python scripts/advanced_stock_report.py \
  --stock 000333 \
  --format html \
  --cache \
  --output ./reports/meidi.html

# 显示所有新闻（20条）
python scripts/advanced_stock_report.py \
  --stock 600000 \
  --max-news 20 \
  --output ./reports/baidu_full.md
```

---

## 股票代码格式

脚本支持多种格式：

```
000333      # 深圳A股
000333.SZ   # 深圳A股（完整格式）
600000      # 上海A股  
600000.SH   # 上海A股（完整格式）
```

脚本会自动识别和转换。

---

## 报告内容

生成的报告包含以下部分：

### 1. 基本信息
- 股票名称
- 市场表现描述

### 2. 诊断评分
- 总体评分
- 基础评分、市场评分、市场关注度
- 技术评分、资金评分、新闻评分
- 诊断时间和价格变化

### 3. 涨幅概率
- 股票上涨的概率

### 4. 情绪评分
- 市场对该股票的情绪评价
- 统计周期

### 5. 热点新闻
- 与股票相关的最新新闻
- 发布时间

---

## 输出示例

### Markdown格式

```markdown
# 股票综合分析报告

生成时间：2026-06-05 11:17:39
股票代码：000333 (000333.SZ)

## 基本信息
**股票名称：** 美的集团
**市场表现：** 近期消息面活跃，主力资金有大幅介入迹象...

## 诊断评分
**总体评分：** 81.61
**基础评分：** 84.37
...
```

### HTML格式

生成带有样式的可视化HTML报告，可以在浏览器中打开查看。

---

## 常见问题

### Q: 如何批量生成多个股票的报告？

使用shell脚本循环调用：

```bash
for stock in 000333 600000 000001; do
  python scripts/advanced_stock_report.py \
    --stock $stock \
    --format markdown \
    --output "./reports/${stock}.md"
done
```

### Q: 如何处理网络超时？

增加超时时间参数：

```bash
python scripts/advanced_stock_report.py --stock 000333 --timeout 60
```

### Q: 缓存文件在哪里？

缓存位置：`/tmp/stock_report_cache/`

要清除缓存：
```bash
rm -rf /tmp/stock_report_cache/
```

### Q: 为什么某些字段显示 N/A？

说明该数据源无法访问或返回了不预期的格式。可能原因：
- 网络连接问题
- 股票代码错误
- API服务异常

### Q: 如何修改输出样式？

**HTML格式**：编辑 `advanced_stock_report.py` 中的 CSS 样式部分

**Markdown格式**：编辑 `generate_markdown()` 方法的内容

---

## 性能优化

### 1. 使用缓存

```bash
# 启用缓存后，重复查询会快很多
python scripts/advanced_stock_report.py --stock 000333 --cache
```

### 2. 减少新闻显示

```bash
# 只显示2条新闻，减少输出
python scripts/advanced_stock_report.py --stock 000333 --max-news 2
```

### 3. 并发获取

两个脚本都使用异步IO并发获取多个API的数据，速度优化。

---

## 扩展功能建议

1. **数据库存储** - 将结果存储到数据库
2. **邮件发送** - 自动生成并邮件发送报告
3. **定时任务** - 使用cron定时生成报告
4. **Web界面** - 创建Web应用前端
5. **更多数据源** - 添加K线数据、财报数据等
6. **PDF导出** - 支持PDF格式
7. **多语言** - 支持英文等其他语言
8. **对比分析** - 对比多个股票

---

## 技术细节

### 依赖

- `httpx` - 异步HTTP客户端
- Python 3.7+

### API数据源

- **热点新闻**: https://np-listapi.eastmoney.com/
- **股票数据**: https://datacenter.eastmoney.com/

### 异步设计

使用 `asyncio` 和 `httpx.AsyncClient` 实现并发数据获取，提高性能。

---

## 故障排除

### 问题：连接超时

```
Error fetching data: timeout
```

**解决方案**：增加超时时间
```bash
python scripts/advanced_stock_report.py --stock 000333 --timeout 60
```

### 问题：股票代码无效

返回空报告或大量 N/A

**解决方案**：检查股票代码格式
```bash
# 使用正确的格式
python scripts/advanced_stock_report.py --stock 000333  # ✓ 正确
python scripts/advanced_stock_report.py --stock XXXX    # ✗ 错误
```

### 问题：依赖缺失

```
Error: httpx is required
```

**解决方案**：安装依赖
```bash
uv run --with httpx python scripts/...
```

---

## 许可证

内部使用工具

---

## 联系与反馈

有任何问题或改进建议，请联系开发团队。
