# Local demo

## Start both services

```sh
uv sync --all-groups
npm --prefix ui ci
./demo.sh
```

The launcher starts FastAPI on `127.0.0.1:8000` and Vite on `127.0.0.1:5173`. It does not install packages, write logs, create snapshots, refresh a cache, or terminate unrelated processes. Press `Ctrl+C` to stop the services.

Set `API_PORT` or `UI_PORT` before starting if the defaults are occupied. The Vite proxy follows `API_PORT`.

## Command-line view

```sh
uv run python scripts/run_pipeline.py --data demo
uv run python scripts/run_pipeline.py --data demo --json
```

The command prints results to stdout and does not create an output artifact.

## API views

- `GET /api/health` reports deterministic mode and read-only status.
- `GET /api/overview` reports counts for the fictional result set.
- `GET /api/subsets` exposes filters derived from current records.
- `GET /api/emails?subset=mismatches` returns filtered summaries.
- `GET /api/emails/email_001/story` returns attachments, row anchors, trace steps, and the decision.

## Optional model experiment

```sh
export GEMINI_API_KEYS="your-key"
uv run python scripts/run_pipeline.py --data demo --gemini
```

This is intentionally separate from the normal launcher. Review the provider's data-handling terms before sending any non-public document.
