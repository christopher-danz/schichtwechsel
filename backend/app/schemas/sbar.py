"""
GLiNER2 extraction schema for SBAR handover structuring.

Kept separate from models/sbar.py so fine-tuned adapters are swappable
without touching the output contract.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gliner2 import GLiNER2


def build_sbar_schema(extractor: "GLiNER2") -> object:
    return (
        extractor.create_schema()
        .entities(
            {
                "patient_identifier": "Name, Bettnummer, Alter oder Geschlecht des Patienten",
                "main_problem": "Primärdiagnose oder aktuelles Hauptproblem heute",
                "admission_reason": "Aufnahmegrund ins Krankenhaus",
                "relevant_history": "Vorerkrankungen, Komorbiditäten, relevante Anamnese",
                "medication": "Medikamentenname, Dosis oder Medikamentenaktion (starten, absetzen, pausieren, weiter)",
                "allergy": "Allergie oder Unverträglichkeit, die der Arzt erwähnt",
                "vital_sign": "Vitalparameter-Wert oder Trend (Temperatur, Blutdruck, Sättigung, Puls etc.)",
                "complication": "Komplikation, Verschlechterung oder besorgniserregender Befund",
                "pending_test": "Ausstehende Labor-, Bildgebungs- oder andere Diagnostik",
                "action_item": "Konkrete Anordnung oder Aufgabe für die nächste Schicht",
                "family_communication": "Familienangehörige, Besuch oder Kommunikationspunkt",
            }
        )
        .classification("overall_severity", ["routine", "watch", "urgent"])
        .structure("sbar_card")
        .field(
            "situation",
            dtype="str",
            description="1-2 Sätze zum aktuellen Zustand des Patienten",
        )
        .field("admission_reason", dtype="str")
        .field("admission_date", dtype="str")
        .field(
            "allergies_explicitly_none",
            dtype="str",
            choices=["yes", "no", "not_mentioned"],
        )
        .field(
            "current_status",
            dtype="str",
            description="Gesamtbeurteilung des Patientenzustands heute",
        )
        .field(
            "key_actions",
            dtype="list",
            description="Liste konkreter Anordnungen für die nächste Schicht",
        )
    )
