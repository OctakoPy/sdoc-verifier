# Data provenance

All application data in this repository is fictional and independently authored for the portfolio demo. Names, companies, ports, references, values, email subjects, and bodies were created solely to exercise the pipeline.

The demo contains ten compact inbox examples under `demo/inbox/` and fifteen small attachments under `demo/attachments/`. The cases cover:

- a matching TXT SI/BL pair;
- a mismatching DOCX pair;
- a missing value in XLSX;
- an unreadable/corrupt PDF;
- a scanned PDF that requires explicit OCR;
- a wrong document type;
- a non-comparison operations email;
- an SI request without attachments;
- a non-English label pair that requires explicit translation;
- a native PDF pair.

The DOCX, XLSX, and PDF files are small binary fixtures generated from the same fictional values by `scripts/build_demo_fixtures.py`. Regenerating them does not read an external corpus or private archive.

No real customer document, credential, private evaluation artifact, or production record is included. The examples are suitable for demonstrating behavior, not measuring real-world performance.
