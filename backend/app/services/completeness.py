import re

from app.models.handover import CompletenessScore, HandoverCard
from app.models.patient import Patient

# Proportional penalties: missing ALL critical fields = -40%, all optional = -15%
_CRITICAL_MAX_PENALTY = 0.40
_OPTIONAL_MAX_PENALTY = 0.15

_MISSING_LABELS: dict[str, str] = {
    "allergies_mentioned_or_explicitly_none": "allergies_not_mentioned",
    "main_problem_in_situation": "situation_empty",
    "at_least_one_action": "no_recommendation",
    "vital_mentioned": "no_vital_signs",
    "medications_mentioned": "no_medications",
    "pending_diagnostics_mentioned": "open_diagnostics_not_addressed",
}


def _first_token(name: str) -> str:
    """Extract the first significant token from a drug/diagnostic name."""
    return re.split(r"[\s/\-]", name.lower())[0]


def compute_completeness(card: HandoverCard, patient: Patient) -> CompletenessScore:
    bg = card.sbar.background
    transcript_lower = card.raw_transcript.lower()
    details: dict[str, bool] = {}

    # ── Critical ──────────────────���──────────────────────────────���────────
    details["allergies_mentioned_or_explicitly_none"] = (
        len(bg.allergies_mentioned) > 0 or bg.allergies_explicitly_none
    )
    details["main_problem_in_situation"] = bool(card.sbar.situation.strip())
    details["at_least_one_action"] = len(card.sbar.recommendation) > 0

    # ── Optional ──────────────────────────────────────────────────────────
    details["vital_mentioned"] = len(card.sbar.assessment.vital_mentions) > 0

    # Medications: SBAR extraction or transcript keyword fallback
    active_med_tokens = [
        _first_token(m.name) for m in patient.medications if m.status == "active"
    ]
    details["medications_mentioned"] = len(bg.current_medications) > 0 or any(
        t in transcript_lower for t in active_med_tokens
    )

    # Pending diagnostics: only required when patient actually has open ones
    has_open = len(patient.open_diagnostics) > 0
    diag_tokens = [_first_token(d.name) for d in patient.open_diagnostics]
    details["pending_diagnostics_mentioned"] = (
        not has_open
        or len(card.sbar.assessment.pending_diagnostics) > 0
        or any(t in transcript_lower for t in diag_tokens)
    )

    critical = [
        "allergies_mentioned_or_explicitly_none",
        "main_problem_in_situation",
        "at_least_one_action",
    ]
    optional = ["vital_mentioned", "medications_mentioned", "pending_diagnostics_mentioned"]

    missing_critical = sum(1 for k in critical if not details[k])
    missing_optional = sum(1 for k in optional if not details[k])

    # Proportional penalty so missing 1-of-3 critical ≈ 13.3% (→ 87% score)
    score = max(
        0.0,
        1.0
        - (missing_critical / len(critical)) * _CRITICAL_MAX_PENALTY
        - (missing_optional / len(optional)) * _OPTIONAL_MAX_PENALTY,
    )

    missing_items = [_MISSING_LABELS[k] for k in critical + optional if not details[k]]

    return CompletenessScore(score=round(score, 2), missing_items=missing_items, details=details)
