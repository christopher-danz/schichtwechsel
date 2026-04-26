import logging
import os
from pathlib import Path

from app.models.sbar import SBARStructure
from app.services.sbar_mapper import heuristic_sbar, map_gliner_to_sbar
from app.schemas.sbar import build_sbar_schema

logger = logging.getLogger(__name__)

# Adapter lives relative to the backend package root
_ADAPTER_DIR = Path(__file__).parent.parent.parent / "models" / "lora_handover"


class GLiNERService:
    def __init__(self) -> None:
        self._local_model = None  # lazy-loaded when USE_FINETUNED=true

    async def extract_sbar(self, transcript: str) -> SBARStructure:
        use_finetuned = os.getenv("USE_FINETUNED", "false").lower() == "true"

        if use_finetuned:
            try:
                return self._extract_local_finetuned(transcript)
            except Exception as exc:
                logger.warning(
                    "Fine-tuned model failed (%s), falling back to heuristic", exc
                )
                return heuristic_sbar(transcript)

        api_key = os.getenv("PIONEER_API_KEY")
        if api_key:
            try:
                return self._extract_api(transcript, api_key)
            except Exception as exc:
                logger.warning(
                    "GLiNER2 API failed (%s), using heuristic fallback", exc
                )
        return heuristic_sbar(transcript)

    # ------------------------------------------------------------------
    # Pioneer cloud API path (default)
    # ------------------------------------------------------------------

    def _extract_api(self, transcript: str, api_key: str) -> SBARStructure:
        from gliner2 import GLiNER2API

        client = GLiNER2API(api_key=api_key)
        schema = build_sbar_schema(client)
        raw = client.extract(transcript, schema)
        return map_gliner_to_sbar(raw, transcript)

    # ------------------------------------------------------------------
    # Local fine-tuned model path (USE_FINETUNED=true)
    # ------------------------------------------------------------------

    def _extract_local_finetuned(self, transcript: str) -> SBARStructure:
        if not _ADAPTER_DIR.exists():
            raise FileNotFoundError(
                f"LoRA adapter not found at {_ADAPTER_DIR}. "
                "Run scripts/finetune.py first."
            )

        if self._local_model is None:
            logger.info("Loading fine-tuned GLiNER2 from %s ...", _ADAPTER_DIR)
            from gliner2 import GLiNER2

            model = GLiNER2.from_pretrained("fastino/gliner2-base-v1")
            model.load_adapter(str(_ADAPTER_DIR))
            model.eval()
            self._local_model = model
            logger.info("Fine-tuned model ready.")

        schema = build_sbar_schema(self._local_model)
        raw = self._local_model.extract(transcript, schema)
        return map_gliner_to_sbar(raw, transcript)
