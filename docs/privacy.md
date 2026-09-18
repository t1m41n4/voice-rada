# Privacy

VoiceRada minimizes collection: a report body, optional location text, source type, derived incident fields, and (where a channel supplies it) a pseudonymous HMAC token. Raw phone numbers are normalized then immediately HMAC-SHA256 hashed with the server secret and are not stored in incidents or exposed by the API.

Coordinates and report text are sensitive. The responder APIs require authentication; public submitters receive only an acceptance reference. Retain operational data only as long as the configured deployment policy requires. This MVP has no deletion worker yet.

Offline text reports are temporarily stored in the browser's IndexedDB on the reporting device until delivery succeeds. Browser storage is not a substitute for device encryption or an organizational data-retention policy; users should avoid submitting sensitive information from a shared device.

External AI, geocoding, speech-to-text, and Mapbox integrations are optional and disabled locally. Enabling one may disclose selected report/location data to that provider, which needs a data-processing review. Pitch shifting, if added for stored audio, reduces some voice-identification cues but does not guarantee anonymity.

Human verification is required: AI extraction and triage are explicitly not verified facts.
