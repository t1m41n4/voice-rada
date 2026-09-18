# API

Public ingestion: `POST /api/v1/reports/text` with `{text, location_name?, phone_number?, source_type?}` returns `202`. `POST /api/v1/reports/mock` makes a fictional report. Never send real sensitive reports to the demo.

Responders first call `POST /api/v1/auth/login`, then pass `Authorization: Bearer <token>` to `GET /api/v1/incidents`, `GET /api/v1/dashboard/summary`, and `PATCH /api/v1/incidents/{id}/verification` with `{status: VERIFIED|DISMISSED|NEEDS_REVIEW, notes?}`.

Health endpoints are `/health`, `/health/live`, and `/health/ready`. Full request/response schemas are exposed at `/docs`.
