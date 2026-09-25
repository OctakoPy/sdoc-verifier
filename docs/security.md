# Security

The portfolio version is designed for a local, read-only demonstration. The API exposes `GET` routes, binds through the launcher to loopback, and keeps state in process memory. It does not write runtime snapshots, send email, reset records, or connect to cloud storage.

Gemini is never enabled by a normal request. An operator must explicitly provide a key in the environment and pass the opt-in flag to the CLI. When enabled, the relevant document content leaves the machine and is governed by the selected provider's terms. Use only fictional or authorized documents.

Do not add mutation, upload, authentication, or cloud features without an explicit threat model, authorization boundary, audit policy, and tests. Report security issues privately to the maintainers without including credentials or sensitive documents. The repository-level policy is in the root `SECURITY.md` file.
