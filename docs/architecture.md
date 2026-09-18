# Architecture

The MVP is a three-container vertical slice: Next.js mobile reporting/dashboard UI, FastAPI API, and PostgreSQL/PostGIS image. The current compact schema stores incidents, non-reversible reporter tokens, and verification events. Database coordinates are scalar fields in this MVP; PostGIS is selected so a geometry column/spatial queries can be added without replacing the service.

`POST report → HMAC token (if supplied) → deterministic mock extraction → cautious geocode → transparent risk rules → incident → responder verification`.

Risk rules inspect reported terms such as flooding, fire, threats and injuries, plus an explicit people-affected modifier. The score is a prioritization aid, not a statement of fact. Provider boundaries are intentionally small for the hackathon: mock extraction and geocoding are local; external STT/LLM/Mapbox adapters are deferred until credentials and a safe review process are available.

Must-have scope is text/PWA ingestion, protected feed, triage, location handling, duplicate prevention, verification, and a small IndexedDB queue for offline text reports. Queued reports retry when the browser comes back online; backend content-hash idempotency protects against a repeated delivery. Audio transformation, live telecom signature validation, WebSockets, service-worker shell caching, Alembic migrations, and production provider adapters are deferred rather than simulated.
