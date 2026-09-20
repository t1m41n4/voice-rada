"""Provider interfaces and real adapters are kept separate from route handlers."""
from typing import Protocol
from app.schemas import GeocodingResult,IncidentExtraction,TranscriptionResult

class IncidentExtractionProvider(Protocol):
    def extract(self,text:str)->IncidentExtraction: ...
class SpeechToTextProvider(Protocol):
    def transcribe(self,audio:bytes,content_type:str,filename:str)->TranscriptionResult: ...
class GeocodingProvider(Protocol):
    def geocode(self,location:str)->GeocodingResult: ...
class ProviderUnavailable(RuntimeError):
    pass
