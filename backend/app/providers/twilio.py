import httpx
from twilio.request_validator import RequestValidator
from app.core.config import PROVIDER_TIMEOUT_SECONDS,TWILIO_ACCOUNT_SID,TWILIO_AUTH_TOKEN,TWILIO_WHATSAPP_WEBHOOK_URL
from app.providers import ProviderUnavailable

def validate_whatsapp_webhook(url:str,params:dict[str,str],signature:str|None)->bool:
    return validate_twilio_webhook(url,params,signature,TWILIO_WHATSAPP_WEBHOOK_URL)

def validate_twilio_webhook(url:str,params:dict[str,str],signature:str|None,public_url:str='')->bool:
    if not TWILIO_AUTH_TOKEN:raise ProviderUnavailable('TWILIO_AUTH_TOKEN is not configured')
    signed_url=public_url or url
    return RequestValidator(TWILIO_AUTH_TOKEN).validate(signed_url,params,signature or '')

def fetch_voice_recording(recording_url:str)->tuple[bytes,str]:
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        raise ProviderUnavailable('Twilio voice credentials are not configured')
    try:
        with httpx.Client(timeout=PROVIDER_TIMEOUT_SECONDS) as client:
            response=client.get(recording_url,auth=(TWILIO_ACCOUNT_SID,TWILIO_AUTH_TOKEN))
            response.raise_for_status()
            return response.content,response.headers.get('content-type','audio/mpeg').split(';')[0]
    except httpx.HTTPError as error:
        raise ProviderUnavailable('Twilio recording download failed') from error
