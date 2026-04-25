from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from app.models.sbar import SBARStructure


class Inconsistency(BaseModel):
    type: Literal["VITAL_TREND", "MED_STATE", "ALLERGY_COLLISION"]
    severity: Literal["INFO", "WARN", "CRITICAL"]
    message: str  # German, physician-readable
    evidence: dict[str, str | float | dict[str, str | float]]


class CompletenessScore(BaseModel):
    score: float  # 0.0 – 1.0
    missing_items: list[str]
    details: dict[str, bool] = Field(default_factory=dict)


class HandoverCard(BaseModel):
    card_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    patient_id: str
    recorded_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    raw_transcript: str
    sbar: SBARStructure
    inconsistencies: list[Inconsistency] = Field(default_factory=list)
    completeness: CompletenessScore
    signed: bool = False
    signed_at: str | None = None
    signed_by: str | None = None


class HandoverSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    started_by: str = "Dr. Müller"
    started_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    patient_ids: list[str] = Field(default_factory=list)
    card_ids: list[str] = Field(default_factory=list)
