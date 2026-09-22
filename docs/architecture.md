# Architecture

VoiceRada is a three-container MVP:

```text
Next.js PWA + responder dashboard  <-->  FastAPI API + WebSockets  <-->  PostgreSQL/PostGIS
```

The public PWA is intentionally separate from the protected responder dashboard. The frontend supports offline text queueing and a small service-worker app shell; the backend owns ingestion, processing, verification, provider calls, and access control.

## Incident lifecycle

```text
Public channel
  -> raw report (RECEIVED)
  -> background processing (PROCESSING)
  -> Groq transcription when audio is supplied
  -> OpenRouter structured extraction + transparent rule scoring
  -> Mapbox Kenyan geocoding + PostGIS geometry
  -> incident (PROCESSED) or recoverable failure (FAILED)
  -> WebSocket update + non-blocking public-web corroboration
  -> human responder verification
```

The categories are constrained in both the schema and database constraint to Flood Emergency, Goon Activity & Intimidation, Electoral Tension, and Resource Dispute. Ambiguous reports use an explicit operational fallback, never an invented category.

## Storage and privacy boundaries

- `raw_reports` retains the submitted text only for authenticated responder review and processing recovery.
- `incidents` contains the responder-facing structured output, processing status, resolved location, PostGIS point, verification data, and bounded corroboration result.
- Phone numbers are transformed into HMAC reporter tokens; the raw number is not retained in application records.
- Audio is handled in memory for transcription, then discarded. `evidence` stores its SHA-256 hash only.
- The public list and acceptance response never expose raw report text.

## Integrations

Provider adapters isolate OpenRouter, Groq, Mapbox, Twilio, and public-news lookup failures. A missing key, timeout, or invalid provider response creates a visible failed-processing state rather than generated placeholder data. Twilio signatures are validated, and the public-web query is restricted to a resolved place label and operational category—never the raw report text.

## Realtime and spatial awareness

The FastAPI WebSocket endpoint publishes incident creation, processing failure, verification, and corroboration events. The dashboard refreshes its feed and map from those events.

PostGIS stores incident geometry and supports nearby-incident queries and configurable time/radius-based activity clusters. A cluster is a reporting-density signal requiring responder review, not confirmation of an event or its cause.
