from typing import Literal
from pydantic import BaseModel,Field

SourceType=Literal['PWA','WHATSAPP','USSD','IVR','SEED']
IncidentCategory=Literal[
    'El Niño / Flood Emergency',
    'Goon Activity & Intimidation',
    'Electoral Tension',
    'Resource Dispute',
]

# Shared contract for provider validation, deterministic triage, database
# constraints, seed data, and API filters.
INCIDENT_CATEGORIES:tuple[IncidentCategory,...]=(
    'El Niño / Flood Emergency',
    'Goon Activity & Intimidation',
    'Electoral Tension',
    'Resource Dispute',
)
FALLBACK_INCIDENT_CATEGORY:IncidentCategory='Resource Dispute'

class TextReportIn(BaseModel):
    text:str=Field(min_length=3,max_length=5000)
    location_name:str|None=Field(default=None,max_length=200)
    phone_number:str|None=None
    source_type:SourceType='PWA'
    provider_message_id:str|None=Field(default=None,max_length=128)
class VerifyIn(BaseModel):
    status:Literal['VERIFIED','DISMISSED','NEEDS_REVIEW']
    notes:str|None=Field(default=None,max_length=1000)
class LoginIn(BaseModel):
    email:str
    password:str
class UssdWebhookIn(BaseModel):
    session_id:str=Field(min_length=3,max_length=100)
    phone_number:str=Field(min_length=7,max_length=30)
    description:str|None=Field(default=None,max_length=5000)
    location_name:str|None=Field(default=None,max_length=200)
class IvrWebhookIn(BaseModel):
    call_id:str=Field(min_length=3,max_length=100)
    caller_number:str=Field(min_length=7,max_length=30)
    consent:bool=False
    transcription:str|None=Field(default=None,max_length=5000)
    location_name:str|None=Field(default=None,max_length=200)
class IncidentExtraction(BaseModel):
    category:IncidentCategory
    subcategory:str|None=None
    summary:str
    reported_event:str
    location_name:str|None=None
    severity_indicators:list[str]=Field(default_factory=list)
    people_affected:int|None=None
    immediate_danger:bool|None=None
    risk_factors:list[str]=Field(default_factory=list)
    confidence:float=Field(ge=0,le=1)
class TranscriptionResult(BaseModel):
    text:str
    language:str|None=None
    duration:float|None=None
    provider:str
class GeocodingResult(BaseModel):
    latitude:float|None=None
    longitude:float|None=None
    display_name:str|None=None
    confidence:float=Field(ge=0,le=1)
