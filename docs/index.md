# SDOC Verifier

SDOC Verifier is a local, read-only portfolio implementation of a shipping-document verification workflow. It classifies an email, parses supported attachments, extracts seven canonical fields with source-row anchors, compares normalized SI and draft-BL values, and returns `OK`, `MISMATCH`, or `NEEDS_REVIEW`.

The default path is deterministic. Gemini is an explicit opt-in for scanned-PDF OCR and experimental label translation only. The checked-in examples are fictional and independently authored; they demonstrate behavior without representing a production validation study.

Start with [Demo](demo.md), then review [Architecture](architecture.md), [Validation](validation.md), and [Limitations](limitations.md).
