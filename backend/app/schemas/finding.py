from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: str
    severity: str
    rule_id: str | None = None
    file_path: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    message: str
    suggestion: str | None = None
    # Lee el atributo ORM `finding_metadata` pero se serializa como `metadata`.
    metadata: dict[str, Any] = Field(
        default_factory=dict, validation_alias="finding_metadata"
    )


class FindingPage(BaseModel):
    items: list[FindingOut]
    total: int
    limit: int
    offset: int
