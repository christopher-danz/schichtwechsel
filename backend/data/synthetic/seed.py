"""
Deterministic synthetic patient data generator.
Usage: python -m data.synthetic.seed   (from backend/)
Same SEED → same timestamps and values, for demo reproducibility.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED = 42
# Fixed demo reference: evening handover on 2026-04-25
REFERENCE_TIME = datetime(2026, 4, 25, 14, 30, 0)
OUT_DIR = Path(__file__).parent


def _readings(
    rng: random.Random,
    parameter: str,
    unit: str,
    start_val: float,
    end_val: float,
    noise_std: float,
    start_offset_h: float,
    end_offset_h: float,
    step_min: int = 30,
) -> list[dict]:
    start = REFERENCE_TIME - timedelta(hours=start_offset_h)
    end = REFERENCE_TIME - timedelta(hours=end_offset_h)
    total_min = int((end - start).total_seconds() / 60)
    steps = total_min // step_min
    readings = []
    for i in range(steps + 1):
        t = start + timedelta(minutes=step_min * i)
        progress = i / max(steps, 1)
        val = start_val + progress * (end_val - start_val) + rng.gauss(0, noise_std)
        readings.append(
            {
                "parameter": parameter,
                "value": round(val, 1),
                "unit": unit,
                "recorded_at": t.isoformat(),
            }
        )
    return readings


def patient_001(rng: random.Random) -> dict:
    """Frau Schmidt — Pneumonie Tag 3. Triggers VITAL_TREND inconsistency.
    Temperature last measured 4h ago at 38.4°C.
    """
    vitals = (
        # Temperature: 24h window but stops at T-4h (last measured 4h ago)
        _readings(rng, "temperature", "°C", 39.1, 38.4, 0.08, 24, 4)
        # SpO2 and HR measured up to 30 min ago
        + _readings(rng, "oxygen_saturation", "%", 95.0, 96.5, 0.4, 24, 0.5)
        + _readings(rng, "heart_rate", "bpm", 92.0, 84.0, 2.5, 24, 0.5)
    )
    return {
        "patient_id": "synth-001",
        "bed": "1",
        "demographics": {"age": 67, "sex": "F", "name": "Frau Schmidt"},
        "main_diagnosis": "Pneumonie",
        "allergies": [],
        "medications": [
            {
                "name": "Amoxicillin/Clavulansäure",
                "dose": "875/125 mg",
                "frequency": "3× täglich",
                "route": "oral",
                "status": "active",
                "started_at": "2026-04-22",
            },
            {
                "name": "Paracetamol",
                "dose": "1000 mg",
                "frequency": "bei Bedarf, max. 4× täglich",
                "route": "oral",
                "status": "active",
                "started_at": "2026-04-22",
            },
        ],
        "recent_vitals": vitals,
        "open_diagnostics": [
            {
                "name": "CRP-Kontrolle",
                "ordered_at": "2026-04-25T08:00:00",
                "status": "pending",
            }
        ],
    }


def patient_002(rng: random.Random) -> dict:
    """Herr Weber — postoperative Cholezystektomie Tag 1. Triggers MED_STATE.
    Metamizol is active in chart; physician says 'Schmerzmittel abgesetzt'.
    """
    vitals = (
        _readings(rng, "temperature", "°C", 37.2, 36.9, 0.06, 24, 0.5)
        + _readings(rng, "oxygen_saturation", "%", 97.0, 98.5, 0.3, 24, 0.5)
        + _readings(rng, "heart_rate", "bpm", 78.0, 72.0, 2.0, 24, 0.5)
    )
    return {
        "patient_id": "synth-002",
        "bed": "2",
        "demographics": {"age": 54, "sex": "M", "name": "Herr Weber"},
        "main_diagnosis": "Postoperativ nach laparoskopischer Cholezystektomie (Tag 1)",
        "allergies": [],
        "medications": [
            {
                "name": "Metamizol",
                "dose": "1000 mg",
                "frequency": "4× täglich",
                "route": "intravenös",
                "status": "active",
                "started_at": "2026-04-25",
            },
            {
                "name": "Enoxaparin",
                "dose": "40 mg",
                "frequency": "1× täglich",
                "route": "subkutan",
                "status": "active",
                "started_at": "2026-04-25",
            },
            {
                "name": "Pantoprazol",
                "dose": "40 mg",
                "frequency": "1× täglich",
                "route": "oral",
                "status": "active",
                "started_at": "2026-04-25",
            },
        ],
        "recent_vitals": vitals,
        "open_diagnostics": [
            {
                "name": "Wundkontrolle",
                "ordered_at": "2026-04-25T07:00:00",
                "status": "pending",
            }
        ],
    }


def patient_003(rng: random.Random) -> dict:
    """Frau Kowalski — akute kardiale Dekompensation. Triggers ALLERGY_COLLISION (stretch).
    Documented penicillin allergy; if physician mentions amoxicillin → CRITICAL.
    """
    vitals = (
        _readings(rng, "temperature", "°C", 37.3, 37.0, 0.07, 24, 0.5)
        + _readings(rng, "oxygen_saturation", "%", 92.0, 94.0, 0.5, 24, 0.5)
        + _readings(rng, "heart_rate", "bpm", 105.0, 94.0, 3.0, 24, 0.5)
    )
    return {
        "patient_id": "synth-003",
        "bed": "3",
        "demographics": {"age": 78, "sex": "F", "name": "Frau Kowalski"},
        "main_diagnosis": "Akute kardiale Dekompensation (frisch verlegt aus Notaufnahme)",
        "allergies": [
            {
                "substance": "Penicillin",
                "reaction": "Urtikaria, Dyspnoe",
                "severity": "severe",
            }
        ],
        "medications": [
            {
                "name": "Furosemid",
                "dose": "40 mg",
                "frequency": "2× täglich",
                "route": "oral",
                "status": "active",
                "started_at": "2026-04-25",
            },
            {
                "name": "Ramipril",
                "dose": "5 mg",
                "frequency": "1× täglich",
                "route": "oral",
                "status": "active",
                "started_at": "2026-04-25",
            },
            {
                "name": "Torasemid",
                "dose": "10 mg",
                "frequency": "1× täglich",
                "route": "oral",
                "status": "active",
                "started_at": "2026-04-25",
            },
        ],
        "recent_vitals": vitals,
        "open_diagnostics": [
            {
                "name": "Echokardiographie",
                "ordered_at": "2026-04-25T10:00:00",
                "status": "pending",
            },
            {
                "name": "BNP",
                "ordered_at": "2026-04-25T09:00:00",
                "status": "in_progress",
            },
        ],
    }


def main() -> None:
    rng = random.Random(SEED)
    patients = [patient_001(rng), patient_002(rng), patient_003(rng)]
    for i, p in enumerate(patients, start=1):
        path = OUT_DIR / f"patient_00{i}.json"
        path.write_text(json.dumps(p, ensure_ascii=False, indent=2))
        print(f"wrote {path}  ({len(p['recent_vitals'])} vitals)")


if __name__ == "__main__":
    main()
