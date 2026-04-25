import logging
import os
import tempfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

_whisper_model: "WhisperModel | None" = None


def _get_whisper() -> "WhisperModel":
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel

        _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
    return _whisper_model


class TranscriptionService:
    async def transcribe(self, audio_bytes: bytes, content_type: str) -> str:
        api_key = os.getenv("GRADIUM_API_KEY")
        if api_key:
            try:
                return await self._gradium(audio_bytes, content_type, api_key)
            except Exception as exc:
                logger.warning("Gradium failed (%s), falling back to Whisper", exc)
        return await self._whisper(audio_bytes, content_type)

    async def _gradium(self, audio_bytes: bytes, content_type: str, api_key: str) -> str:
        from gradium import GradiumClient, STTSetup

        fmt = "wav" if "wav" in content_type else "webm"
        client = GradiumClient(api_key=api_key)
        setup = STTSetup(model_name="default", input_format=fmt)
        result = await client.stt(setup, audio_bytes)
        return result.text

    async def _whisper(self, audio_bytes: bytes, content_type: str) -> str:
        suffix = ".wav" if "wav" in content_type else ".webm"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        try:
            model = _get_whisper()
            segments, _ = model.transcribe(tmp_path, language="de")
            return " ".join(s.text.strip() for s in segments)
        finally:
            os.unlink(tmp_path)
