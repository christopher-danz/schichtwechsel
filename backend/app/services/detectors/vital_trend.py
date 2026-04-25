from datetime import datetime, timezone

from app.models.handover import HandoverCard, Inconsistency
from app.models.patient import Patient, VitalReading

_FEVER_FREE_KEYWORDS = [
    "fieberfrei",
    "kein fieber",
    "fieber weg",
    "afebril",
    "apyrexie",
    "fever free",
    "temperatur normal",
    "keine temperatur",
    "36,",  # "36,8" — implies normal temperature mentioned
]

_THRESHOLDS: dict[str, dict[str, float]] = {
    "temperature": {"fever_above": 37.8},
    "oxygen_saturation": {"low_below": 92.0},
    "heart_rate": {"tachy_above": 100.0, "brady_below": 50.0},
}


def _latest_per_param(vitals: list[VitalReading]) -> dict[str, VitalReading]:
    latest: dict[str, VitalReading] = {}
    for v in vitals:
        existing = latest.get(v.parameter)
        if not existing or v.recorded_at > existing.recorded_at:
            latest[v.parameter] = v
    return latest


def _hours_ago(iso: str) -> int:
    try:
        ts = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - ts
        return int(delta.total_seconds() / 3600)
    except ValueError:
        return 0


class VitalTrendDetector:
    def detect(self, card: HandoverCard, patient: Patient) -> list[Inconsistency]:
        result: list[Inconsistency] = []
        latest = _latest_per_param(patient.recent_vitals)
        transcript_lower = card.raw_transcript.lower()

        # VITAL_TREND: physician claims fever-free but last reading is elevated
        if any(kw in transcript_lower for kw in _FEVER_FREE_KEYWORDS):
            temp = latest.get("temperature")
            if temp and temp.value > _THRESHOLDS["temperature"]["fever_above"]:
                h = _hours_ago(temp.recorded_at)
                result.append(
                    Inconsistency(
                        type="VITAL_TREND",
                        severity="WARN",
                        message=(
                            f"Sie sagten 'fieberfrei', letzte gemessene Temperatur "
                            f"war {temp.value:.1f}°C vor {h}h"
                        ),
                        evidence={
                            "claim": "fieberfrei",
                            "actual": {
                                "temperature": temp.value,
                                "timestamp": temp.recorded_at,
                            },
                        },
                    )
                )

        # VITAL_TREND: physician claims stable sats but SpO2 is low
        spo2_ok_keywords = ["sättigung gut", "sättigung stabil", "spo2 gut", "spo2 stabil"]
        if any(kw in transcript_lower for kw in spo2_ok_keywords):
            spo2 = latest.get("oxygen_saturation")
            if spo2 and spo2.value < _THRESHOLDS["oxygen_saturation"]["low_below"]:
                h = _hours_ago(spo2.recorded_at)
                result.append(
                    Inconsistency(
                        type="VITAL_TREND",
                        severity="WARN",
                        message=(
                            f"Sie sagten 'Sättigung gut', letzte gemessene SpO₂ "
                            f"war {spo2.value:.0f}% vor {h}h"
                        ),
                        evidence={
                            "claim": "Sättigung gut",
                            "actual": {
                                "oxygen_saturation": spo2.value,
                                "timestamp": spo2.recorded_at,
                            },
                        },
                    )
                )

        # Also check VitalMentions from SBAR for stable/improving qualifiers
        for mention in card.sbar.assessment.vital_mentions:
            if mention.qualifier not in ("stable", "improving", "unchanged"):
                continue
            threshold = _THRESHOLDS.get(mention.parameter, {})
            reading = latest.get(mention.parameter)
            if not reading:
                continue
            if "fever_above" in threshold and reading.value > threshold["fever_above"]:
                h = _hours_ago(reading.recorded_at)
                result.append(
                    Inconsistency(
                        type="VITAL_TREND",
                        severity="WARN",
                        message=(
                            f"SBAR zeigt '{mention.parameter}' als stabil, "
                            f"Messung zeigt {reading.value} vor {h}h"
                        ),
                        evidence={
                            "sbar_qualifier": mention.qualifier,
                            "actual": {
                                mention.parameter: reading.value,
                                "timestamp": reading.recorded_at,
                            },
                        },
                    )
                )

        return result
