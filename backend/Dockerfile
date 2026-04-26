FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv --quiet

COPY pyproject.toml .
RUN uv pip install --system --no-cache .

# Pre-download the Whisper tiny model as root so it's baked into the image.
# HF_HOME is set to /app/.hf_cache so all HF downloads land in a
# location owned by appuser after the chown below.
ENV HF_HOME=/app/.hf_cache
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('tiny', device='cpu', compute_type='int8')"

COPY app/ app/
COPY data/ data/

EXPOSE 8000
RUN useradd -m -U -u 1000 appuser && chown -R 1000:1000 /app
USER 1000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
