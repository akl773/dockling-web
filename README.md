# Docling Web
A self-hosted, dockerized web interface for Docling to easily extract and parse documents.

## Overview
Docling Web is a modular monolith built to provide a robust web UI and API for the Docling document conversion library. It allows you to process PDF forms, extract contents into markdown, and manage conversion jobs via a persistent SQLite-backed queue, all packaged into a single deployable Docker container.

## Core Capabilities
- Web UI for document upload and conversion tracking
- FastAPI-powered API and static asset serving
- In-process background worker with reliable SQLite-backed job queue
- Persistent caching for Docling machine learning models to speed up repeat conversions
- Bundled downloading of multi-stage conversion results

## Tech Stack
- Backend: FastAPI, Python
- Frontend: React, TypeScript, Vite
- Data: SQLite (app.db)
- AI: Docling 2.84.0
- Infra: Docker Compose

## Architecture
The application runs as a modular monolith within a single Docker container. The Python runtime serves both the FastAPI endpoints and the compiled React SPA. It relies on an in-process background worker to manage and execute document conversion jobs asynchronously, utilizing a SQLite database for application state and queue history. Persistent Docker volumes store both application data (uploads, results) and the Docling model cache.

## Project Structure
```text
/data
  app.db                      # SQLite database
  uploads/{job_id}/*          # Source files
  results/{job_id}/*          # Extracted outputs (markdown, assets)
  bundles/{batch_id}.zip      # Zipped export bundles
```

## Getting Started

### Prerequisites
- Docker and Docker Compose locally installed

### Quick Run (Docker Hub)
```bash
docker run -p 6176:6176 -p 8176:8176 -v docling-data:/data akl49879/docling-web:latest
```
Then open `http://localhost:6176`

### Local Development
```bash
make up
```

1. Open `http://localhost:6176` in your browser for the web interface.
2. Open `http://localhost:8176/api/docs` for the Swagger UI API documentation.

## Configuration
The following environment variables can be configured in your `docker-compose.yml`:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| DATABASE_URL | Yes | SQLite connection string | sqlite:////data/app.db |
| DATA_DIR | Yes | Storage path for uploads and results | /data |
| OMP_NUM_THREADS | No | Number of threads for PyTorch/Docling | 4 |
| MAX_CONCURRENT_JOBS | No | Max active background conversion workers | 1 |
| FRONTEND_DIST_DIR | No | Path to served static frontend files | /app/frontend-dist |

## Usage
1. Upload a PDF document via the frontend running on `http://localhost:6176`.
2. The UI will track the queue progress which is stage-based: upload, queued, processing, serializing, bundling, done.
3. Note: The first conversion can be slower because Docling downloads machine-learning models into the persistent `docling_cache` volume.
4. Failed jobs in a batch do not block the rest of the batch queue.

## Development Workflow
Use the Makefile to manage the project:

```bash
make help           # Show all available targets
make up             # Start the app (Docker)
make down           # Stop the app
make dev            # Start both frontend and backend with hot reload
make dev-be         # Start backend only (hot reload)
make dev-fe         # Start frontend only (Vite HMR)
make check          # Run lint and tests
make clean         # Clean up containers and volumes
```
