# Fictional demo set

These ten inbox records and their attachments are independently authored for
this repository. They are not copied from a production or private corpus.

| Case | Default decision | Purpose |
| --- | --- | --- |
| `email_001` | `OK` | Matching TXT SI/BL pair |
| `email_002` | `MISMATCH` | DOCX pair with a container-count difference |
| `email_003` | `NEEDS_REVIEW` | XLSX SI missing gross weight |
| `email_004` | `NEEDS_REVIEW` | Corrupt PDF attachment |
| `email_005` | `NEEDS_REVIEW` | Invoice paired with an SI |
| `email_006` | `OK` | Non-comparison operations email |
| `email_007` | `NEEDS_REVIEW` | Explicit OCR opt-in demonstration |
| `email_008` | `NEEDS_REVIEW` | Non-English labels without translation opt-in |
| `email_009` | `OK` | SI request without attachments |
| `email_010` | `OK` | Matching native PDF pair |

The optional model paths are not exercised by the default API or launcher.
Use the CLI's explicit `--gemini` flag only with documents you are authorized
to send to the selected provider.
