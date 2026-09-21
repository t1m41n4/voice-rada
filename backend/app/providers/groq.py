import httpx
from app.core.config import GROQ_API_KEY,GROQ_STT_MODEL,PROVIDER_TIMEOUT_SECONDS
from app.providers import ProviderUnavailable
from app.schemas import TranscriptionResult
class GroqSpeechToTextProvider:
    def transcribe(self,audio:bytes,content_type:str,filename:str)->TranscriptionResult:
        if not GROQ_API_KEY:raise ProviderUnavailable('GROQ_API_KEY is not configured')
        try:
            response=httpx.post('https://api.groq.com/openai/v1/audio/transcriptions',headers={'Authorization':'Bearer '+GROQ_API_KEY},files={'file':(filename,audio,content_type)},data={'model':GROQ_STT_MODEL,'response_format':'verbose_json','temperature':'0','prompt':'Transcribe faithfully. Audio may be Swahili, English, or Sheng. Do not add facts.'},timeout=PROVIDER_TIMEOUT_SECONDS)
            response.raise_for_status();data=response.json()
            return TranscriptionResult(text=data['text'],language=data.get('language'),duration=data.get('duration'),provider='groq:'+GROQ_STT_MODEL)
        except (httpx.HTTPError,KeyError,ValueError) as error:
            raise ProviderUnavailable('Groq transcription failed') from error
