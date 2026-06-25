from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AnalysisOptions(BaseModel):
    deep_quality: bool = True
    generate_docs: bool = False


class AnalysisCreate(BaseModel):
    url: str = Field(..., examples=["https://github.com/owner/repo"])
    options: AnalysisOptions = Field(default_factory=AnalysisOptions)


class AnalysisLinks(BaseModel):
    self: str
    result: str


class AnalysisJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    repository_id: uuid.UUID
    status: str
    phase: str | None = None
    progress_pct: int = 0
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime


class AnalysisCreateResponse(BaseModel):
    job_id: uuid.UUID
    status: str
    links: AnalysisLinks


class RepositoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    owner: str
    name: str
    default_branch: str | None = None
    commit_sha: str | None = None


class AnalysisResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job: AnalysisJobOut
    repository: RepositoryOut
    primary_language: str | None = None
    languages: dict[str, Any] = Field(default_factory=dict)
    frameworks: list[Any] = Field(default_factory=list)
    structure: dict[str, Any] = Field(default_factory=dict)
    summary: str | None = None
    purpose: str | None = None
    modules: list[Any] = Field(default_factory=list)
    flow_description: str | None = None
    risk_level: str | None = None
    quality_score: int | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    diagrams: dict[str, Any] = Field(default_factory=dict)
    generated_docs: dict[str, Any] = Field(default_factory=dict)
