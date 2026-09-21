# API

Public ingestion: `POST /api/v1/reports/text` with `{text, location_name?, phone_number?, source_type?}` returns `202`. Never send real sensitive reports to a development deployment.

`POST /api/v1/reports/audio` accepts multipart form data: an `audio` file, optional `location_name`, `phone_number`, source type, and optional `transcription`. The MVP reads at most 10 MB in memory, sends audio to Groq only when configured, records a SHA-256 evidence hash, and does not retain the raw upload.

Provider-neutral USSD and IVR adapters are available at `POST /api/v1/webhooks/ussd` and `POST /api/v1/webhooks/ivr`. USSD returns a menu until it receives a description. IVR requires explicit `consent: true` before it accepts a transcription. Both pseudonymize caller identifiers before any incident is stored.

Africa's Talking USSD callback is available at `POST /api/v1/webhooks/africastalking/ussd`. It accepts the standard form fields `sessionId`, `phoneNumber`, and `text`, and returns the `CON`/`END` plain-text protocol responses required by USSD gateways.

Twilio WhatsApp submits form data to `POST /api/v1/webhooks/twilio/whatsapp`. The endpoint validates `X-Twilio-Signature` with the official Twilio helper. Set `TWILIO_WHATSAPP_WEBHOOK_URL` to the exact public HTTPS callback URL configured in Twilio; this is necessary when the application is behind a proxy or tunnel.

Twilio IVR begins at `POST /api/v1/webhooks/twilio/voice`, asks for explicit keypad consent, and records only after consent. Its signed recording callback downloads the audio in a background task, transcribes it, and discards it.

Reporters do not have VoiceRada accounts. They can use the public PWA, USSD, WhatsApp, and voice-ingestion endpoints. Responders call `POST /api/v1/auth/login`, then pass `Authorization: Bearer <token>` to protected endpoints. `GET /api/v1/auth/me` returns the authenticated responder, and `POST /api/v1/auth/logout` revokes the current token. The incident list uses `page` and `page_size` pagination and accepts `risk_level`, `verification_status`, and `category` filters.

`GET /api/v1/dashboard/clusters` returns transparent, location-and-time based emerging-reporting clusters. `VELOCITY_WINDOW_MINUTES` and `VELOCITY_REPORT_THRESHOLD` configure its rule.

`GET /api/v1/incidents/nearby?latitude=-1.2864&longitude=36.8172&radius_meters=1500` returns protected radius-based nearby incident results. `CLUSTER_RADIUS_METERS` configures cluster proximity.

Submission first creates a raw report with `RECEIVED` processing state, then progresses through `PROCESSING` to `PROCESSED` or `FAILED`. A responder can retry a failed report at `POST /api/v1/reports/{report_id}/retry`.

`GET /api/v1/reports/processing` exposes the authenticated responder queue without returning raw report text. It supports a `status` filter. Only failed text reports are retryable; raw audio is deliberately discarded after processing and must be submitted again if transcription fails.

VoiceRada has no administrator role or user-management endpoint in this MVP. Authenticated responders can review, retry, and verify reports.

Health endpoints are `/health`, `/health/live`, and `/health/ready`. Full request/response schemas are exposed at `/docs`.
