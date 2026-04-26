"""
Generate synthetic GLiNER2 training data via Claude API.

Produces 50 train + 10 eval JSONL examples of German ward handover
transcripts with labeled SBAR entities and structures.

Usage:
    cd backend/
    ANTHROPIC_API_KEY=... uv run scripts/generate_training_data.py
    # or with existing venv:
    .venv/bin/python scripts/generate_training_data.py
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
from pathlib import Path

import anthropic

# ---------------------------------------------------------------------------
# Patient template profiles — varied enough to produce diverse transcripts
# ---------------------------------------------------------------------------

PATIENT_PROFILES = [
    {
        "id": "pneumonia",
        "diagnose": "Community-acquired Pneumonie",
        "alter_range": (65, 82),
        "geschlecht": ["weiblich", "weiblich", "männlich"],
        "med_context": "Amoxicillin-Clavulansäure i.v., Paracetamol bei Bedarf",
        "pending": "Blutkultur, Röntgen-Thorax-Verlauf",
        "severity_hint": "watch",
    },
    {
        "id": "cardiac_decompensation",
        "diagnose": "Dekompensierte Herzinsuffizienz (EF 30%)",
        "alter_range": (68, 80),
        "geschlecht": ["männlich", "männlich", "weiblich"],
        "med_context": "Furosemid 40mg i.v., Ramipril, Metoprolol",
        "pending": "Echo, BNP-Verlauf",
        "severity_hint": "watch",
    },
    {
        "id": "postop_cabg",
        "diagnose": "Z.n. CABG (koronare Bypass-OP), Tag 3 post-op",
        "alter_range": (58, 70),
        "geschlecht": ["männlich", "männlich", "weiblich"],
        "med_context": "ASS 100mg, Bisoprolol, Pantoprazol, Enoxaparin",
        "pending": "Wundkontrolle, EKG",
        "severity_hint": "routine",
    },
    {
        "id": "diabetes_entgleisung",
        "diagnose": "Hyperglykämische Entgleisung bei DM Typ 2",
        "alter_range": (52, 72),
        "geschlecht": ["weiblich", "männlich", "weiblich"],
        "med_context": "Altinsulin-Perfusor, Kaliumsubstitution, NaCl-Infusion",
        "pending": "BZ-Profil, HbA1c",
        "severity_hint": "watch",
    },
    {
        "id": "stroke",
        "diagnose": "Ischämischer Apoplex links-hemisphärisch",
        "alter_range": (70, 82),
        "geschlecht": ["männlich", "weiblich", "männlich"],
        "med_context": "ASS 100mg, Pantoprazol, Heparin-Pumpe",
        "pending": "MRT-Verlauf, Schluckdiagnostik",
        "severity_hint": "urgent",
    },
    {
        "id": "urosepsis",
        "diagnose": "Urosepsis bei E.-coli-Harnwegsinfekt",
        "alter_range": (42, 65),
        "geschlecht": ["weiblich", "weiblich", "männlich"],
        "med_context": "Piperacillin-Tazobactam 4.5g alle 8h, Noradrenalin-Perfusor",
        "pending": "Antibiogramm, Urin-Kultur",
        "severity_hint": "urgent",
    },
    {
        "id": "gi_bleeding",
        "diagnose": "Obere GI-Blutung bei Ösophagusvarizenblutung",
        "alter_range": (55, 72),
        "geschlecht": ["männlich", "männlich", "weiblich"],
        "med_context": "Terlipressin, Pantoprazol-Dauerinfusion, EK-Transfusion",
        "pending": "Hb-Kontrolle, Ösophagoskopie-Befund",
        "severity_hint": "urgent",
    },
    {
        "id": "meningitis",
        "diagnose": "Bakterielle Meningitis (Pneumokokken-Verdacht)",
        "alter_range": (22, 45),
        "geschlecht": ["männlich", "weiblich", "männlich"],
        "med_context": "Ceftriaxon 2g alle 12h, Dexamethason, Aciclovir empirisch",
        "pending": "LP-Ergebnis ausstehend, BK x2",
        "severity_hint": "urgent",
    },
]

NAMEN_WEIBLICH = [
    "Müller", "Schmidt", "Fischer", "Weber", "Klein", "Schneider",
    "Hoffmann", "Bauer", "Koch", "Richter", "Wagner", "Wolf",
]
NAMEN_MAENNLICH = [
    "Maier", "Schäfer", "Braun", "Zimmermann", "Hartmann", "Krüger",
    "Lange", "Schwarz", "Weiß", "Köhler", "Krause", "Lorenz",
]

SYSTEM_PROMPT = """\
Du bist ein erfahrener Stationsarzt auf einer deutschen Internisten-Station
(Innere Medizin) und übergibst Patienten mündlich an die nächste Schicht.

Deine Aufgabe: Generiere einen realistischen mündlichen Übergabe-Text und die
dazu passenden strukturierten SBAR-Annotationen im angegebenen JSON-Format.

Regeln für den Übergabe-Text:
- Deutsch, typische Stationssprache (Abkürzungen wie "Z.n.", "HF", "RR", "SpO2")
- 100–170 Wörter
- Natürlicher Sprachfluss, wie beim echten Übergabegespräch gesprochen
- Enthält typische medizinische Informationen: Vitalwerte, Medis, offene Befunde,
  Handlungsempfehlungen
- Manchmal Allergien erwähnen, manchmal nicht
- Manchmal kleine Widersprüche einbauen (z.B. "fieberfrei" obwohl Temp 38.5)

Antworte NUR mit einem JSON-Objekt, kein Markdown, keine Erklärungen.
"""

USER_TEMPLATE = """\
Patient: {geschlecht}, {alter} Jahre, Name: {nachname}, Bett {bett}
Diagnose: {diagnose}
Aktuelle Medikamente: {med_context}
Ausstehende Diagnostik: {pending}
Gewünschte Schwere (severity): {severity_hint}

Erstelle das JSON genau in diesem Format:
{{
  "transcript": "<mündlicher Übergabe-Text auf Deutsch, 100-170 Wörter>",
  "entities": {{
    "main_problem": ["<exakter Textspan aus transcript>"],
    "vital_sign": ["<span1>", "<span2>"],
    "medication": ["<span1>", "<span2>"],
    "action_item": ["<span1>"],
    "pending_test": ["<span1>"],
    "allergy": [],
    "admission_reason": ["<span>"],
    "relevant_history": ["<span>"],
    "complication": []
  }},
  "severity": "{severity_hint}",
  "sbar": {{
    "situation": "<1-2 Sätze aktueller Zustand>",
    "admission_reason": "<Aufnahmegrund>",
    "current_status": "<Gesamtbeurteilung heute>",
    "key_actions": ["<Maßnahme 1>", "<Maßnahme 2>"],
    "allergies_explicitly_none": "yes|no|not_mentioned"
  }}
}}

Wichtig: Alle Werte in "entities" müssen exakte Substrings aus "transcript" sein.
"""


def generate_one(client: anthropic.Anthropic, profile: dict, seed: int) -> dict | None:
    rng = random.Random(seed)
    alter = rng.randint(*profile["alter_range"])
    geschlecht = rng.choice(profile["geschlecht"])
    nachname = rng.choice(NAMEN_WEIBLICH if geschlecht == "weiblich" else NAMEN_MAENNLICH)
    bett = rng.randint(1, 24)

    user_msg = USER_TEMPLATE.format(
        geschlecht=geschlecht,
        alter=alter,
        nachname=nachname,
        bett=bett,
        diagnose=profile["diagnose"],
        med_context=profile["med_context"],
        pending=profile["pending"],
        severity_hint=profile["severity_hint"],
    )

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1200,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = response.content[0].text.strip()
        data = json.loads(raw)
    except (json.JSONDecodeError, IndexError, anthropic.APIError) as exc:
        print(f"  [warn] seed={seed} failed: {exc}", file=sys.stderr)
        return None

    # Convert to GLiNER2 InputExample format
    transcript: str = data.get("transcript", "")
    entities: dict = data.get("entities", {})
    sbar: dict = data.get("sbar", {})
    severity: str = data.get("severity", "routine")

    # Filter entity lists to non-empty, actual substrings
    filtered_entities: dict[str, list[str]] = {}
    for etype, spans in entities.items():
        valid = [s for s in spans if isinstance(s, str) and s and s in transcript]
        if valid:
            filtered_entities[etype] = valid

    record = {
        "input": transcript,
        "output": {
            "entities": filtered_entities,
            "classifications": [
                {
                    "task": "overall_severity",
                    "labels": ["routine", "watch", "urgent"],
                    "true_label": [severity if severity in ("routine", "watch", "urgent") else "watch"],
                }
            ],
            "json_structures": [
                {
                    "sbar_card": {
                        "situation": sbar.get("situation", ""),
                        "admission_reason": sbar.get("admission_reason", ""),
                        "current_status": sbar.get("current_status", ""),
                        "key_actions": sbar.get("key_actions", []),
                        "allergies_explicitly_none": sbar.get(
                            "allergies_explicitly_none", "not_mentioned"
                        ),
                    }
                }
            ],
        },
    }
    return record


def main() -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("Error: ANTHROPIC_API_KEY not set.")

    client = anthropic.Anthropic(api_key=api_key)

    out_dir = Path(__file__).parent.parent / "data" / "training"
    out_dir.mkdir(parents=True, exist_ok=True)
    train_path = out_dir / "train.jsonl"
    eval_path = out_dir / "eval.jsonl"

    total_train = 50
    total_eval = 10
    total = total_train + total_eval

    # Distribute evenly across profiles
    profiles_expanded: list[dict] = []
    per_profile = total // len(PATIENT_PROFILES)
    for p in PATIENT_PROFILES:
        profiles_expanded.extend([p] * per_profile)
    # Fill remainder
    while len(profiles_expanded) < total:
        profiles_expanded.append(random.choice(PATIENT_PROFILES))
    random.shuffle(profiles_expanded)

    print(f"Generating {total} examples ({total_train} train + {total_eval} eval)...")
    train_records: list[dict] = []
    eval_records: list[dict] = []

    for i, profile in enumerate(profiles_expanded):
        split = "train" if i < total_train else "eval"
        print(f"  [{i+1}/{total}] {split} — {profile['id']} (seed={i})", end=" ", flush=True)
        record = generate_one(client, profile, seed=i)
        if record:
            if split == "train":
                train_records.append(record)
            else:
                eval_records.append(record)
            print("OK")
        else:
            print("SKIP")
        # Respect rate limits
        if i > 0 and i % 10 == 0:
            time.sleep(1)

    with open(train_path, "w", encoding="utf-8") as f:
        for r in train_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(eval_path, "w", encoding="utf-8") as f:
        for r in eval_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\nSaved {len(train_records)} train → {train_path}")
    print(f"Saved {len(eval_records)} eval  → {eval_path}")


if __name__ == "__main__":
    main()
