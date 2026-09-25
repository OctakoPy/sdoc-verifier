# Security

SDOC Verifier is a local, read-only demonstration. The default API exposes
GET endpoints only, binds to loopback through the local launcher, and keeps
pipeline results in process memory. It does not upload files, send email,
write a resolution log, or persist demo state.

## Optional model access

Gemini is not required and is never enabled by an ordinary API request or a
normal demo start. If an operator explicitly opts in to OCR or experimental
label translation, the selected document content is sent to the configured
model provider. Use only fictional or appropriately authorized documents and
review the provider's data-handling terms first. Do not place API keys in the
repository or commit `.env` files.

## Operational guidance

- Keep the API bound to `127.0.0.1` unless a separate access-control layer has
  been added.
- Treat demo fixtures as synthetic, not as a security test corpus.
- Do not add write, upload, reset, mail, or cloud-persistence routes without
  authentication, authorization, audit logging, and a documented threat model.
- Report suspected vulnerabilities privately to the repository maintainers.
  Do not include credentials, real customer documents, or answer-key material
  in a report.
