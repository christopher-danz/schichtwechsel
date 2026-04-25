from typing import Protocol

from app.models.handover import HandoverCard, Inconsistency
from app.models.patient import Patient


class InconsistencyDetector(Protocol):
    def detect(self, card: HandoverCard, patient: Patient) -> list[Inconsistency]:
        ...
