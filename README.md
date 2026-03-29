# Neptou backend

## Layout

```
Neptou_BackEnd/
  neptou_api/
    main.py           # FastAPI app + CORS
    config.py         # Paths (e.g. PLACES_DB_PATH)
    database.py       # SQLite helpers
    schemas.py        # Pydantic models
    llm.py              # Anthropic calls
    routers/          # One module per route group
  requirements.txt
  Dockerfile
```

## Run locally

From this directory:

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn neptou_api.main:app --reload --host 0.0.0.0 --port 8000
```

Place `places_clean.db` here (or set `PLACES_DB_PATH` to a file path). Copy `.env` with `ANTHROPIC_API_KEY`.

## Docker

```bash
docker build -t neptou-api .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=... -v /path/to/places_clean.db:/app/places_clean.db neptou-api
```
