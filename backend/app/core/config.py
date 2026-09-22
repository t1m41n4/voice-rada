import os

def normalize_database_url(value:str)->str:
    """Use psycopg 3 for standard PostgreSQL URLs supplied by deployment hosts."""
    value=value.strip()
    if value.startswith('postgres://'):
        value='postgresql://'+value.removeprefix('postgres://')
    if value.startswith('postgresql://'):
        return 'postgresql+psycopg://'+value.removeprefix('postgresql://')
    return value

def comma_separated_values(value:str)->list[str]:
    return [item.strip().rstrip('/') for item in value.split(',') if item.strip()]

DATABASE_URL=normalize_database_url(os.getenv('DATABASE_URL','sqlite:///./voicerada.db'))
ALLOWED_ORIGINS=comma_separated_values(os.getenv('ALLOWED_ORIGINS','http://localhost:3001'))
VOICE_RADAR_SECRET=os.getenv('VOICE_RADAR_SECRET','unsafe-local-secret')
VELOCITY_WINDOW_MINUTES=max(1,int(os.getenv('VELOCITY_WINDOW_MINUTES','60')))
VELOCITY_REPORT_THRESHOLD=max(2,int(os.getenv('VELOCITY_REPORT_THRESHOLD','3')))
CLUSTER_RADIUS_METERS=max(100,int(os.getenv('CLUSTER_RADIUS_METERS','1500')))
OPENROUTER_API_KEY=os.getenv('OPENROUTER_API_KEY','')
OPENROUTER_MODEL=os.getenv('OPENROUTER_MODEL','openai/gpt-4o-mini')
GROQ_API_KEY=os.getenv('GROQ_API_KEY','')
GROQ_STT_MODEL=os.getenv('GROQ_STT_MODEL','whisper-large-v3-turbo')
MAPBOX_ACCESS_TOKEN=os.getenv('MAPBOX_ACCESS_TOKEN','')
PROVIDER_TIMEOUT_SECONDS=float(os.getenv('PROVIDER_TIMEOUT_SECONDS','20'))
WEB_CORROBORATION_ENABLED=os.getenv('WEB_CORROBORATION_ENABLED','true').lower() in {'1','true','yes','on'}
WEB_CORROBORATION_MAX_RESULTS=max(1,min(10,int(os.getenv('WEB_CORROBORATION_MAX_RESULTS','5'))))
TWILIO_AUTH_TOKEN=os.getenv('TWILIO_AUTH_TOKEN','')
TWILIO_ACCOUNT_SID=os.getenv('TWILIO_ACCOUNT_SID','')
TWILIO_WHATSAPP_WEBHOOK_URL=os.getenv('TWILIO_WHATSAPP_WEBHOOK_URL','')
TWILIO_VOICE_WEBHOOK_URL=os.getenv('TWILIO_VOICE_WEBHOOK_URL','')
DEMO_RESPONDER_EMAIL=os.getenv('DEMO_RESPONDER_EMAIL','')
DEMO_RESPONDER_PASSWORD=os.getenv('DEMO_RESPONDER_PASSWORD','')
