import logging
import os

from app.models.sbar import SBARStructure
from app.services.sbar_mapper import heuristic_sbar, map_gliner_to_sbar
from app.schemas.sbar import build_sbar_schema

logger = logging.getLogger(__name__)


class GLiNERService:
    async def extract_sbar(self, transcript: str) -> SBARStructure:
        api_key = os.getenv("PIONEER_API_KEY")
        if api_key:
            try:
                return self._extract_api(transcript, api_key)
            except Exception as exc:
                logger.warning("GLiNER2 API failed (%s), using heuristic fallback", exc)
        return heuristic_sbar(transcript)

    def _extract_api(self, transcript: str, api_key: str) -> SBARStructure:
        from gliner2 import GLiNER2API

        client = GLiNER2API(api_key=api_key)
        schema = build_sbar_schema(client)
        raw = client.extract(transcript, schema)
        return map_gliner_to_sbar(raw, transcript)
