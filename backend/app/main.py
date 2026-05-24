from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .runner import allowed_file_path, run_skill
from .skills import list_skills


class RunRequest(BaseModel):
    skillId: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)
    params: dict[str, Any] = Field(default_factory=dict)


app = FastAPI(title="Local Finance Skill Console", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/skills")
def skills() -> dict[str, Any]:
    return {"skills": list_skills()}


@app.post("/api/runs")
async def runs(request: RunRequest) -> dict[str, Any]:
    try:
        return await run_skill(request.skillId, request.query, request.params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/files")
def files(path: str = Query(..., min_length=1)) -> FileResponse:
    try:
        resolved = allowed_file_path(path)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(resolved, filename=resolved.name)
