from pydantic import BaseModel, Field
from typing import Literal


class Allergy(BaseModel):
    substance: str
    reaction: str | None = None
    severity: Literal["mild", "moderate", "severe"] = "moderate"


class Medication(BaseModel):
    name: str
    dose: str | None = None
    frequency: str | None = None
    route: str | None = None
    status: Literal["active", "paused", "discontinued"] = "active"
    started_at: str | None = None  # ISO date


class VitalReading(BaseModel):
    parameter: Literal[
        "temperature",
        "blood_pressure",
        "heart_rate",
        "oxygen_saturation",
        "respiratory_rate",
        "pain_score",
    ]
    value: float
    unit: str
    recorded_at: str  # ISO datetime


class OpenDiagnostic(BaseModel):
    name: str
    ordered_at: str | None = None  # ISO datetime
    status: Literal["pending", "in_progress", "resulted"] = "pending"
    result: str | None = None


class PatientDemographics(BaseModel):
    age: int
    sex: Literal["M", "F", "D"]
    name: str


class Patient(BaseModel):
    patient_id: str
    bed: str
    demographics: PatientDemographics
    main_diagnosis: str
    allergies: list[Allergy] = Field(default_factory=list)
    medications: list[Medication] = Field(default_factory=list)
    recent_vitals: list[VitalReading] = Field(default_factory=list)
    open_diagnostics: list[OpenDiagnostic] = Field(default_factory=list)


class PatientSummary(BaseModel):
    """Lightweight patient object returned by GET /api/patients."""

    patient_id: str
    bed: str
    demographics: PatientDemographics
    main_diagnosis: str
