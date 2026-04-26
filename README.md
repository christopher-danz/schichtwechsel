# Schichtwechsel — AI-Powered Shift Handover for German Hospital Wards

Schichtwechsel ("shift change") is a voice-first shift handover assistant for German acute-care hospital wards. An outgoing physician speaks freely for 60–90 seconds about each patient. The system transcribes the speech in real time, structures it into a standardised SBAR card using a fine-tuned on-device NLP model, cross-references the spoken information against the patient record, flags inconsistencies, and produces a digitally signed handover card for the incoming shift.

**Built at:** AI Healthhack 2025 (48-hour hackathon)  
**Author:** Christopher Danz — AI & Data Manager, DRK Clinics Berlin

---

## Table of Contents

- [Demo](#demo)
- [Sponsor Tools](#sponsor-tools)
- [Architecture](#architecture)
- [Data Model](#data-model)
- [API Reference](#api-reference)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Fine-tuning Pipeline](#fine-tuning-pipeline)
- [Project Structure](#project-structure)

---

## Demo

The system is built around one concrete 90-second sequence:

1. Physician opens Schichtwechsel on a tablet, sees three patients with their bed, name, and diagnosis
2. Selects Bed 1 — Frau Schmidt, 67, pneumonia — and presses record
3. Speaks for ~30 seconds in natural German ward language ("fieberfrei seit gestern, Sättigung stabil…")
4. After stopping: live transcript was visible during recording; SBAR card appears in 3–5 seconds
5. One yellow inconsistency warning: *"Sie sagten 'fieberfrei' — letzte gemessene Temperatur war 38.4 °C vor 4h"*
6. Completeness score shows **87%** — allergies were not mentioned
7. Physician clicks "Keine bekannten Allergien bestätigen" → score jumps to **100%**
8. Physician clicks "Übergabe abschließen" → digital signature with SHA-256 audit hash

---

## Sponsor Tools

### Pioneer / Fastino — GLiNER2 (`gliner2-base-v1`)

**Role:** Core SBAR structuring model. Converts raw German transcript → named entities + classified fields + structured SBAR output in a single extraction call.

**Integration:** `gliner2` Python package, `GLiNER2API` class (cloud inference via Pioneer API).

**What it extracts:**

| Entity type | Description |
|---|---|
| `patient_identifier` | Name, bed, age, sex |
| `main_problem` | Primary diagnosis or current problem |
| `admission_reason` | Reason for admission |
| `relevant_history` | Comorbidities, prior conditions |
| `medication` | Drug name, dose, or medication action |
| `allergy` | Any allergy or intolerance mentioned |
| `vital_sign` | Vital parameter value or trend |
| `complication` | Complications or deteriorations |
| `pending_test` | Pending lab, imaging, or diagnostics |
| `action_item` | Concrete tasks for the next shift |
| `family_communication` | Family, visitor, or communication notes |

**Structured output — `sbar_card`:**

| Field | Type | Description |
|---|---|---|
| `situation` | string | 1–2 sentences on current patient state |
| `admission_reason` | string | Why admitted |
| `admission_date` | string | Date of admission if mentioned |
| `allergies_explicitly_none` | `yes` / `no` / `not_mentioned` | Whether physician explicitly cleared allergies |
| `current_status` | string | Overall clinical assessment |
| `key_actions` | list[string] | Actions ordered for the next shift |

**Classification:** `overall_severity` → `routine` / `watch` / `urgent`

**LoRA fine-tuning:** A `gliner2-base-v1` adapter was trained on 50 synthetic German ward handover examples (generated via Claude API — see [Fine-tuning Pipeline](#fine-tuning-pipeline)). The `USE_FINETUNED=true` environment variable switches the service to load this adapter for local on-device inference.

**Schema definition:** [`backend/app/schemas/sbar.py`](backend/app/schemas/sbar.py)  
**Service:** [`backend/app/services/gliner_service.py`](backend/app/services/gliner_service.py)

---

### Gradium — Speech-to-Text

**Role:** Primary transcription of recorded ward handover audio. Converts browser-recorded `audio/webm;codecs=opus` to German text.

**Integration:** `gradium` Python package, `GradiumClient` + `STTSetup(model_name="default", input_format="wav")`.

**Fallback:** If `GRADIUM_API_KEY` is not set or the call fails, the system automatically falls back to a locally bundled `faster-whisper` `tiny` model (CPU, `int8` quantised, baked into the Docker image at build time — no runtime download).

**Service:** [`backend/app/services/transcription.py`](backend/app/services/transcription.py)

---

### Entire — Approval Workflow

**Role:** Human-in-the-loop approval layer. After the physician signs a handover card, the signature is sent to Entire's approval API for a second-shift review before the audit hash is finalised.

**Integration:** Endpoint `POST /api/handover-cards/{card_id}/sign` → Entire approval round-trip.

**Route:** [`backend/app/api/routes/handover_cards.py`](backend/app/api/routes/handover_cards.py)

---

### Aikido — Security Scanning

The repository is connected to Aikido for automated security scanning. Before/after screenshots of the Aikido dashboard are stored in [`docs/aikido-evidence/`](docs/aikido-evidence/).

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Browser (tablet, 1024×768)                                      │
│  React 18 + Vite + TypeScript + Tailwind CSS                     │
│                                                                  │
│  PatientSidebar ─ 3 patients, status dots (pending/in-progress/  │
│                   signed), progress bar                          │
│  PatientDetail  ─ vitals, meds, allergies, open diagnostics      │
│  RecordingSection ─ MediaRecorder + Web Speech API live captions │
│  SBARCard       ─ inconsistency banners, completeness bar,       │
│                   allergy confirm, digital sign                  │
└────────────────────────────┬─────────────────────────────────────┘
                             │  /api/*  (Vite proxy → :8000)
┌────────────────────────────▼─────────────────────────────────────┐
│  FastAPI 0.111  (Python 3.12, uvicorn)                           │
│                                                                  │
│  POST /api/transcribe    ──► GradiumClient.stt()                 │
│                               └─ fallback: faster-whisper tiny   │
│  POST /api/structure     ──► GLiNER2API.extract()                │
│                               └─ fallback: heuristic rule-based  │
│                           + VitalTrendDetector                   │
│                           + MedicationStateDetector              │
│                           + CompletenessScorer                   │
│  POST /api/handover-cards/{id}/confirm-missing                   │
│  POST /api/handover-cards/{id}/sign  ──► Entire approval         │
│                                                                  │
│  In-memory CardStore (SQLite planned for production)             │
│  PatientSource  ──► 3 synthetic JSON patient records             │
└──────────────────────────────────────────────────────────────────┘
```

**Inconsistency detection** uses a strategy pattern — each detector is a class implementing `detect(card, patient) -> list[Inconsistency]`:

- `VitalTrendDetector` — detects contradictions between verbal claims ("fieberfrei") and recorded vitals (temperature > 38.0 °C)
- `MedicationStateDetector` — detects "abgesetzt"/"pausiert" claims conflicting with active medication list

**Completeness scoring** uses a proportional formula:

```
score = 1.0 − (missing_critical / 3) × 0.40 − (missing_optional / 3) × 0.15
```

Critical items: vital signs mentioned, situation present, recommendation present.  
Optional items: medications addressed, allergies addressed, pending diagnostics addressed.

Missing items are also detected via transcript-level token scanning (first token of medication/diagnostic names), so a transcript saying "Amoxiclav läuft weiter" satisfies `medications_mentioned` even if GLiNER2 did not extract a structured entity.

---

## Data Model

```
Patient
  ├─ patient_id, bed, demographics (name, age, sex)
  ├─ main_diagnosis
  ├─ allergies: list[Allergy]          (substance, reaction, severity)
  ├─ medications: list[Medication]     (name, dose, frequency, status)
  ├─ recent_vitals: list[VitalReading] (parameter, value, unit, recorded_at)
  └─ open_diagnostics: list[OpenDiagnostic]

HandoverCard                           ← central output entity
  ├─ card_id, patient_id, recorded_at
  ├─ raw_transcript: str
  ├─ sbar: SBARStructure
  ├─ inconsistencies: list[Inconsistency]
  ├─ completeness: CompletenessScore
  └─ signed: bool, signed_at, signed_by, audit_hash

SBARStructure
  ├─ situation: str
  ├─ background: BackgroundFields
  │    ├─ admission_reason, admission_date
  │    ├─ relevant_history: list[str]
  │    ├─ current_medications: list[str]
  │    ├─ allergies_mentioned: list[str]
  │    └─ allergies_explicitly_none: bool
  ├─ assessment: AssessmentFields
  │    ├─ current_status: str
  │    ├─ vital_mentions: list[VitalMention]
  │    ├─ complications: list[str]
  │    └─ pending_diagnostics: list[str]
  └─ recommendation: list[ActionItem]   (action, priority, timing)

Inconsistency
  ├─ type: VITAL_TREND | MED_STATE | ALLERGY_COLLISION
  ├─ severity: INFO | WARN | CRITICAL
  ├─ message: str                       (German, physician-readable)
  └─ evidence: dict                     (which fields collide)

CompletenessScore
  ├─ score: float (0..1)
  ├─ missing_items: list[str]
  └─ details: dict[str, bool]
```

Patient data is synthetic — three JSON mocks under `backend/data/synthetic/`. No real PHI is used anywhere.

---

## API Reference

All endpoints are prefixed `/api`. Interactive docs at `http://localhost:8000/docs`.

### `GET /api/health`
Returns service liveness.
```json
{ "status": "ok", "service": "ShiftChange-Bot", "version": "0.1.0" }
```

### `GET /api/patients`
Returns list of all patients (summary view).
```json
[
  {
    "patient_id": "patient_001",
    "bed": "1",
    "demographics": { "name": "Frau Schmidt", "age": 67, "sex": "F" },
    "main_diagnosis": "Community-acquired Pneumonie"
  }
]
```

### `GET /api/patients/{patient_id}`
Returns full patient detail including vitals, medications, allergies, and open diagnostics.

### `POST /api/transcribe`
Accepts multipart form upload of audio file. Tries Gradium STT first; falls back to local Whisper.

**Request:** `multipart/form-data` — field `audio` (any audio MIME type; browser typically sends `audio/webm;codecs=opus`)

**Response:**
```json
{ "transcript": "Frau Schmidt, Bett 1, 67 Jahre..." }
```

### `POST /api/structure`
Structures a transcript into a full SBAR card with inconsistency detection and completeness scoring. Saves the card to the in-memory store.

**Request:**
```json
{ "transcript": "...", "patient_id": "patient_001" }
```

**Response:**
```json
{
  "card_id": "c1a2b3...",
  "sbar": { "situation": "...", "background": {...}, "assessment": {...}, "recommendation": [...] },
  "inconsistencies": [
    {
      "type": "VITAL_TREND",
      "severity": "WARN",
      "message": "Sie sagten 'fieberfrei', letzte gemessene Temperatur war 38.4°C vor 4h",
      "evidence": { "claim": "fieberfrei", "actual": { "temperature": 38.4 } }
    }
  ],
  "completeness": { "score": 0.87, "missing_items": ["allergies_not_mentioned"], "details": {...} }
}
```

### `POST /api/handover-cards/{card_id}/confirm-missing`
Confirms a missing item, triggering a completeness recomputation.

**Request:**
```json
{ "item": "allergies", "value": "explicitly_none" }
```

**Response:**
```json
{ "card_id": "...", "completeness": { "score": 1.0, "missing_items": [], "details": {...} } }
```

### `POST /api/handover-cards/{card_id}/sign`
Digitally signs the handover card. Returns a SHA-256 audit hash.

**Request:**
```json
{ "signed_by": "Dr. Müller" }
```

**Response:**
```json
{
  "card_id": "...",
  "signed_at": "2025-04-26T10:00:00Z",
  "audit_hash": "sha256-73136b9a2ebf6..."
}
```

Returns `409 Conflict` if the card was already signed.

---

## Quick Start

**Prerequisites:** Docker, Docker Compose, API keys (see below).

```bash
git clone https://github.com/<your-org>/shiftchange-bot
cd shiftchange-bot

# 1. Configure API keys
cp .env.example .env
# Edit .env and fill in:
#   GRADIUM_API_KEY   — Gradium speech-to-text
#   PIONEER_API_KEY   — Fastino/Pioneer GLiNER2 API
#   ANTHROPIC_API_KEY — only needed for fine-tune data generation

# 2. Start the full stack
docker compose up

# 3. Open the app
open http://localhost:5173
```

The backend starts on `:8000`, the frontend dev server on `:5173` (with `/api` proxied to the backend). Both support hot reload.

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GRADIUM_API_KEY` | Yes (primary STT) | Gradium speech-to-text API key |
| `PIONEER_API_KEY` | Yes (primary NLP) | Pioneer/Fastino GLiNER2 API key |
| `ANTHROPIC_API_KEY` | Scripts only | Used by `generate_training_data.py` |
| `USE_FINETUNED` | No (default: `false`) | Set to `true` to use the LoRA fine-tuned adapter |

If `GRADIUM_API_KEY` is absent or the call fails, transcription falls back to the bundled `faster-whisper` tiny model automatically. If `PIONEER_API_KEY` is absent or the call fails, structuring falls back to a rule-based heuristic extractor — the demo path still works end-to-end without any API keys.

---

## Development Setup

```bash
# Backend (Python 3.12, uv)
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000

# Run tests
uv run pytest

# Frontend (Node 20+)
cd frontend
npm install
npm run dev      # starts Vite on :5173, proxies /api to :8000
npm run build    # production build
```

---

## Fine-tuning Pipeline

The LoRA fine-tuning pipeline for `gliner2-base-v1` operates in three steps, all run from the `backend/` directory:

### Step 1 — Generate synthetic training data

Uses Claude `claude-haiku-4-5-20251001` to generate 50 training + 10 evaluation German ward handover examples across 8 patient profiles (pneumonia, cardiac decompensation, post-CABG, diabetes, stroke, urosepsis, GI bleeding, meningitis). Each example includes exact entity spans, SBAR structure fields, and severity classification.

```bash
cd backend
ANTHROPIC_API_KEY=sk-ant-... .venv/bin/python scripts/generate_training_data.py
# Output: data/training/train.jsonl  (50 examples)
#         data/training/eval.jsonl   (10 examples)
```

### Step 2 — Fine-tune with LoRA

```bash
.venv/bin/python scripts/finetune.py
# Downloads fastino/gliner2-base-v1 (~250 MB, first run only)
# Trains 3 epochs, LoRA r=8, α=16, target modules: encoder
# Output: models/lora_handover/  (adapter weights, ~few MB)
```

Training configuration: `batch_size=2`, `gradient_accumulation_steps=4` (effective batch 8), `encoder_lr=1e-5`, `task_lr=5e-5`, CPU-compatible (no fp16).

### Step 3 — Evaluate base vs. fine-tuned

```bash
.venv/bin/python scripts/eval_compare.py
# Outputs: docs/eval-results.md  (entity recall, severity accuracy, SBAR fill rate)
```

### Step 4 — Activate in the app

```bash
# In .env:
USE_FINETUNED=true

docker compose up -d --build backend
```

When `USE_FINETUNED=true`, `GLiNERService` loads the base model and adapter locally at first request (lazy, cached), bypassing the Pioneer cloud API. This enables fully **on-device inference** — no patient data leaves the hospital network.

---

## Project Structure

```
shiftchange-bot/
├── .env.example                   API key template
├── docker-compose.yml             Full-stack container setup
│
├── backend/
│   ├── pyproject.toml             Python dependencies (uv)
│   ├── Dockerfile                 python:3.12-slim + ffmpeg + whisper model baked in
│   ├── app/
│   │   ├── main.py                FastAPI app, lifespan, router registration
│   │   ├── api/routes/
│   │   │   ├── health.py          GET /api/health
│   │   │   ├── patients.py        GET /api/patients, GET /api/patients/{id}
│   │   │   ├── transcribe.py      POST /api/transcribe
│   │   │   ├── structure.py       POST /api/structure
│   │   │   └── handover_cards.py  POST /api/handover-cards/{id}/confirm-missing
│   │   │                          POST /api/handover-cards/{id}/sign
│   │   ├── models/                Pydantic v2 domain models
│   │   │   ├── patient.py         Patient, Medication, VitalReading, Allergy
│   │   │   ├── sbar.py            SBARStructure, ActionItem, VitalMention
│   │   │   └── handover.py        HandoverCard, Inconsistency, CompletenessScore
│   │   ├── schemas/
│   │   │   └── sbar.py            GLiNER2 extraction schema (entity types + structure)
│   │   └── services/
│   │       ├── transcription.py   GradiumClient → faster-whisper fallback
│   │       ├── gliner_service.py  GLiNER2API → heuristic fallback; USE_FINETUNED path
│   │       ├── sbar_mapper.py     map_gliner_to_sbar(), heuristic_sbar()
│   │       ├── completeness.py    Proportional completeness scoring
│   │       ├── card_store.py      In-memory HandoverCard store
│   │       ├── patient_source.py  Loads synthetic patient JSON mocks
│   │       └── detectors/
│   │           ├── vital_trend.py     VITAL_TREND inconsistency detector
│   │           └── medication_state.py MED_STATE inconsistency detector
│   ├── data/
│   │   ├── synthetic/             patient_001.json, _002.json, _003.json
│   │   └── training/              train.jsonl, eval.jsonl (generated by script)
│   ├── models/
│   │   └── lora_handover/         LoRA adapter weights (after fine-tuning)
│   ├── scripts/
│   │   ├── generate_training_data.py  Claude API → GLiNER2 training JSONL
│   │   ├── finetune.py                GLiNER2Trainer + LoRAConfig
│   │   └── eval_compare.py            Base vs. fine-tuned evaluation
│   └── tests/
│       └── test_health.py
│
├── frontend/
│   ├── vite.config.ts             /api proxy → :8000
│   └── src/
│       ├── App.tsx                Main layout, state, patient selection, sign flow
│       ├── api/                   fetch wrappers (patients, transcribe, structure,
│       │                          handoverCards)
│       ├── components/
│       │   ├── PatientSidebar.tsx Fixed sidebar, status dots, progress bar
│       │   ├── PatientDetail.tsx  Vitals, meds, allergies, diagnostics
│       │   ├── RecordingSection.tsx MediaRecorder + Web Speech API live captions
│       │   └── SBARCard.tsx       Inconsistency banners, completeness bar,
│       │                          allergy confirm, digital sign
│       └── types/                 TypeScript interfaces mirroring backend models
│
└── docs/
    ├── spec.md                    Detailed technical specification
    ├── demo.md                    90-second pitch script and rehearsal checklist
    └── eval-results.md            GLiNER2 base vs. fine-tuned comparison table
```
