# Schichtwechsel — Detailed Specification

> Complements `CLAUDE.md`. Loaded into a session via `@docs/spec.md` when
> spec-relevant work is happening. This file is the implementation
> reference. If something here conflicts with `CLAUDE.md`, `CLAUDE.md`
> wins.

## SBAR schema (complete)

The SBAR structure is the output form of the structuring step. Every
field is optional at the semantic level (the model only extracts what
was said), but completeness scoring checks which fields are expected
for each patient type.

```python
# backend/models/sbar.py
from pydantic import BaseModel, Field
from typing import Literal

class BackgroundFields(BaseModel):
    admission_reason: str | None = None
    admission_date: str | None = None       # ISO date
    relevant_history: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    allergies_mentioned: list[str] = Field(default_factory=list)
    allergies_explicitly_none: bool = False  # physician said "no allergies"

class VitalMention(BaseModel):
    parameter: Literal["temperature", "blood_pressure", "heart_rate",
                       "oxygen_saturation", "respiratory_rate", "pain_score"]
    value: str | None = None
    qualifier: Literal["stable", "improving", "worsening", "unchanged",
                       "abnormal", None] = None

class AssessmentFields(BaseModel):
    current_status: str | None = None
    vital_mentions: list[VitalMention] = Field(default_factory=list)
    complications: list[str] = Field(default_factory=list)
    pending_diagnostics: list[str] = Field(default_factory=list)

class ActionItem(BaseModel):
    action: str
    timing: str | None = None       # "tonight", "before rounds"
    priority: Literal["routine", "urgent", "critical"] = "routine"

class SBARStructure(BaseModel):
    situation: str
    background: BackgroundFields
    assessment: AssessmentFields
    recommendation: list[ActionItem]
```

Important: GLiNER2 produces flat entities plus structured extraction.
The mapping layer from GLiNER2 output to the structure above is its own
function, `backend/services/sbar_mapper.py`. Keep them separate so
fine-tuned outputs are swappable.

## API contracts

Six endpoints are enough for the MVP. More is feature creep.

### `GET /api/patients`
Returns the patient list for the current demo shift.

```json
Response 200:
{
  "patients": [
    {
      "patient_id": "synth-001",
      "bed": "1",
      "demographics": {"age": 67, "sex": "F", "name": "Frau Schmidt"},
      "main_diagnosis": "Pneumonie"
    },
    ...
  ]
}
```

### `GET /api/patients/{patient_id}`
Full patient object including vitals, meds, allergies, diagnostics.

### `POST /api/transcribe`
Audio in, German text out. Wraps Gradium (or Whisper fallback).

```json
Request (multipart/form-data):
  audio: <blob, webm/wav>
  patient_id: "synth-001"

Response 200:
{
  "transcript": "Patient klagt seit gestern abend...",
  "duration_ms": 73420,
  "provider": "gradium" | "whisper-local" | "browser-webspeech"
}
```

### `POST /api/structure`
Transcript plus patient context in, SBAR card with inconsistencies out.

```json
Request:
{
  "transcript": "...",
  "patient_id": "synth-001"
}

Response 200:
{
  "card_id": "card-abc123",
  "sbar": { ... SBARStructure ... },
  "inconsistencies": [
    {
      "type": "VITAL_TREND",
      "severity": "WARN",
      "message": "Du sagst 'fieberfrei seit 12h', letzte gemessene Temperatur war 38.4°C vor 4h",
      "evidence": {
        "claim": "fieberfrei seit 12h",
        "actual": {"temperature": 38.4, "timestamp": "2025-04-25T08:30:00"}
      }
    }
  ],
  "completeness": {
    "score": 0.87,
    "missing_items": ["allergies_not_mentioned"],
    "details": {...}
  }
}
```

### `POST /api/handover-cards/{card_id}/confirm-missing`
Physician explicitly confirms that something missing was intentional
(e.g. "no known allergies" rather than forgotten).

```json
Request:
{
  "item": "allergies",
  "value": "explicitly_none" | "addressed_separately" | "not_applicable"
}

Response 200:
{ "completeness": { "score": 1.0, ... } }
```

### `POST /api/handover-cards/{card_id}/sign`
Complete the handover, create the audit log entry.

```json
Request:
{ "signed_by": "Dr. Müller" }

Response 200:
{
  "card_id": "card-abc123",
  "signed_at": "2025-04-25T14:32:11Z",
  "audit_hash": "sha256-..."
}
```

## Inconsistency pattern definitions

Strategy pattern: each detector is a separate class implementing
`detect(card, patient) -> list[Inconsistency]`. This keeps the
allergy-collision detector (stretch) cleanly removable.

### MVP pattern 1: VITAL_TREND

Triggers when the physician mentions a vital status in the transcript
(`fieberfrei`, `stabil`, `kein Fieber`, `Sättigung gut`), but the most
recent recorded vital readings contradict that.

```python
class VitalTrendDetector:
    """
    Looks for VitalMentions in the SBAR output. Compares the qualifier
    (stable/improving) against the actual most-recent measurements
    from patient.recent_vitals.
    """
    THRESHOLDS = {
        "temperature": {"fever_above": 37.8},
        "oxygen_saturation": {"low_below": 92},
        "heart_rate": {"tachy_above": 100, "brady_below": 50},
    }

    def detect(self, card: HandoverCard, patient: Patient) -> list[Inconsistency]:
        # for each VitalMention in SBAR
        # find the latest matching reading in patient.recent_vitals
        # compare qualifier to threshold
        # if conflict: Inconsistency(type=VITAL_TREND, severity=WARN, ...)
        ...
```

### MVP pattern 2: MED_STATE

Triggers when the physician says "medication X stopped / paused /
started", but `patient.medications` shows a different status.

```python
class MedicationStateDetector:
    """
    Looks for medication actions in the SBAR (recommendation +
    assessment). Compares against current patient.medications.status.
    """
    STATE_VERBS = {
        "absetzen": "discontinued",
        "pausieren": "paused",
        "starten": "active",
        "hochdosieren": "active",
        "weiter": "active",
    }

    def detect(self, card, patient) -> list[Inconsistency]:
        # verb-pattern match on medication + action
        # if the action implies a state change the DB does not reflect
        ...
```

### Stretch pattern 3: ALLERGY_COLLISION

Triggers when a medication mentioned in the SBAR contains an active
ingredient against which the patient has a documented allergy.

```python
class AllergyCollisionDetector:
    """
    STRETCH GOAL — only build this if Day 2 morning still has time.
    Needs a small active-ingredient database (~50 entries is enough
    for the demo, e.g. penicillin class, NSAIDs, opioids).
    """
    # Hardcoded for the demo:
    ACTIVE_INGREDIENTS = {
        "amoxicillin": ["penicillin"],
        "ampicillin": ["penicillin"],
        "ibuprofen": ["nsaid"],
        "diclofenac": ["nsaid"],
        # ~50 more
    }

    def detect(self, card, patient) -> list[Inconsistency]:
        # for each medication mentioned in SBAR
        # look up the active-ingredient class
        # compare to patient.allergies
        # if match: severity=CRITICAL
        ...
```

**Important:** the detector manager loads all detector classes from a
list. If `AllergyCollisionDetector` is not implemented, that entry is
just missing — the rest still runs. No try/except spaghetti.

## Completeness scoring

Score = (1 - missing_critical * 0.4 - missing_optional * 0.05)

```python
EXPECTED_FIELDS = {
    "critical": [
        "allergies_mentioned_or_explicitly_none",
        "main_problem_in_situation",
        "at_least_one_action_in_recommendation",
    ],
    "optional": [
        "vital_mention_count >= 1",
        "current_medications_mentioned",
        "pending_diagnostics_mentioned_if_any_open",
    ],
}
```

## Synthetic patient profiles

Three patients are enough for the demo. Each is designed to trigger
a different inconsistency.

### Patient 1: synth-001 — Frau Schmidt, bed 1

**Profile:** 67 y/o female, pneumonia, day 3 of antibiotic therapy.

**Designed for:** VITAL_TREND inconsistency. Last recorded temperature
was 38.4°C 4h ago. If demo physician says "fever-free", the warning
triggers.

**Allergies:** none known (documented in chart field).

### Patient 2: synth-002 — Herr Weber, bed 2

**Profile:** 54 y/o male, post-op cholecystectomy day 1, stable.

**Designed for:** MED_STATE inconsistency. Patient currently receiving
metamizol as analgesic. If demo physician says "analgesic discontinued",
but the chart shows the metamizol order as active, it triggers.

**Allergies:** none known.

### Patient 3: synth-003 — Frau Kowalski, bed 3

**Profile:** 78 y/o female, acute cardiac decompensation, freshly
transferred from ED.

**Designed for:** ALLERGY_COLLISION inconsistency (stretch). Patient
has a documented penicillin allergy. If demo physician says "antibiotic
therapy started with amoxicillin" (note: a real physician would never
do this — but the demo shows the system would catch it), the
critical warning triggers.

**Bonus for completeness demo:** if the demo physician omits allergies,
the score drops sharply, because allergies are critical for this
patient.

## Synthesis-data generation

File `backend/data/synthetic/seed.py` deterministically generates the
three JSON profiles (same seed → same data, for demo reproducibility).
Output: `backend/data/synthetic/patient_001.json`,
`patient_002.json`, `patient_003.json`.

Vital readings are generated for the last 24h, every 30 minutes, with
realistic drift. For patient 1: deliberately bake in a temperature
spike 4h ago so the VITAL_TREND detector can fire.

## FHIR sandbox integration (primary path)

Plan: at app startup, the three JSON mocks are POSTed to the HAPI FHIR
sandbox (as a FHIR Bundle, transaction). The app then fetches patient
data via FHIR calls instead of from the local JSONs. JSONs are the
fallback if the FHIR sandbox is unreachable.

```python
# backend/services/patient_source.py
class PatientSource:
    def __init__(self, prefer_fhir=True):
        self.prefer_fhir = prefer_fhir
        self._fhir_available = self._check_fhir()

    def get_patient(self, patient_id) -> Patient:
        if self.prefer_fhir and self._fhir_available:
            return self._fetch_from_fhir(patient_id)
        return self._load_from_json(patient_id)
```

Pitch wow-factor relevant: **"works against any FHIR-compliant
hospital system; demoed here against the public HAPI sandbox"**.

## Aikido setup steps

Day 1 morning (before any code):
1. https://app.aikido.dev → create account (free)
2. Connect Source Code → GitHub → select `<your-repo>`
3. Wait for initial scan (~3-5 min)
4. Browser screenshot of the report → save as
   `docs/aikido-baseline.png`
5. Review issues — if there are critical false positives, mark them as
   "false positive" in the Aikido dashboard

Day 2 evening (before submission):
6. Push the latest commit
7. Wait for the final scan
8. Browser screenshot → `docs/aikido-final.png`
9. In submission state: "Aikido baseline: X issues, final: Y issues"
   (ideally Y < X, because the demo-tester subagent reported issues
   you fixed)

## Pioneer/Fastino fine-tune plan

Detail in `docs/finetune.md` (created Day 2 morning). Short version:

- 50 synthetic handover transcripts with SBAR ground truth
  generated via Claude/GPT-4o (Day 1 stretch or Day 2 morning)
- Train LoRA adapter (10 epochs, batch_size 4, ~30-45 min on CPU)
- Eval against GPT-4o baseline on 10 test examples:
  metrics: F1 (SBAR fields), latency, cost per call
- Production switch via env variable `USE_FINETUNED=true|false`
- Frontend: toggle for live demo comparison

## Out of scope (stretch goals, Day 2 if time permits)

In this priority order, if time is left over:

1. ALLERGY_COLLISION detector + active-ingredient database (~30 min)
2. Pioneer fine-tune + eval comparison UI (~3h, scheduled Day 2)
3. FHIR Bundle export of the signed handover (~45 min)
4. Multiple patients in one session as a connected workflow (~2h)
5. Entire approval layer with audit-log hash chain (~1.5h, scheduled Day 2)

Things we explicitly do NOT build, even with time to spare, because
they distract from the demo path: login, multi-user, multiple wards,
real-time sync, persistent DB migrations, mobile-native app,
performance tuning under 100ms, tests beyond the happy path.
