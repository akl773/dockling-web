# Docling Web

Dockerized Docling web UI built as a simple modular monolith.

## Stack

- FastAPI backend serving API endpoints and built SPA assets
- In-process background worker with SQLite-backed queue and history
- React + TypeScript + Vite frontend
- Persistent Docker volumes for `/data` and Docling model cache
- `docling==2.84.0` pinned in `backend/requirements.txt`

## Run

```bash
docker compose up --build
```

Open `http://localhost:8080`.

## Storage Layout

```text
/data/
  app.db
  uploads/{job_id}/source.pdf
  results/{job_id}/output.md
  results/{job_id}/assets/*
  bundles/{batch_id}.zip
```

## Notes

- The first conversion can be slower because Docling downloads models into the persistent `docling_cache` volume.
- Queue progress is stage-based rather than per-page: upload, queued, processing, serializing, bundling, done.
- Failed jobs do not block the rest of a batch.

## Development

Backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
pytest backend/tests
uvicorn app.main:app --app-dir backend --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```
