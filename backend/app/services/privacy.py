import hashlib,hmac,re
from app.core.config import VOICE_RADAR_SECRET

def normalize_phone(value:str)->str:
    digits=re.sub(r'\D','',value)
    if len(digits)==10 and digits.startswith('0'):digits='254'+digits[1:]
    elif len(digits)==9 and digits.startswith('7'):digits='254'+digits
    return '+'+digits

def reporter_hash(value:str)->str:
    return hmac.new(VOICE_RADAR_SECRET.encode(),normalize_phone(value).encode(),hashlib.sha256).hexdigest()
