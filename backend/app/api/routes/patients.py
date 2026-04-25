from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.models.patient import Patient, PatientSummary
from app.services.patient_source import PatientSource

router = APIRouter(tags=["patients"])


class PatientListResponse(BaseModel):
    patients: list[PatientSummary]


def _source(request: Request) -> PatientSource:
    return request.app.state.patient_source


@router.get("/patients", response_model=PatientListResponse)
async def list_patients(request: Request) -> PatientListResponse:
    return PatientListResponse(patients=_source(request).list_summaries())


@router.get("/patients/{patient_id}", response_model=Patient)
async def get_patient(patient_id: str, request: Request) -> Patient:
    patient = _source(request).get_patient(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")
    return patient
