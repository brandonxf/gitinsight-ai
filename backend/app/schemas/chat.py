from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatSessionCreateResponse(BaseModel):
    session_id: uuid.UUID
    job_id: uuid.UUID


class ChatMessageCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class Citation(BaseModel):
    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    symbol: str | None = None


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    citations: list[Citation] = Field(default_factory=list)
    created_at: datetime


class ChatHistoryOut(BaseModel):
    session_id: uuid.UUID
    messages: list[ChatMessageOut] = Field(default_factory=list)
