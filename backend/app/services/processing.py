import hashlib,uuid
from datetime import datetime,timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Evidence,Incident,RawReport,ReporterToken
from app.providers.groq import GroqSpeechToTextProvider
from app.providers.twilio import fetch_voice_recording
from app.providers import ProviderUnavailable
from app.providers.mapbox import MapboxGeocodingProvider
from app.providers.openrouter import OpenRouterExtractionProvider
from app.schemas import INCIDENT_CATEGORIES,TextReportIn
from app.services.privacy import reporter_hash
from app.services.triage import extract_and_triage
from app.services.spatial import set_incident_geometry
from app.db.session import SessionLocal
from app.services.realtime import event_hub
from app.services.corroboration import corroborate_incident_in_background

def incident_created_event(incident:Incident)->dict:
    return {
        'type':'incident.created',
        'incident_id':incident.id,
        'public_reference':incident.public_reference,
        'category':incident.category,
        'verification_status':incident.verification_status,
        'created_at':incident.created_at,
    }

def report_hash(payload:TextReportIn)->str:
    value='|'.join((payload.source_type,payload.text.strip().lower(),str(payload.location_name),str(payload.provider_message_id or '')))
    return hashlib.sha256(value.encode()).hexdigest()
def receive_text_report(session:Session,payload:TextReportIn)->tuple[RawReport,bool]:
    content_hash=report_hash(payload);existing=session.scalar(select(RawReport).where(RawReport.content_hash==content_hash))
    if existing:return existing,False
    token_id=None
    if payload.phone_number:
        token=reporter_hash(payload.phone_number);reporter=session.scalar(select(ReporterToken).where(ReporterToken.token==token))
        if not reporter:reporter=ReporterToken(token=token,source_type=payload.source_type);session.add(reporter);session.flush()
        token_id=reporter.id
    raw=RawReport(source_type=payload.source_type,raw_text=payload.text,location_name=payload.location_name,provider_message_id=payload.provider_message_id,reporter_token_id=token_id,content_hash=content_hash,processing_status='RECEIVED')
    session.add(raw);session.commit();session.refresh(raw);return raw,True
def process_report(session:Session,raw:RawReport,extraction_provider=None,geocoding_provider=None)->Incident:
    if raw.incident:return raw.incident
    raw.processing_status='PROCESSING';raw.processing_error=None;session.commit()
    try:
        extraction=(extraction_provider or OpenRouterExtractionProvider()).extract(raw.raw_text)
        rule_category,score,level,rule_factors=extract_and_triage(raw.raw_text)
        # IncidentExtraction is a Literal-backed model. This guard preserves a
        # safe operational fallback for non-conforming custom providers.
        category=extraction.category if extraction.category in INCIDENT_CATEGORIES else rule_category
        location_name=extraction.location_name or raw.location_name
        geocode=(geocoding_provider or MapboxGeocodingProvider()).geocode(location_name) if location_name else None
        incident=Incident(public_reference='VR-'+uuid.uuid4().hex[:8].upper(),raw_report_id=raw.id,category=category,description=raw.raw_text,source_type=raw.source_type,risk_level=level,risk_score=score,confidence=extraction.confidence,location_name=geocode.display_name if geocode and geocode.display_name else location_name,latitude=geocode.latitude if geocode else None,longitude=geocode.longitude if geocode else None,ai_summary=extraction.summary,ai_extraction={**extraction.model_dump(),'risk_factors':list(dict.fromkeys(extraction.risk_factors+rule_factors)),'provider':'openrouter','untrusted_input':True},processing_status='PROCESSED',content_hash=raw.content_hash)
        session.add(incident);session.flush();set_incident_geometry(session,incident.id,incident.latitude,incident.longitude);raw.processing_status='PROCESSED';raw.processed_at=datetime.now(timezone.utc);session.commit();session.refresh(incident);return incident
    except Exception as error:
        raw.processing_status='FAILED';raw.processing_error='Provider processing failed; responder retry is available.';session.commit()
        if isinstance(error,ProviderUnavailable):raise
        raise ProviderUnavailable('Incident processing failed') from error
def retry_report(session:Session,report_id:str)->Incident:
    raw=session.get(RawReport,report_id)
    if not raw:raise LookupError('Report not found')
    return process_report(session,raw)
def process_report_in_background(report_id:str):
    session=SessionLocal()
    try:
        raw=session.get(RawReport,report_id)
        if not raw:return
        incident=process_report(session,raw)
        event_hub.publish(incident_created_event(incident))
        corroborate_incident_in_background(incident.id)
    except ProviderUnavailable:
        event_hub.publish({'type':'report.failed','report_id':report_id})
    finally:session.close()

def process_audio_report_in_background(report_id:str,audio:bytes,content_type:str,filename:str):
    """Transcribe transient upload bytes, then discard them after processing."""
    session=SessionLocal()
    try:
        raw=session.get(RawReport,report_id)
        if not raw:return
        raw.processing_status='PROCESSING';raw.processing_error=None;session.commit()
        event_hub.publish({'type':'report.processing','report_id':report_id})
        transcript=GroqSpeechToTextProvider().transcribe(audio,content_type,filename)
        raw.raw_text=transcript.text
        session.commit()
        incident=process_report(session,raw)
        session.add(Evidence(incident_id=incident.id,evidence_type='AUDIO_HASH_ONLY',content_hash=hashlib.sha256(audio).hexdigest()))
        session.commit()
        event_hub.publish(incident_created_event(incident))
        corroborate_incident_in_background(incident.id)
    except ProviderUnavailable:
        raw=session.get(RawReport,report_id)
        if raw:
            raw.processing_status='FAILED'
            raw.processing_error='Audio processing failed; audio is not retained, so the report must be re-submitted.'
            session.commit()
        event_hub.publish({'type':'report.failed','report_id':report_id})
    finally:
        session.close()

def process_twilio_recording_in_background(report_id:str,recording_url:str):
    try:
        audio,content_type=fetch_voice_recording(recording_url)
    except ProviderUnavailable:
        session=SessionLocal()
        try:
            raw=session.get(RawReport,report_id)
            if raw:
                raw.processing_status='FAILED'
                raw.processing_error='IVR recording download failed; audio is not retained.'
                session.commit()
            event_hub.publish({'type':'report.failed','report_id':report_id})
        finally:
            session.close()
        return
    process_audio_report_in_background(report_id,audio,content_type,'twilio-recording')
