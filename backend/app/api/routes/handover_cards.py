import hashlib
import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.models.handover import CompletenessScore
from app.services.card_store import CardStore
from app.services.completeness import compute_completeness
from app.services.patient_source import PatientSource

router = APIRouter()

_CONFIRM_ITEM_ALIASES = {
    "allergies": "allergies_not_mentioned",
}


class ConfirmMissingRequest(BaseModel):
    item: str
    value: str  # "explicitly_none" | "addressed_separately" | "not_applicable"


class ConfirmMissingResponse(BaseModel):
    completeness: CompletenessScore


class SignRequest(BaseModel):
    signed_by: str


class SignResponse(BaseModel):
    card_id: str
    signed_at: str
    audit_hash: str


def _audit_hash(card_id: str, patient_id: str, transcript: str, signed_by: str, signed_at: str) -> str:
    payload = json.dumps(
        {
            "card_id": card_id,
            "patient_id": patient_id,
            "transcript_hash": hashlib.sha256(transcript.encode()).hexdigest()[:16],
            "signed_by": signed_by,
            "signed_at": signed_at,
        },
        sort_keys=True,
    )
    return "sha256-" + hashlib.sha256(payload.encode()).hexdigest()


@router.post(
    "/handover-cards/{card_id}/confirm-missing",
    response_model=ConfirmMissingResponse,
)
async def confirm_missing(
    card_id: str,
    body: ConfirmMissingRequest,
    request: Request,
) -> ConfirmMissingResponse:
    card_store: CardStore = request.app.state.card_store
    patient_source: PatientSource = request.app.state.patient_source

    card = card_store.get(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")

    patient = patient_source.get_patient(card.patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Apply the confirmation to the SBAR data so recomputation picks it up
    if body.item == "allergies" and body.value in ("explicitly_none", "addressed_separately"):
        card.sbar.background.allergies_explicitly_none = True

    card.completeness = compute_completeness(card, patient)
    card_store.update(card)

    return ConfirmMissingResponse(completeness=card.completeness)


@router.post("/handover-cards/{card_id}/sign", response_model=SignResponse)
async def sign_card(
    card_id: str,
    body: SignRequest,
    request: Request,
) -> SignResponse:
    card_store: CardStore = request.app.state.card_store

    card = card_store.get(card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    if card.signed:
        raise HTTPException(status_code=409, detail="Card already signed")

    signed_at = datetime.now(timezone.utc).isoformat()
    audit = _audit_hash(
        card_id=card.card_id,
        patient_id=card.patient_id,
        transcript=card.raw_transcript,
        signed_by=body.signed_by,
        signed_at=signed_at,
    )

    card.signed = True
    card.signed_at = signed_at
    card.signed_by = body.signed_by
    card_store.update(card)

    return SignResponse(card_id=card_id, signed_at=signed_at, audit_hash=audit)
