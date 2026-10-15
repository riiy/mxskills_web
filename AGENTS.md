# Repository Guidelines

## Project Structure & Module Organization

This repository contains a local finance skill console plus reusable finance skill modules.

- `backend/`: FastAPI API for listing skills, running scripts, normalizing results, and serving generated files. Main app code is in `backend/app/`; tests are in `backend/tests/`.
- `frontend/`: Vite React console. Source lives in `frontend/src/`, with styles in `frontend/src/styles.css` and tests beside source as `*.test.jsx`.
- `*/SKILL.md` directories: individual finance/reporting skills. Script entry points are usually under each skill's `scripts/` directory.
- `miaoxiang/`: generated output location used by tests and runtime file serving; do not commit generated reports unless explicitly required.

## Build, Test, and Development Commands

Prefix shell commands with `rtk` when working in this repo.

Backend:

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
uv run pytest
```

Frontend:

```bash
cd frontend
npm install
npm run dev
npm run build
npm test
npm run preview
```

Use `uv` for backend environment creation, dependency sync, and Python command execution. `npm run dev` starts Vite on `127.0.0.1`; `npm run build` creates the production bundle.

## Coding Style & Naming Conventions

Python targets 3.13 and uses type hints, Pydantic models, and small FastAPI route functions. Use 4-space indentation, `snake_case` for functions and modules, and concise docstrings for public endpoints or non-obvious helpers.

React code uses ES modules, functional components, hooks, and JSX files. Use `PascalCase` for components, `camelCase` for variables/functions, and keep API constants such as `API_BASE` in uppercase. Match the existing single-quote JavaScript style.

## Testing Guidelines

Backend tests use `pytest` with `pytest-asyncio`; add tests under `backend/tests/test_*.py`. Mock subprocess calls when testing skill execution, and cover path validation for file-serving changes.

Frontend tests use Vitest and jsdom; name tests `*.test.jsx` near the related source. Add smoke or interaction tests when changing UI behavior.

## Commit & Pull Request Guidelines

History is minimal, with short imperative messages plus occasional descriptive titles. Prefer concise commits such as `Add skill runner validation` or `Update frontend run panel`.

Pull requests should include a brief summary, tests run, linked issue if any, and screenshots or screen recordings for visible frontend changes. Note any new environment variables, generated output paths, or external API requirements.

## Security & Configuration Tips

Keep generated file downloads constrained to allowed output directories. Do not expose arbitrary filesystem paths through `/api/files`. Store secrets outside the repo and pass frontend API overrides with `VITE_API_BASE`.
