"""FastAPI backend for the Local Finance Skill Console.

This module provides REST API endpoints for:
- Listing available financial analysis skills
- Running skills with user-provided queries and parameters
- Downloading generated output files securely
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .runner import allowed_file_path, run_skill
from .skills import list_skills


class RunRequest(BaseModel):
    """Request model for running a skill.

    Attributes:
        skillId: The unique identifier of the skill to execute.
        query: The user's natural language query or command.
        params: Optional skill-specific parameters.
    """

    skillId: str = Field(..., min_length=1, description="Skill identifier")
    query: str = Field(..., min_length=1, description="User query")
    params: dict[str, Any] = Field(default_factory=dict, description="Skill parameters")


app = FastAPI(
    title="Local Finance Skill Console",
    version="0.1.0",
    description="API for running local financial analysis skills",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://finance-skills.acquirecord.top", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/skills")
def skills() -> dict[str, Any]:
    """Return list of all registered skills."""
    return {"skills": list_skills()}


@app.post("/api/runs")
async def runs(request: RunRequest) -> dict[str, Any]:
    """Execute a skill with the provided query and parameters.

    Args:
        request: RunRequest containing skillId, query, and params.

    Returns:
        Execution result with content, files, links, and status.

    Raises:
        HTTPException: 400 if skill execution fails due to invalid input.
    """
    try:
        return await run_skill(request.skillId, request.query, request.params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/files")
def files(path: str = Query(..., min_length=1)) -> FileResponse:
    """Download a generated file from allowed output directories.

    Args:
        path: Absolute or relative path to the file.

    Returns:
        FileResponse for the requested file.

    Raises:
        HTTPException: 403 if path is outside allowed directories.
        HTTPException: 404 if file does not exist.
    """
    try:
        resolved = allowed_file_path(path)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(resolved, filename=resolved.name)
