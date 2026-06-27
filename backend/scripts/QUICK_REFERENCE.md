# 股票报告生成器 - 快速参考

## 🎯 最常用命令

### 1️⃣ 快速查看单个股票

```bash
cd backend
uv run --with httpx python scripts/generate_stock_report.py --stock 000333
```

### 2️⃣ 生成并保存Markdown报告

```bash
uv run --with httpx python scripts/advanced_stock_report.py \
  --stock 000333 \
  --output report.md
```

### 3️⃣ 生成HTML报告（带样式）

```bash
uv run --with httpx python scripts/advanced_stock_report.py \
  --stock 000333 \
  --format html \
  --output report.html
```

### 4️⃣ 使用缓存加速查询

```bash
# 第一次（获取数据）
uv run --with httpx python scripts/advanced_stock_report.py --stock 000333 --cache

# 第二次（秒速返回！）
uv run --with httpx python scripts/advanced_stock_report.py --stock 000333 --cache
```

### 5️⃣ 批量生成多个股票报告

```bash
# 方法1：直接指定股票列表
uv run --with httpx python scripts/batch_stock_reports.py --stocks 000333 600000 000001

# 方法2：使用配置文件
# 编辑 stocks_to_report.json，然后运行
uv run --with httpx python scripts/batch_stock_reports.py
```

---

## 📋 参数速查表

### generate_stock_report.py

| 参数 | 说明 | 示例 |
|------|------|------|
| `--stock` | 股票代码（必需） | `--stock 000333` |
| `--output` | 输出文件 | `--output report.md` |
| `--timeout` | 超时时间 | `--timeout 60` |

### advanced_stock_report.py

| 参数 | 说明 | 示例 |
|------|------|------|
| `--stock` | 股票代码（必需） | `--stock 000333` |
| `--output` | 输出文件 | `--output report.md` |
| `--format` | 输出格式 | `--format html` |
| `--timeout` | 超时时间 | `--timeout 60` |
| `--cache` | 启用缓存 | `--cache` |
| `--max-news` | 新闻数量 | `--max-news 10` |

### batch_stock_reports.py

| 参数 | 说明 | 示例 |
|------|------|------|
| `--stocks` | 股票列表 | `--stocks 000333 600000` |
| `--config` | 配置文件 | `--config stocks_to_report.json` |
| `--output` | 输出目录 | `--output ./reports` |
| `--format` | 输出格式 | `--format html` |
| `--cache` | 启用缓存 | `--cache` |
| `--create-sample` | 创建示例配置 | `--create-sample` |

---

## 🎨 常见使用组合

### 为了简洁 - 只要最少信息
```bash
python scripts/generate_stock_report.py --stock 000333
```

### 为了分享 - HTML格式报告
```bash
python scripts/advanced_stock_report.py --stock 000333 --format html --output report.html
```

### 为了性能 - 启用缓存
```bash
python scripts/advanced_stock_report.py --stock 000333 --cache --max-news 3
```

### 为了全面 - 完整配置
```bash
python scripts/advanced_stock_report.py \
  --stock 000333 \
  --format markdown \
  --output ./reports/000333_full.md \
  --cache \
  --max-news 10 \
  --timeout 60
```

### 为了批量 - 监控多个股票
```bash
python scripts/batch_stock_reports.py \
  --stocks 000333 600000 000001 000858 \
  --format html \
  --cache \
  --output ./daily_reports
```

---

## 💡 提示和技巧

### 快速清除缓存
```bash
rm -rf /tmp/stock_report_cache/
```

### 查看缓存文件
```bash
ls -la /tmp/stock_report_cache/
```

### 测试网络连接
```bash
python scripts/generate_stock_report.py --stock 000333 --timeout 10
```

### 生成多个格式
```bash
# 同时生成 Markdown 和 HTML
python scripts/advanced_stock_report.py --stock 000333 --format markdown --output report.md
python scripts/advanced_stock_report.py --stock 000333 --format html --output report.html
```

### 定时生成（cron任务）
```bash
# 每天10点生成报告
0 10 * * * cd /home/riiy/miaoxiang_web/backend && \
  uv run --with httpx python scripts/batch_stock_reports.py \
  --stocks 000333 600000 \
  --output /var/reports/$(date +%Y%m%d)
```

---

## 🆘 问题排查

### 问题：连接超时

**症状**：`timeout` 错误

**解决**：
```bash
python scripts/advanced_stock_report.py --stock 000333 --timeout 60
```

### 问题：N/A信息过多

**症状**：报告中大量显示 "N/A"

**可能原因**：
- 股票代码错误
- API服务异常
- 网络连接问题

**解决**：检查股票代码，重试或稍后再试

### 问题：缓存数据过期

**症状**：想要最新数据

**解决**：清除缓存
```bash
rm -rf /tmp/stock_report_cache/000333*
```

### 问题：输出文件没有内容

**症状**：生成的文件为空或很小

**解决**：
```bash
# 检查错误信息
python scripts/advanced_stock_report.py --stock 000333 --timeout 60
```

---

## 📊 股票代码格式

支持的格式：

```
000333      ✓ 深圳股票
000333.SZ   ✓ 深圳股票（完整）
600000      ✓ 上海股票
600000.SH   ✓ 上海股票（完整）

XXXX        ✗ 无效格式
000333.HK   ✗ 暂不支持香港股票
```

系统会自动识别和转换。

---

## 🔄 工作流程示例

### 场景1：监控特定股票
```bash
# 创建脚本 monitor.sh
#!/bin/bash
stocks=(000333 600000 000001)
for stock in "${stocks[@]}"; do
  python scripts/advanced_stock_report.py \
    --stock $stock \
    --format html \
    --cache \
    --output "./reports/${stock}_$(date +%Y%m%d).html"
done
```

### 场景2：每日报告
```bash
# 在cron中添加
0 9 * * 1-5 /path/to/monitor.sh
```

### 场景3：Web应用集成
```python
# 在Python应用中调用
import subprocess

result = subprocess.run([
    'python', 'scripts/advanced_stock_report.py',
    '--stock', '000333',
    '--format', 'markdown',
    '--cache'
], capture_output=True, text=True)

report_content = result.stdout
```

---

## 📈 性能对比

| 场景 | 命令 | 耗时 | 备注 |
|------|------|------|------|
| 首次查询 | 无缓存 | 3-5秒 | 调用API |
| 缓存查询 | 有缓存 | 0.2秒 | 从本地读取 |
| 批量5个 | 并发 | 4-6秒 | 异步处理 |
| HTML格式 | 附加 | +0.5秒 | 格式化 |

---

## 🎓 学习资源

| 资源 | 位置 | 说明 |
|------|------|------|
| 基础指南 | `STOCK_REPORT_GUIDE.md` | 快速入门 |
| 完整文档 | `README_STOCK_REPORT.md` | 详细说明 |
| 系统概览 | `SYSTEM_OVERVIEW.md` | 架构设计 |
| 代码注释 | `*.py` | 源代码文件 |

---

## 📞 获取帮助

1. **查看使用文档**
   ```bash
   cat STOCK_REPORT_GUIDE.md
   cat README_STOCK_REPORT.md
   ```

2. **查看脚本帮助**
   ```bash
   python scripts/generate_stock_report.py --help
   python scripts/advanced_stock_report.py --help
   python scripts/batch_stock_reports.py --help
   ```

3. **检查日志**
   - 脚本错误会输出到stderr
   - 使用 `2>&1` 重定向查看

---

**最后更新**：2026-06-05  
**快速参考版本**：1.0

祝你使用愉快！ 🚀
