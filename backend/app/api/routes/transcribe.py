from fastapi import APIRouter, File, Request, UploadFile
from pydantic import BaseModel

from app.services.transcription import TranscriptionService

router = APIRouter()


class TranscribeResponse(BaseModel):
    transcript: str


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    request: Request,
    audio: UploadFile = File(...),
) -> TranscribeResponse:
    audio_bytes = await audio.read()
    svc: TranscriptionService = request.app.state.transcription_service
    transcript = await svc.transcribe(
        audio_bytes, audio.content_type or "audio/webm"
    )
    return TranscribeResponse(transcript=transcript)
