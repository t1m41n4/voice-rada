# VoiceRada

VoiceRada is a local-first hackathon MVP for receiving community observations and helping responders triage and verify them. Reports are always presented as **unverified** until a responder reviews them.

## Access model

- **Reporters** use PWA, USSD, WhatsApp, or voice channels without creating a VoiceRada account.
- **Responders** authenticate to the dashboard to view incoming incidents and perform human verification. The demo responder credentials are configured through environment variables for judges; there is no administrator role in this MVP.

## Quick start

```powershell
Copy-Item .env.example .env
docker compose up --build
```

- PWA and operations dashboard: http://localhost:3001
- API and OpenAPI: http://localhost:8001/docs
- Health: http://localhost:8001/health

Set `DEMO_RESPONDER_EMAIL` and `DEMO_RESPONDER_PASSWORD` in `.env` before first startup. That configured responder can enter the dashboard and can be shared with hackathon judges; no administrator account or self-registration is needed. Submit a fictional report such as `Maji imeingia kwa nyumba kadhaa karibu na mto. Watu wanahitaji msaada.` and location `Kibera`.

OpenRouter extraction, Groq transcription, and Mapbox geocoding activate when their environment variables are configured. Until those credentials exist, reports remain visibly failed and can be retried; the application does not fabricate external-provider output.

## Design decisions

- HMAC-SHA256 pseudonymizes a normalized phone number; the raw number is not persisted in application data.
- The report body is untrusted data. The structured extraction prompt preserves it as a reported claim, and output is labeled AI-extracted.
- Protected responder routes require a JWT. Public report ingestion deliberately returns only an acceptance reference.
- Exact duplicate report payloads are idempotent through a content hash.

## Operations

```powershell
docker compose logs -f backend
docker compose down
docker compose exec backend python -m app.seed
docker compose exec backend pytest
docker compose exec frontend npm test
docker compose exec backend alembic current
```

The WhatsApp webhook accepts Twilio's `Body`, `From`, `Location`, and `MessageSid` fields at `/api/v1/webhooks/twilio/whatsapp`; it validates the official Twilio request signature before accepting the report.

`python -m app.seed` adds idempotent, clearly labelled **DEMO DATA** for a stronger dashboard demonstration.

The core automated checks cover report submission, provider failure/retry, responder roles, privacy normalization, provider signature/schema handling, landing/reporting UI, offline queueing, and microphone-denial UX.

See [architecture](docs/architecture.md), [privacy](docs/privacy.md), [threat model](docs/threat-model.md), and [API notes](docs/api.md).

See the [provider setup guide](docs/providers.md) before adding real credentials.
