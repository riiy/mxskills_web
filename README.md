# 本地金融技能控制台

这个项目在现有金融 skill 脚本外增加一个本地单用户 Web 控制台：

- `backend/`：FastAPI API，负责技能注册、参数校验、同步调用 Python 脚本、结果归一化和本地文件下载。
- `frontend/`：Vite React 控制台，支持选择技能、输入自然语言查询、运行脚本、查看 Markdown/文本结果和生成文件。

## 启动

后端：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

打开 Vite 输出的地址，默认是 `http://127.0.0.1:5173`。

## API

- `GET /api/skills`：返回技能列表、分组、描述、示例和控件配置。
- `POST /api/runs`：同步运行技能，body 示例：

```json
{
  "skillId": "mx-stocks-screener",
  "query": "股价大于500元的股票",
  "params": {
    "selectType": "A股"
  }
}
```

- `GET /api/files?path=...`：仅下载允许输出目录下的生成文件。

## 测试

```bash
cd backend
pytest

cd ../frontend
npm test
```
