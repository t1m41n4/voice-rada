# VoiceRada

VoiceRada is a privacy-first civic early-warning MVP for Kenya. Community members can submit climate-emergency and pre-election risk observations without creating an account; authenticated responders triage, map, review, and verify those reports.

> Reports are unverified community observations. AI extraction, risk scoring, clusters, and public-web signals support responder review; they never establish a fact on their own.

## What it does

- Accepts anonymous reports through the web PWA, WhatsApp, USSD, and Twilio voice/IVR flows.
- Supports typed and microphone reports. Audio is transcribed transiently and retained only as a SHA-256 evidence hash.
- Queues typed PWA reports locally when offline and retries them when the connection returns.
- Uses OpenRouter for structured triage, Groq for transcription, and Mapbox for Kenyan location resolution and the responder map.
- Shows processing states (`RECEIVED`, `PROCESSING`, `PROCESSED`, `FAILED`) and allows responders to retry failed text processing.
- Provides a protected tactical dashboard with filters, Kenya map markers, spatial activity clusters, verification history, raw-report review, and live WebSocket updates.
- Adds a time-bounded, privacy-safe public-web corroboration signal based only on the report category and resolved place name.

VoiceRada uses exactly these operational categories:

1. `El Niño / Flood Emergency`
2. `Goon Activity & Intimidation`
3. `Electoral Tension`
4. `Resource Dispute`

## Run locally

1. Create your local configuration without committing it:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Set a strong `DEMO_RESPONDER_PASSWORD` and, when ready, add provider credentials to `.env`.

3. Start the stack:

   ```powershell
   docker compose up --build
   ```

4. Open:

   - Public reporting PWA: <http://localhost:3001>
   - Responder dashboard: <http://localhost:3001/dashboard>
   - API documentation: <http://localhost:8001/docs>
   - Health check: <http://localhost:8001/health>

The backend runs Alembic migrations and creates the configured demo responder on startup. Use the email and password configured in `.env` to enter the responder dashboard.

## Demo flow

1. On the public PWA, choose a report domain, enter a fictional observation, and optionally add a Kenyan location or audio recording.
2. Confirm the public acceptance reference and the category-specific emergency-support card.
3. Sign in at `/dashboard` with the configured demo responder credentials.
4. Review the processing state, map location, AI-extracted summary, evidence hash, public-web signal, and raw report.
5. Verify the incident only after human review.

To populate a clearly labelled demo dashboard:

```powershell
docker compose exec backend python -m app.seed
```

## Configuration

Start with [`.env.example`](.env.example). Keep `.env` private and out of Git.

| Purpose | Variables |
| --- | --- |
| Local stack | `DATABASE_URL`, `BACKEND_PORT`, `FRONTEND_PORT`, `ALLOWED_ORIGINS`, `VOICE_RADAR_SECRET` |
| Demo responder | `DEMO_RESPONDER_EMAIL`, `DEMO_RESPONDER_PASSWORD` |
| AI and geocoding | `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `MAPBOX_ACCESS_TOKEN` |
| Browser map | `NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN` — use a Mapbox browser-restricted token only |
| Channel callbacks | `TWILIO_*` variables and public HTTPS callback URLs |
| Operations tuning | `VELOCITY_*`, `CLUSTER_RADIUS_METERS`, `PROVIDER_TIMEOUT_SECONDS` |

Real-provider setup and callback URLs are documented in [docs/providers.md](docs/providers.md).

## Privacy and security

- Reporters do not create accounts. Phone numbers, when supplied by a channel, are normalized and HMAC-SHA256 pseudonymized before storage.
- The public API returns only an acceptance reference; raw reports and detailed evidence require responder authentication.
- Responder passwords are bcrypt-hashed and dashboard sessions use JWTs with logout revocation.
- Public report and webhook routes are rate-limited. Twilio callbacks validate official request signatures.
- Audio uploads are processed in memory, then discarded. The database stores an evidence hash rather than a raw audio file.

Read [privacy notes](docs/privacy.md) and the [threat model](docs/threat-model.md) before a public deployment.

## Verify the build

```powershell
docker compose exec backend python -m pytest
docker compose exec frontend npm test
docker compose exec backend python -m alembic current
docker compose logs -f backend
```

## Deploy: Vercel + Railway

1. In Railway, create a **PostGIS** database service (not the default PostgreSQL template) and a backend service from this repository. Set the backend service Root Directory to `backend`, then generate its public HTTPS domain. Railway's `PORT` is handled automatically by the entrypoint.
2. In Railway backend variables, set `DATABASE_URL` as a reference to the PostGIS service URL, set `ALLOWED_ORIGINS` to the final Vercel origin, and add `VOICE_RADAR_SECRET`, demo responder credentials, and server-side provider credentials. The migration enables PostGIS before creating the geometry column.
3. In Vercel, import the same repository with Root Directory `frontend`. Set `NEXT_PUBLIC_API_URL` to the Railway API domain (for example, `https://your-api.up.railway.app`) and `NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN` to a browser-restricted Mapbox token. Redeploy whenever either `NEXT_PUBLIC_*` value changes.
4. After both domains exist, configure the exact Railway HTTPS callback URLs for Twilio WhatsApp, Twilio Voice, and Africa's Talking. Run fictional-report smoke tests before sharing the deployment.

Do not add provider secrets to Vercel or use a `NEXT_PUBLIC_` prefix for them.

## Project guide

- [Architecture](docs/architecture.md)
- [API notes](docs/api.md)
- [Provider setup](docs/providers.md)
- [Privacy](docs/privacy.md)
- [Threat model](docs/threat-model.md)
