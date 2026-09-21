# Provider setup

Add credentials only to your uncommitted `.env` file. Never expose server secrets through `NEXT_PUBLIC_*` variables.

## OpenRouter

Set `OPENROUTER_API_KEY` and optionally `OPENROUTER_MODEL`. The selected model must support strict JSON-schema structured outputs. VoiceRada sends untrusted report text inside a data boundary and validates the response with Pydantic.

## Groq

Set `GROQ_API_KEY` and optionally `GROQ_STT_MODEL=whisper-large-v3-turbo`. Groq receives in-memory audio only for transcription. VoiceRada stores an evidence hash, not the raw upload.

## Mapbox

Set `MAPBOX_ACCESS_TOKEN` for server geocoding. Set `NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN` to a browser-restricted public Mapbox token for the map UI; restrict it to the deployed site origin in Mapbox. Do not put a secret server token in the browser variable.

## Twilio WhatsApp

Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER`, and `TWILIO_WHATSAPP_WEBHOOK_URL`. Configure Twilio to send inbound WhatsApp messages to:

`https://YOUR_PUBLIC_HOST/api/v1/webhooks/twilio/whatsapp`

`TWILIO_WHATSAPP_WEBHOOK_URL` must be the identical public HTTPS URL. VoiceRada validates the `X-Twilio-Signature` before accepting a report.

## Twilio Voice / IVR

Configure the incoming-call webhook as `POST https://YOUR_PUBLIC_HOST/api/v1/webhooks/twilio/voice` and set that exact URL as `TWILIO_VOICE_WEBHOOK_URL`. The flow asks for keypad consent before recording, accepts at most 120 seconds, downloads the recording with `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`, transcribes it with Groq, then discards the downloaded audio. The recording callback is signature-validated before it is accepted.

## Africa's Talking USSD

Configure the USSD callback URL as:

`https://YOUR_PUBLIC_HOST/api/v1/webhooks/africastalking/ussd`

The adapter accepts the gateway's `sessionId`, `phoneNumber`, and `text` form values and returns `CON`/`END` responses. Ensure the provider dashboard has the correct callback URL for the production environment.

## Initial responder account

Set `INITIAL_ADMIN_EMAIL` and a strong `INITIAL_ADMIN_PASSWORD` before first startup. The backend hashes the password with bcrypt and only creates that bootstrap admin when no account has that email.

## Verification checklist

After configuration, rebuild the stack, run migrations, then verify a text report, an audio report, an inbound WhatsApp message with a valid Twilio signature, a Twilio IVR call, and a USSD session. Confirm provider failures become visible `FAILED` reports rather than fabricated results.
