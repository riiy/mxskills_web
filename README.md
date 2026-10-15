# Local Finance Skill Console

A local, single-user finance skill console built around a collection of financial analysis scripts.

The repository combines:

- `backend/`: a FastAPI service that registers skills, validates requests, runs Python scripts, normalizes skill output, and serves generated files.
- `frontend/`: a Vite + React web console for selecting skills, entering natural language queries, running tasks, and viewing Markdown/text results.
- skill directories at the repository root such as `mx-finance-data/`, `stock-diagnosis/`, `topic-research-report/`, and more.
- generated output under `miaoxiang/` and several allowed output directories used by downloadable reports.

## What this project does

It exposes a local API for financial analysis skills and a browser UI to interact with them.

- Users choose a skill and enter a query.
- Backend resolves skill metadata from `backend/app/skills.py`.
- Skills run as subprocesses through `backend/app/runner.py`.
- Output is normalized into structured JSON, including text, files, and links.
- Generated files can be downloaded through a secure file endpoint.

## Repository layout

- `backend/`
  - `app/main.py`: FastAPI application and API routes.
  - `app/skills.py`: skill registry, metadata, controls, and available skill definitions.
  - `app/runner.py`: command construction, subprocess execution, output normalization, URL/file extraction, and allowed file download logic.
  - `pyproject.toml` / `requirements.txt`: backend dependencies.
- `frontend/`
  - `src/`: React application source.
  - `package.json`: frontend dependencies and scripts.
- `miaoxiang/`: generated reports and files produced by skills.
- Skill folders such as `mx-finance-search/`, `industry-research-report/`, `stock-market-hotspot-discovery/`, `fund-diagnosis/`, etc.

## Key skills supported

The backend currently exposes a wide set of financial skill modules, including:

- `mx-financial-assistant`: financial Q&A with optional deep thinking.
- `mx-finance-data`: structured financial data queries with Excel outputs.
- `mx-finance-search`: financial news and report search.
- `mx-macro-data`: macroeconomic data lookup.
- `mx-stocks-screener`: stock/fund/screening search by natural language.
- `stock-diagnosis`: single-stock diagnostic reports.
- `fund-diagnosis`: fund diagnosis reports.
- `stock-market-hotspot-discovery`: market hotspot discovery.
- `topic-research-report`, `industry-research-report`, `industry-stock-tracker`, `initiation-of-coverage-or-deep-dive`: research/report generation.
- `comparable-company-analysis`: comparable company Excel analysis.
- `stock-earnings-review`: earnings review with a custom entity/report period workflow.

## Running locally

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Then open the Vite URL shown in the terminal, usually `http://127.0.0.1:5173`.

## API overview

- `GET /api/health` - health check.
- `GET /api/skills` - returns available skill definitions, groups, descriptions, examples, and UI control configuration.
- `POST /api/runs` - execute a skill with JSON payload.
- `GET /api/files?path=...` - download a generated file from an allowed output directory.

### Example `POST /api/runs`

```json
{
  "skillId": "mx-stocks-screener",
  "query": "股价大于500元的股票",
  "params": {
    "selectType": "A股"
  }
}
```

## Testing

### Backend

```bash
cd backend
uv run pytest
```

### Frontend

```bash
cd frontend
npm test
```

## Notes

- The backend validates file download requests to permitted output roots only.
- Skill metadata and UI controls are defined in `backend/app/skills.py`.
- Some advanced skills use a custom execution path, such as `stock-earnings-review`.
- Generated files are typically written under `miaoxiang/` and allowed output directories defined in `backend/app/runner.py`.
