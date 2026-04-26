"""
Evaluate base GLiNER2 vs. fine-tuned LoRA adapter on the held-out eval set.

Run from backend/ directory:
    .venv/bin/python scripts/eval_compare.py

Outputs a markdown table to stdout and saves docs/eval-results.md.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).parent.parent.resolve()
os.environ.setdefault("HF_HOME", str(BASE_DIR / ".hf_cache"))

logging.basicConfig(
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    level=logging.WARNING,
)

# -------------------------------------------------------------------------
# Metrics helpers
# -------------------------------------------------------------------------

def _entity_recall(predicted: dict, gold: dict) -> float:
    """Fraction of gold entity spans found (case-insensitive substring match)."""
    total, found = 0, 0
    for etype, gold_spans in gold.items():
        pred_spans = predicted.get(etype, [])
        pred_lower = [s.lower() for s in pred_spans]
        for gspan in gold_spans:
            total += 1
            g = gspan.lower()
            # partial match: prediction contains gold span or vice versa
            if any(g in p or p in g for p in pred_lower):
                found += 1
    return found / total if total > 0 else 1.0


def _severity_correct(predicted: dict, gold_label: str) -> bool:
    sev = predicted.get("overall_severity", "")
    if isinstance(sev, list):
        sev = sev[0] if sev else ""
    return sev == gold_label


def _sbar_fill(predicted_sbar: dict) -> float:
    """Fraction of SBAR structure fields that are non-empty."""
    fields = ["situation", "admission_reason", "current_status", "key_actions"]
    filled = sum(1 for f in fields if predicted_sbar.get(f))
    return filled / len(fields)


# -------------------------------------------------------------------------
# Run extraction with either model variant
# -------------------------------------------------------------------------

def run_model(model, transcript: str) -> dict[str, Any]:
    """Extract SBAR using local GLiNER2 model."""
    sys.path.insert(0, str(BASE_DIR))
    from app.schemas.sbar import build_sbar_schema

    schema = build_sbar_schema(model)
    return model.extract(transcript, schema)


# -------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------

def main() -> None:
    eval_path = BASE_DIR / "data" / "training" / "eval.jsonl"
    adapter_dir = BASE_DIR / "models" / "lora_handover"

    if not eval_path.exists():
        sys.exit(f"Missing {eval_path}. Run generate_training_data.py first.")

    records: list[dict] = []
    with open(eval_path) as f:
        for line in f:
            records.append(json.loads(line))
    print(f"Loaded {len(records)} eval examples.")

    # Load models
    print("Loading base model ...")
    from gliner2 import GLiNER2

    base_model = GLiNER2.from_pretrained("fastino/gliner2-base-v1")
    base_model.eval()

    ft_model = None
    if adapter_dir.exists():
        print("Loading fine-tuned adapter ...")
        ft_model = GLiNER2.from_pretrained("fastino/gliner2-base-v1")
        ft_model.load_adapter(str(adapter_dir))
        ft_model.eval()
    else:
        print(f"[warn] Adapter not found at {adapter_dir} — skipping fine-tuned column.")

    # Evaluate
    results: list[dict[str, float]] = []

    for i, record in enumerate(records):
        transcript: str = record["input"]
        gold_entities: dict = record["output"].get("entities", {})
        gold_sev_list: list = record["output"].get("classifications", [{}])[0].get(
            "true_label", ["routine"]
        )
        gold_sev: str = gold_sev_list[0] if gold_sev_list else "routine"
        gold_sbar: dict = (record["output"].get("json_structures") or [{}])[0].get(
            "sbar_card", {}
        )

        base_out = run_model(base_model, transcript)
        base_ent = base_out.get("entities") or {}
        base_sbar = base_out.get("sbar_card") or {}

        row: dict[str, float] = {
            "base_entity_recall": _entity_recall(base_ent, gold_entities),
            "base_severity_correct": float(_severity_correct(base_out, gold_sev)),
            "base_sbar_fill": _sbar_fill(base_sbar),
        }

        if ft_model is not None:
            ft_out = run_model(ft_model, transcript)
            ft_ent = ft_out.get("entities") or {}
            ft_sbar = ft_out.get("sbar_card") or {}
            row["ft_entity_recall"] = _entity_recall(ft_ent, gold_entities)
            row["ft_severity_correct"] = float(_severity_correct(ft_out, gold_sev))
            row["ft_sbar_fill"] = _sbar_fill(ft_sbar)

        results.append(row)
        print(
            f"  [{i+1}/{len(records)}] "
            f"base_recall={row['base_entity_recall']:.2f}  "
            + (
                f"ft_recall={row.get('ft_entity_recall', 0):.2f}"
                if ft_model
                else ""
            )
        )

    # Aggregate
    def avg(key: str) -> str:
        vals = [r[key] for r in results if key in r]
        return f"{sum(vals)/len(vals)*100:.1f}%" if vals else "–"

    # Markdown table
    header = (
        "| Metric | Base GLiNER2 | Fine-tuned (LoRA r=8) |\n"
        "|--------|-------------|----------------------|\n"
    )
    rows = (
        f"| Entity recall    | {avg('base_entity_recall')} | {avg('ft_entity_recall')} |\n"
        f"| Severity correct | {avg('base_severity_correct')} | {avg('ft_severity_correct')} |\n"
        f"| SBAR fill rate   | {avg('base_sbar_fill')} | {avg('ft_sbar_fill')} |\n"
    )

    table = f"# GLiNER2 Eval — Base vs. Fine-tuned\n\n{header}{rows}\n"
    table += f"_Eval set: {len(records)} examples (held-out from synthetic training data)_\n"

    print("\n" + table)

    out_dir = BASE_DIR.parent / "docs"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "eval-results.md"
    out_path.write_text(table, encoding="utf-8")
    print(f"Results saved to {out_path}")


if __name__ == "__main__":
    main()
