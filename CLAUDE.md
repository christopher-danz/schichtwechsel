# Schichtwechsel — Project Context

> **This file is auto-loaded into every Claude Code session.**
> It is the single source of truth for what the product is, what it is
> not, and which architectural decisions are locked in. If something here
> is unclear: stop and ask, never assume.

## What Schichtwechsel is

A voice-first shift-handover assistant for German hospital wards. The
outgoing physician speaks freely for 60-90 seconds about each patient.
The system structures the spoken text in real time into an SBAR card,
cross-references it against the current patient record, flags
inconsistencies, and hands off a complete, signed handover card to
the next shift.

Target users: ward physicians during shift change in German acute-care
hospitals. Use context: tablet at the ward station or smartphone in
hand, 30-60 seconds per patient, 8-12 patients per handover.

## What Schichtwechsel is NOT

This list matters as much as the one above. If we catch ourselves
building toward any of these, we stop.

- **Not a HIS replacement.** We integrate with existing systems via
  FHIR; we do not replace ORBIS or comparable systems.
- **No multi-user system for days 1-2.** Single demo user, hardcoded
  as "Dr. Müller". No authentication, no permission model.
- **No real clinical integration.** Patients are synthetic (JSON mocks
  plus optional HAPI FHIR sandbox), never real PHI.
- **No nursing documentation.** We build physician handover, not
  nursing documentation. This boundary must be communicated clearly.
- **No medical decision-making.** Inconsistency warnings are decision-
  support; the system does not replace clinical judgment.
- **No real-time collaboration.** If two physicians open the same
  session simultaneously, that is undefined behavior — we do not
  address it.

## Data model (the heart of the system)

Six core entities. Everything else is derived.

```
Patient
  ├─ patient_id, bed, demographics
  ├─ allergies: list[Allergy]
  ├─ medications: list[Medication]
  ├─ recent_vitals: list[VitalReading]   (last 24h)
  └─ open_diagnostics: list[OpenDiagnostic]

HandoverSession
  ├─ session_id, started_by="Dr. Müller", started_at
  ├─ patients: list[Patient]              (the patients to hand over)
  └─ cards: list[HandoverCard]

HandoverCard            ← the central output entity
  ├─ card_id, patient_id, recorded_at
  ├─ raw_transcript: str                 (what the physician said)
  ├─ sbar: SBARStructure
  ├─ inconsistencies: list[Inconsistency]
  ├─ completeness: CompletenessScore
  └─ signed: bool, signed_at, signed_by

SBARStructure
  ├─ situation: str                       (1-2 sentences)
  ├─ background: BackgroundFields
  ├─ assessment: AssessmentFields
  └─ recommendation: list[ActionItem]

Inconsistency
  ├─ type: enum {VITAL_TREND, MED_STATE, ALLERGY_COLLISION}
  ├─ severity: enum {INFO, WARN, CRITICAL}
  ├─ message: str                         (German, physician-readable)
  └─ evidence: dict                        (which fields collide)

CompletenessScore
  ├─ score: float (0..1)
  ├─ missing_items: list[str]             (e.g. "allergies_not_mentioned")
  └─ details: dict
```

**SBAR is the structuring schema.** A new developer should be able to
look at this model and immediately understand what is happening. All UI
components and API endpoints derive from this.

## Stack constraints (locked, not negotiable)

These sponsor tools have a fixed place. The build plan does not work
without them, because they are required for side-challenge entries:

- **Pioneer/Fastino GLiNER2** — does the SBAR structuring (transcript
  → SBAR). In the critical path. Day 2 additionally: LoRA fine-tune
  on 50 synthetically generated handover examples, eval against GPT-4o.
- **Gradium** — voice-to-text. Primary path. If the API fails, fall
  back to local Whisper (offline-capable); last fallback is browser
  Web Speech API.
- **Aikido** — connect repo, run security scans, capture before/after
  screenshots as submission evidence.
- **Entire** — approval workflow at the end of a handover (human
  reviews AI structuring, signs digitally). Sponsor hit.

Other stack decisions that are locked in:

- Backend: Python 3.12, FastAPI, uv for dependencies, pydantic v2 for models
- Frontend: React + Vite + TypeScript + Tailwind, tablet-first layout
  (default viewport 1024×768)
- DB: SQLite with JSON storage. Postgres is overkill for 48h.
- Patient data: three JSON mocks under `backend/data/synthetic/`.
  Optional HAPI FHIR sandbox as a second path for pitch wow factor.
- Deploy: `docker compose up` must boot everything. No external services
  beyond sponsor APIs (Gradium, optional Pioneer).

## Demo path (what we build toward)

The entire architecture serves this single 90-second sequence. Details
in `docs/demo.md`. Short version:

1. Physician opens Schichtwechsel on tablet, sees a list of 3 patients
2. Selects bed 1 (Frau Schmidt, 67, pneumonia)
3. Presses record, speaks for 75 seconds about status
4. Sees live transcript while speaking
5. After stop: 3-5 seconds, SBAR card appears
6. One inconsistency warning in yellow (e.g. "You said 'fever-free',
   last recorded temperature was 38.4°C 4h ago")
7. Completeness score shows 87% — allergies were not mentioned
8. Physician clicks "Confirm allergies → none known", score jumps
   to 100%
9. Physician clicks "Complete handover" — digital signature, audit log

This path is sacred. Features that support this path are priority.
Features that endanger this path get cut.

## Code conventions (project-specific)

In addition to my global standing orders:

- All UI text is German. Code comments and variable names are English.
- SBAR fields keep their German labels in the UI (Situation, Hintergrund,
  Beurteilung, Empfehlung) but are English in code.
- Types are explicit: pydantic-v2 for every backend model, TypeScript
  interfaces for every frontend model. No `any`, no `dict[str, Any]`.
- Endpoints use plural resources: `/patients`, `/handover-sessions`,
  `/handover-cards`. An action is a sub-path: `/handover-cards/{id}/sign`.
- Inconsistency detection is built as a strategy pattern: each pattern
  type is its own class implementing `detect(card, patient) ->
  list[Inconsistency]`. This makes stretch goals (allergy collision)
  cleanly removable.

## When uncertain: ask, do not assume

If something comes up during the build that is not unambiguously
specified in this file or in `docs/spec.md`, stop and ask me directly
in chat. Examples where this rule applies:

- New fields on a model
- New endpoint routes
- Switching state-management strategy in the frontend
- Switching sponsor tools (e.g. away from Gradium)
- Architectural decisions affecting multiple files

Do not ask about small implementation details (variable names, helper
functions, error message wording) — that is a brake.

## Related documents

- `docs/spec.md` — detailed spec with SBAR schema, API contracts,
  inconsistency-pattern definitions, synthetic patient profiles
- `docs/demo.md` — the exact 90-second pitch script as the
  architectural anchor
