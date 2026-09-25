# Architecture

## Data flow

```text
EmailRecord
    │
    ▼
Deterministic classifier ───────────────► non-comparison result
    │ BL comparison
    ▼
Safe local attachment loader
    │
    ├── TXT parser
    ├── XLSX parser
    ├── DOCX parser
    └── PDF parser
            │
            ▼
      readability gate
            │
            ├── unreadable / unsupported language ─► NEEDS_REVIEW
            ▼
  anchored field extraction
            │
            ▼
  normalization + comparison
            │
            ▼
  conservative review decision
            │
            ├── Trace events and row anchors
            ├── JSON story payload
            └── FastAPI GET views → React dashboard
```

## Contracts

`src/sdoc_verifier/models.py` defines the shared immutable contracts. The seven fields are declared once in `FIELDS`; extraction, comparison, provenance payloads, and UI labels use that canonical order.

`VerificationRecord` is the public result shape. It contains a category, one of three statuses, an optional review reason, mismatch fields, and whether deterministic rules or an explicitly enabled model path made the decision.

## Parser boundary

`parse_attachment()` dispatches by file suffix and returns the same `ParsedDocument` shape for every format. Parser failures become `UNREADABLE` records rather than exceptions escaping into the review stage. Attachment paths are resolved beneath the configured local data root before reading.

The PDF parser reads native text layers. A scan without explicit OCR remains unreadable and is escalated. The optional Gemini adapter is dynamically imported only when the caller supplies keys and explicitly enables the path.

## Provenance

Each parse event carries the normalized rows. The extraction event carries, for every canonical field, the zero-based source-row indices that produced it and whether a value is present. The comparison event carries raw SI/BL values and the normalized match flag. The API serializes these events; the browser only displays them.

## Read-only boundary

The API computes one in-memory result state from the configured local root. It has no persistence adapter, upload route, reset route, mail adapter, or cloud client. A process restart recomputes the deterministic state from the checked-in examples.
