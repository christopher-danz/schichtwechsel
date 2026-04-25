from app.models.handover import HandoverCard, Inconsistency
from app.models.patient import Patient

_ACTION_KEYWORDS: dict[str, str] = {
    "abgesetzt": "discontinued",
    "absetzen": "discontinued",
    "pausiert": "paused",
    "pausieren": "paused",
    "gestoppt": "discontinued",
    "neu gestartet": "active",
    "angefangen": "active",
}


def _find_medication_name(word: str, patient: Patient) -> str | None:
    """Return canonical medication name if word fuzzy-matches any patient med."""
    word_lower = word.lower()
    for med in patient.medications:
        if med.name.lower() in word_lower or word_lower in med.name.lower():
            return med.name
    return None


class MedicationStateDetector:
    def detect(self, card: HandoverCard, patient: Patient) -> list[Inconsistency]:
        result: list[Inconsistency] = []
        transcript_lower = card.raw_transcript.lower()

        for action_word, implied_state in _ACTION_KEYWORDS.items():
            if action_word not in transcript_lower:
                continue
            # Find the surrounding window (±4 words) around the action keyword
            words = transcript_lower.split()
            for i, w in enumerate(words):
                if action_word not in w:
                    continue
                window = words[max(0, i - 4) : i + 5]
                for candidate in window:
                    med_name = _find_medication_name(candidate, patient)
                    if not med_name:
                        continue
                    # Compare implied_state with actual status in patient record
                    actual = next(
                        (m for m in patient.medications if m.name == med_name), None
                    )
                    if actual and actual.status != implied_state:
                        result.append(
                            Inconsistency(
                                type="MED_STATE",
                                severity="WARN",
                                message=(
                                    f"Sie sagten '{med_name} {action_word}', "
                                    f"Akte zeigt Status: '{actual.status}'"
                                ),
                                evidence={
                                    "medication": med_name,
                                    "claimed_action": action_word,
                                    "implied_state": implied_state,
                                    "recorded_status": actual.status,
                                },
                            )
                        )

        return result
