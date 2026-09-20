# Architecture

The MVP is a three-container vertical slice: Next.js mobile reporting/dashboard UI, FastAPI API, and PostgreSQL/PostGIS image. The current compact schema stores incidents, non-reversible reporter tokens, and verification events. Database coordinates are scalar fields in this MVP; PostGIS is selected so a geometry column/spatial queries can be added without replacing the service.

Alembic runs the schema migration before the backend starts. The initial migration is deliberately safe for the pre-migration MVP database and records the schema version after checking for existing tables.

`POST report → HMAC token (if supplied) → Groq transcription (audio) → OpenRouter extraction → Mapbox geocode → transparent risk rules → incident → responder verification`.

Risk rules inspect reported terms such as flooding, fire, threats and injuries, plus an explicit people-affected modifier. The score is a prioritization aid, not a statement of fact. OpenRouter performs strict-schema incident extraction, Groq performs speech-to-text, and Mapbox performs Kenyan forward geocoding when their keys are configured. Providers are isolated behind adapters and their failure leaves the raw report visibly `FAILED` rather than silently fabricating a result.

The dashboard detects **emerging reporting activity** when the configured number of reports fall within the configured PostGIS geographic radius and time window. It never describes such activity as confirmed, and it does not infer a cause or identify people.

Must-have scope is text/PWA ingestion, protected feed, triage, location handling, duplicate prevention, verification, and a small IndexedDB queue for offline text reports. Queued reports retry when the browser comes back online; backend content-hash idempotency protects against a repeated delivery. Audio transformation, live telecom signature validation, WebSockets, service-worker shell caching, Alembic migrations, and production provider adapters are deferred rather than simulated.
