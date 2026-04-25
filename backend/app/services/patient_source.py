"""
PatientSource — loads patient data from local JSON files.
FHIR integration is a stub; flip prefer_fhir=True when the sandbox is reachable.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.models.patient import Patient, PatientSummary

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "synthetic"


class PatientSource:
    def __init__(self, prefer_fhir: bool = False) -> None:
        self._prefer_fhir = prefer_fhir
        self._patients: dict[str, Patient] = {}
        self._load_from_json()
        logger.info("PatientSource loaded %d patients", len(self._patients))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_patients(self) -> list[Patient]:
        return sorted(self._patients.values(), key=lambda p: p.bed)

    def list_summaries(self) -> list[PatientSummary]:
        return [
            PatientSummary(
                patient_id=p.patient_id,
                bed=p.bed,
                demographics=p.demographics,
                main_diagnosis=p.main_diagnosis,
            )
            for p in self.list_patients()
        ]

    def get_patient(self, patient_id: str) -> Patient | None:
        return self._patients.get(patient_id)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_from_json(self) -> None:
        for path in sorted(_DATA_DIR.glob("patient_*.json")):
            try:
                patient = Patient(**json.loads(path.read_text()))
                self._patients[patient.patient_id] = patient
            except Exception:
                logger.exception("Failed to load %s", path)
