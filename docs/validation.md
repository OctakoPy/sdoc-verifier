# Validation

## What is tested

The test suite is intentionally small and behavior-focused:

- deterministic subject/body classification and fallback;
- TXT, XLSX, DOCX, native PDF, scanned PDF, and non-English routing;
- anchored extraction and missing-value handling;
- formatting-only normalization and genuine mismatches;
- wrong-type, unreadable, missing-attachment, and conservative review decisions;
- source-row provenance in pipeline traces;
- attachment path containment;
- the ten fictional demo outcomes;
- API story assembly and a route-method invariant that permits only read-only methods;
- explicit model opt-in and local environment handling.

## Commands

```sh
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pyright
npm --prefix ui run lint
npm --prefix ui run build
uv run --group docs mkdocs build --strict
```

`just check` runs the complete local handoff set.

## Interpretation

The demo assertions are regression tests for intentionally authored examples. They demonstrate that the implementation handles the listed edge cases as designed. They are not a statistical benchmark and do not establish accuracy, recall, precision, robustness, or production readiness on independent real-world shipping documents.

The optional model tests use injected seams. The default test path does not require a model provider, credentials, or network access.
