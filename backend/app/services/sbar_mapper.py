"""
Maps raw GLiNER2 extraction output to the typed SBARStructure.

The heuristic_sbar() function provides a fallback when GLiNER2 is not
available — it produces a usable (if shallow) SBAR from raw text so
detectors and completeness scoring can still run.
"""

import re

from app.models.sbar import (
    ActionItem,
    AssessmentFields,
    BackgroundFields,
    SBARStructure,
    VitalMention,
)

_VITAL_KEYWORDS: dict[str, str] = {
    "temperatur": "temperature",
    "fieber": "temperature",
    "puls": "heart_rate",
    "herzfrequenz": "heart_rate",
    "blutdruck": "blood_pressure",
    "rr": "blood_pressure",
    "sättigung": "oxygen_saturation",
    "spo2": "oxygen_saturation",
    "atemfrequenz": "respiratory_rate",
    "af ": "respiratory_rate",
    "schmerz": "pain_score",
    "vas": "pain_score",
}

_QUALIFIER_MAP: dict[str, str] = {
    "stabil": "stable",
    "gut": "stable",
    "normal": "stable",
    "besser": "improving",
    "verbessert": "improving",
    "schlechter": "worsening",
    "verschlechtert": "worsening",
    "unverändert": "unchanged",
    "auffällig": "abnormal",
    "erhöht": "abnormal",
    "erniedrigt": "abnormal",
}

_ACTION_VERBS = re.compile(
    r"\b(bitte|soll|muss|weiter|kontrollier|überprüf|bestell|verabreic|gib|veranlass)\w*",
    re.IGNORECASE,
)

_ALLERGIES_NONE_PATTERNS = [
    "keine allergien",
    "keine bekannten allergien",
    "allergieanamnese leer",
    "keine unverträglichkeit",
    "keine bekannte unverträglichkeit",
]


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]


def _detect_vital_mentions(text: str) -> list[VitalMention]:
    text_lower = text.lower()
    seen: set[str] = set()
    mentions: list[VitalMention] = []
    for keyword, parameter in _VITAL_KEYWORDS.items():
        if keyword not in text_lower or parameter in seen:
            continue
        seen.add(parameter)
        qualifier: str | None = None
        # Look for a qualifier word near the keyword
        idx = text_lower.index(keyword)
        window = text_lower[max(0, idx - 30) : idx + 50]
        for q_de, q_en in _QUALIFIER_MAP.items():
            if q_de in window:
                qualifier = q_en
                break
        mentions.append(VitalMention(parameter=parameter, qualifier=qualifier))  # type: ignore[arg-type]
    return mentions


def _detect_allergies_explicitly_none(text: str) -> bool:
    text_lower = text.lower()
    return any(p in text_lower for p in _ALLERGIES_NONE_PATTERNS)


def _extract_action_sentences(text: str) -> list[ActionItem]:
    items: list[ActionItem] = []
    for sentence in _sentences(text):
        if _ACTION_VERBS.search(sentence):
            items.append(ActionItem(action=sentence))
    return items


def heuristic_sbar(transcript: str) -> SBARStructure:
    """Rule-based SBAR extraction — no model needed."""
    sentences = _sentences(transcript)
    situation = " ".join(sentences[:2]) if sentences else transcript[:200]

    return SBARStructure(
        situation=situation,
        background=BackgroundFields(
            allergies_explicitly_none=_detect_allergies_explicitly_none(transcript),
        ),
        assessment=AssessmentFields(
            current_status=" ".join(sentences[2:5]) if len(sentences) > 2 else None,
            vital_mentions=_detect_vital_mentions(transcript),
        ),
        recommendation=_extract_action_sentences(transcript),
    )


def map_gliner_to_sbar(gliner_output: dict, transcript: str) -> SBARStructure:
    """Map GLiNER2 extract() output to SBARStructure."""
    structure: dict = gliner_output.get("sbar_card") or {}
    entities: dict = gliner_output.get("entities") or {}

    situation = structure.get("situation") or ""
    if not situation:
        sentences = _sentences(transcript)
        situation = " ".join(sentences[:2]) if sentences else transcript[:200]

    allergies_raw = structure.get("allergies_explicitly_none", "not_mentioned")

    def _as_list(val: object) -> list[str]:
        if isinstance(val, list):
            return [str(v) for v in val if v]
        if isinstance(val, str) and val:
            return [val]
        return []

    vital_mentions = _detect_vital_mentions(transcript)

    raw_actions = _as_list(structure.get("key_actions") or entities.get("action_item", []))
    recommendation = [ActionItem(action=a) for a in raw_actions if a.strip()]
    if not recommendation:
        recommendation = _extract_action_sentences(transcript)

    return SBARStructure(
        situation=situation,
        background=BackgroundFields(
            admission_reason=structure.get("admission_reason") or None,
            admission_date=structure.get("admission_date") or None,
            relevant_history=_as_list(entities.get("relevant_history", [])),
            current_medications=_as_list(entities.get("medication", [])),
            allergies_mentioned=_as_list(entities.get("allergy", [])),
            allergies_explicitly_none=(allergies_raw == "yes"),
        ),
        assessment=AssessmentFields(
            current_status=structure.get("current_status") or None,
            vital_mentions=vital_mentions,
            complications=_as_list(entities.get("complication", [])),
            pending_diagnostics=_as_list(entities.get("pending_test", [])),
        ),
        recommendation=recommendation,
    )
