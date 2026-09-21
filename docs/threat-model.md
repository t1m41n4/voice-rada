# Threat model

Primary risks: malicious/spam reports, webhook spoofing, prompt injection embedded in report text, sensitive location disclosure, dashboard account theft, oversized/malicious audio, and duplicate delivery.

Current controls include Pydantic input limits, parameterized ORM queries, output-safe React rendering, HMAC pseudonyms, JWT protection, content-hash idempotency, rate limiting on public routes, request IDs, safe metadata-only request logs, and a strict distinction between reports and verified incidents. The OpenRouter extraction prompt treats every report as data, never as instructions.

Before production: add rate limiting/CAPTCHA as appropriate, encrypted object storage and audio scanning/size limits, security headers/CSRF review, short-lived refreshable sessions, audit log protection, PostGIS radius queries, retention jobs, secret rotation, and independent privacy/security review.
