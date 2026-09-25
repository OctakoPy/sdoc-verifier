# SDOC Verifier

SDOC Verifier is a deterministic-first, auditable pipeline for checking a
Shipping Instruction (SI) against a draft Bill of Lading (BL). It classifies
shipping-operations email, parses TXT, XLSX, DOCX, and PDF attachments,
extracts seven canonical fields, preserves source-row provenance, normalizes
values, and returns one of three conservative decisions:

- `OK`: all required fields were present and equivalent after normalization.
- `MISMATCH`: one or more normalized values disagree.
- `NEEDS_REVIEW`: evidence is missing, unreadable, or the wrong document type.

The repository is a local portfolio project. The checked-in demo is fictional,
independently authored, and small enough to inspect. It is not a production
shipping system and does not provide independent real-world validation.

## Why it is built this way

The default path is deterministic. Gemini is optional and is used only when an
operator explicitly enables OCR for a scanned PDF or experimental translation
of non-English labels. A model-assisted result remains auditable through the
trace, and unavailable model access becomes `NEEDS_REVIEW` rather than a guess.

The strongest engineering assets are the typed contracts, format parser
abstraction, anchored extraction, source-row traces, normalization rules,
conservative review precedence, and contract tests.

## Quick start

Requirements: Python 3.11+, `uv`, Node.js 20+, and npm.

```sh
uv sync --all-groups
npm --prefix ui ci
./demo.sh
```

Open the local dashboard at `http://localhost:5173`. The launcher starts the
API on `http://127.0.0.1:8000` and stops both processes with `Ctrl+C`.

The demo is read-only. It does not send email, write output artifacts, persist
resolution state, access cloud storage, or require Google Cloud credentials.
The launcher binds services to loopback and does not install dependencies or
write runtime logs.

## Illustrative synthetic run

The checked-in set contains 10 fictional examples. A deterministic run yields
4 `OK`, 1 `MISMATCH`, and 5 `NEEDS_REVIEW` decisions. These counts describe
only the synthetic, in-distribution fixtures; they are not benchmark results
or evidence of independent real-world performance.

To run the pipeline without the dashboard:

```sh
uv run python scripts/run_pipeline.py --data demo
uv run python scripts/run_pipeline.py --data demo --json
```

## Optional Gemini experiments

The normal demo never reads credentials. To explicitly try the optional model
path, export a key in your shell and opt in on the command line:

```sh
export GEMINI_API_KEYS="your-key"
uv run python scripts/run_pipeline.py --data demo --gemini
```

This can send the selected attachment content to Gemini. The scanned PDF and
non-English label fixtures intentionally demonstrate the conservative
no-key path first. See [SECURITY.md](SECURITY.md) before using real documents.

## API surface

The local FastAPI service exposes read-only `GET` endpoints:

- `/api/health` — mode and read-only status.
- `/api/overview` — distributions for the current fictional result set.
- `/api/subsets` — deterministic filters derived from current results.
- `/api/emails` — summaries, optionally filtered by a subset.
- `/api/emails/{email_id}/story` — trace, attachments, anchors, and decision.

There are no upload, write, reset, mail, or public mutation routes.

## Architecture

```text
email record
  -> deterministic classification
  -> attachment dispatch (TXT / XLSX / DOCX / PDF)
  -> readability and document-kind gate
  -> anchored seven-field extraction
  -> normalization and SI/BL comparison
  -> conservative review decision
  -> trace and read-only API/UI view
```

The package lives in `src/sdoc_verifier/`. `api/` adapts the same pure core to
FastAPI, and `ui/` is a Vite/React dashboard. The browser never re-derives a
verdict: it displays values and provenance emitted by the pipeline trace.

See [docs/architecture.md](docs/architecture.md), [docs/validation.md](docs/validation.md),
[docs/limitations.md](docs/limitations.md), and [docs/data-provenance.md](docs/data-provenance.md).

## Development checks

```sh
just format-check
just lint
just type-check
just test
just ui-lint
just ui-build
just docs-build
```

The full local check is `just check`. Python tests include parser tests for all
four formats, normalization and review tests, trace/provenance tests, demo
pipeline tests, and API read-only invariants.

## Repository boundaries

The repository contains no private evaluation material, raw source corpus,
customer data, credentials, generated output artifacts, or hosted deployment. The
fictional fixtures under `demo/` are the only application data used by the
local demo. Binary fixtures can be regenerated with
`python scripts/build_demo_fixtures.py` from the checked-in fictional values.

## License and attribution

The project is released under [BSD-3-Clause](LICENSE). See [NOTICE](NOTICE)
for the limited starter-template attribution and [SECURITY.md](SECURITY.md)
for the local security posture.
