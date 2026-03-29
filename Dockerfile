# Neptou FastAPI — deploy to Railway, Fly.io, Render, etc.
FROM python:3.12-slim

WORKDIR /app

COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

COPY . .

ENV PORT=8000
EXPOSE 8000

# places_clean.db must be in the image (committed or build step) for search/recommendations.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
