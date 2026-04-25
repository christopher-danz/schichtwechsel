from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.models.handover import HandoverCard, Inconsistency, CompletenessScore
from app.models.sbar import SBARStructure
from app.services.card_store import CardStore
from app.services.completeness import compute_completeness
from app.services.detectors.medication_state import MedicationStateDetector
from app.services.detectors.vital_trend import VitalTrendDetector
from app.services.gliner_service import GLiNERService
from app.services.patient_source import PatientSource

router = APIRouter()

_DETECTORS = [VitalTrendDetector(), MedicationStateDetector()]


class StructureRequest(BaseModel):
    transcript: str
    patient_id: str


class StructureResponse(BaseModel):
    card_id: str
    sbar: SBARStructure
    inconsistencies: list[Inconsistency]
    completeness: CompletenessScore


@router.post("/structure", response_model=StructureResponse)
async def structure_transcript(
    body: StructureRequest, request: Request
) -> StructureResponse:
    patient_source: PatientSource = request.app.state.patient_source
    gliner_svc: GLiNERService = request.app.state.gliner_service
    card_store: CardStore = request.app.state.card_store

    patient = patient_source.get_patient(body.patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    sbar = await gliner_svc.extract_sbar(body.transcript)

    # Build card with placeholder completeness so detectors can reference it
    placeholder_completeness = CompletenessScore(score=0.0, missing_items=[])
    card = HandoverCard(
        patient_id=body.patient_id,
        raw_transcript=body.transcript,
        sbar=sbar,
        completeness=placeholder_completeness,
    )

    # Run all detectors
    inconsistencies: list[Inconsistency] = []
    for detector in _DETECTORS:
        inconsistencies.extend(detector.detect(card, patient))

    card.inconsistencies = inconsistencies
    card.completeness = compute_completeness(card, patient)

    card_store.save(card)

    return StructureResponse(
        card_id=card.card_id,
        sbar=card.sbar,
        inconsistencies=card.inconsistencies,
        completeness=card.completeness,
    )
