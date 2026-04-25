from app.models.handover import CompletenessScore, HandoverCard
from app.models.patient import Patient

_CRITICAL_WEIGHT = 0.4
_OPTIONAL_WEIGHT = 0.05

_MISSING_LABELS: dict[str, str] = {
    "allergies_mentioned_or_explicitly_none": "allergies_not_mentioned",
    "main_problem_in_situation": "situation_empty",
    "at_least_one_action": "no_recommendation",
    "vital_mentioned": "no_vital_signs",
    "medications_mentioned": "no_medications",
    "pending_diagnostics_mentioned": "open_diagnostics_not_addressed",
}


def compute_completeness(card: HandoverCard, patient: Patient) -> CompletenessScore:
    bg = card.sbar.background
    details: dict[str, bool] = {}

    # Critical
    details["allergies_mentioned_or_explicitly_none"] = (
        len(bg.allergies_mentioned) > 0 or bg.allergies_explicitly_none
    )
    details["main_problem_in_situation"] = bool(card.sbar.situation.strip())
    details["at_least_one_action"] = len(card.sbar.recommendation) > 0

    # Optional
    details["vital_mentioned"] = len(card.sbar.assessment.vital_mentions) > 0
    details["medications_mentioned"] = len(bg.current_medications) > 0
    # open diagnostics: only required if the patient actually has any open ones
    has_open = len(patient.open_diagnostics) > 0
    details["pending_diagnostics_mentioned"] = (
        not has_open or len(card.sbar.assessment.pending_diagnostics) > 0
    )

    critical = ["allergies_mentioned_or_explicitly_none", "main_problem_in_situation", "at_least_one_action"]
    optional = ["vital_mentioned", "medications_mentioned", "pending_diagnostics_mentioned"]

    missing_critical = sum(1 for k in critical if not details[k])
    missing_optional = sum(1 for k in optional if not details[k])

    score = max(0.0, 1.0 - missing_critical * _CRITICAL_WEIGHT - missing_optional * _OPTIONAL_WEIGHT)

    missing_items = [_MISSING_LABELS[k] for k in critical + optional if not details[k]]

    return CompletenessScore(score=round(score, 2), missing_items=missing_items, details=details)
