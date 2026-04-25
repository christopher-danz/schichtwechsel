from pydantic import BaseModel, Field
from typing import Literal


class BackgroundFields(BaseModel):
    admission_reason: str | None = None
    admission_date: str | None = None  # ISO date
    relevant_history: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    allergies_mentioned: list[str] = Field(default_factory=list)
    allergies_explicitly_none: bool = False  # physician said "no known allergies"


class VitalMention(BaseModel):
    parameter: Literal[
        "temperature",
        "blood_pressure",
        "heart_rate",
        "oxygen_saturation",
        "respiratory_rate",
        "pain_score",
    ]
    value: str | None = None
    qualifier: Literal["stable", "improving", "worsening", "unchanged", "abnormal"] | None = None


class AssessmentFields(BaseModel):
    current_status: str | None = None
    vital_mentions: list[VitalMention] = Field(default_factory=list)
    complications: list[str] = Field(default_factory=list)
    pending_diagnostics: list[str] = Field(default_factory=list)


class ActionItem(BaseModel):
    action: str
    timing: str | None = None  # "tonight", "before rounds"
    priority: Literal["routine", "urgent", "critical"] = "routine"


class SBARStructure(BaseModel):
    situation: str
    background: BackgroundFields
    assessment: AssessmentFields
    recommendation: list[ActionItem]
