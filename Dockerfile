# Neptou FastAPI — deploy to Railway, Fly.io, Render, etc.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY neptou_api ./neptou_api
# Copy or mount `places_clean.db` at deploy root (same dir as `neptou_api/`) or set PLACES_DB_PATH.

ENV PORT=8000
EXPOSE 8000

# Optional: override DB path if you mount a volume
# ENV PLACES_DB_PATH=/data/places_clean.db

CMD uvicorn neptou_api.main:app --host 0.0.0.0 --port ${PORT:-8000}
