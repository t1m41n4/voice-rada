# VoiceRada

VoiceRada is a local-first hackathon MVP for receiving community observations and helping responders triage and verify them. Reports are always presented as **unverified** until a responder reviews them.

## Quick start

```powershell
Copy-Item .env.example .env
docker compose up --build
```

- PWA and operations dashboard: http://localhost:3001
- API and OpenAPI: http://localhost:8001/docs
- Health: http://localhost:8001/health

Use `responder@voicerada.local` / `change-me` to enter the demo dashboard (change both in `.env` outside a demo environment). Submit a fictional report such as `Maji imeingia kwa nyumba kadhaa karibu na mto. Watu wanahitaji msaada.` and location `Kibera`.

The local pipeline uses deterministic mock extraction and a small Kenyan-location demo geocoder. It needs no external credentials.

## Design decisions

- HMAC-SHA256 pseudonymizes a normalized phone number; the raw number is not persisted in application data.
- The report body is untrusted data. The mock extractor preserves it as a reported claim, and output is labeled AI-extracted.
- Protected responder routes require a JWT. Public report ingestion deliberately returns only an acceptance reference.
- Exact duplicate report payloads are idempotent through a content hash.

## Operations

```powershell
docker compose logs -f backend
docker compose down
```

`POST /api/v1/reports/mock` creates a fictional demo report. Twilio's local mock webhook accepts `Body`, `From`, `Location`, and `MessageSid` at `/api/v1/webhooks/twilio/whatsapp`; configure signature validation before a live deployment.

See [architecture](docs/architecture.md), [privacy](docs/privacy.md), [threat model](docs/threat-model.md), and [API notes](docs/api.md).
