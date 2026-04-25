from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, patients, transcribe, structure
from app.services.card_store import CardStore
from app.services.gliner_service import GLiNERService
from app.services.patient_source import PatientSource
from app.services.transcription import TranscriptionService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.patient_source = PatientSource()
    app.state.transcription_service = TranscriptionService()
    app.state.gliner_service = GLiNERService()
    app.state.card_store = CardStore()
    yield


app = FastAPI(title="ShiftChange-Bot API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(patients.router, prefix="/api")
app.include_router(transcribe.router, prefix="/api")
app.include_router(structure.router, prefix="/api")
