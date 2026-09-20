from fastapi import APIRouter,BackgroundTasks,Depends,HTTPException,Request
from fastapi.responses import PlainTextResponse,Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import limit_public_request
from app.schemas import IvrWebhookIn,TextReportIn,UssdWebhookIn
from app.providers import ProviderUnavailable
from app.core.config import TWILIO_VOICE_WEBHOOK_URL
from app.providers.twilio import validate_twilio_webhook,validate_whatsapp_webhook
from app.services.processing import process_report_in_background,process_twilio_recording_in_background,receive_text_report
router=APIRouter(prefix='/api/v1/webhooks',tags=['webhooks'])
def ingest(session:Session,payload:TextReportIn,background_tasks:BackgroundTasks):
    raw,created=receive_text_report(session,payload)
    if not created:return {'status':'duplicate','report_id':raw.id}
    background_tasks.add_task(process_report_in_background,raw.id)
    return {'status':'accepted','report_id':raw.id,'processing_status':'RECEIVED'}
@router.post('/twilio/whatsapp',status_code=202,dependencies=[Depends(limit_public_request)])
async def whatsapp(request:Request,background_tasks:BackgroundTasks,session:Session=Depends(get_db)):
    form={key:str(value) for key,value in (await request.form()).items()}
    try:valid=validate_whatsapp_webhook(str(request.url),form,request.headers.get('X-Twilio-Signature'))
    except ProviderUnavailable:raise HTTPException(503,'Twilio webhook verification is not configured')
    if not valid:raise HTTPException(403,'Invalid Twilio signature')
    return ingest(session,TextReportIn(text=form.get('Body',''),phone_number=form.get('From'),location_name=form.get('Location'),source_type='WHATSAPP',provider_message_id=form.get('MessageSid')),background_tasks)

def twiml(body:str)->Response:
    return Response(f'<?xml version="1.0" encoding="UTF-8"?><Response>{body}</Response>',media_type='application/xml')

def signed_twilio_form(request:Request,form:dict[str,str]):
    suffix=request.url.path.removeprefix('/api/v1/webhooks/twilio/voice')
    public_url=TWILIO_VOICE_WEBHOOK_URL.rstrip('/')+suffix if TWILIO_VOICE_WEBHOOK_URL else str(request.url)
    try:valid=validate_twilio_webhook(str(request.url),form,request.headers.get('X-Twilio-Signature'),public_url)
    except ProviderUnavailable:raise HTTPException(503,'Twilio voice verification is not configured')
    if not valid:raise HTTPException(403,'Invalid Twilio signature')

@router.post('/twilio/voice')
async def twilio_voice(request:Request):
    form={key:str(value) for key,value in (await request.form()).items()};signed_twilio_form(request,form)
    return twiml('<Gather input="dtmf" numDigits="1" action="consent" method="POST"><Say>This is VoiceRada. Your report is unverified and will be reviewed by a human. Press 1 to consent to a short recording. Press any other key to end the call.</Say></Gather><Say>No consent was received. Goodbye.</Say>')

@router.post('/twilio/voice/consent')
async def twilio_voice_consent(request:Request):
    form={key:str(value) for key,value in (await request.form()).items()};signed_twilio_form(request,form)
    if form.get('Digits')!='1':return twiml('<Say>No recording will be made. Goodbye.</Say>')
    return twiml('<Say>After the tone, describe what happened and where. Press star when you finish.</Say><Record action="recording" method="POST" finishOnKey="*" maxLength="120" playBeep="true"/><Say>We did not receive a recording. Goodbye.</Say>')

@router.post('/twilio/voice/recording',status_code=202)
async def twilio_voice_recording(request:Request,background_tasks:BackgroundTasks,session:Session=Depends(get_db)):
    form={key:str(value) for key,value in (await request.form()).items()};signed_twilio_form(request,form)
    recording_url=form.get('RecordingUrl');call_id=form.get('CallSid')
    if not recording_url or not call_id:raise HTTPException(422,'Twilio RecordingUrl and CallSid are required')
    raw,created=receive_text_report(session,TextReportIn(text='Audio report awaiting transcription.',phone_number=form.get('From'),source_type='IVR',provider_message_id=call_id))
    if created:background_tasks.add_task(process_twilio_recording_in_background,raw.id,recording_url)
    return twiml('<Say>Thank you. Your report has been received as an unverified observation.</Say>')
@router.post('/ussd',dependencies=[Depends(limit_public_request)])
def ussd(payload:UssdWebhookIn,background_tasks:BackgroundTasks,session:Session=Depends(get_db)):
    if not payload.description:return {'response':'CON 1. Report incident\n2. Report flooding\n3. Report safety concern\n\nReply with your description and optional location.'}
    outcome=ingest(session,TextReportIn(text=payload.description,location_name=payload.location_name,phone_number=payload.phone_number,source_type='USSD',provider_message_id=payload.session_id),background_tasks)
    return {'response':'END Thank you. Your report was received as an unverified observation.','report_status':outcome['status'],'public_reference':outcome.get('public_reference')}
@router.post('/africastalking/ussd',response_class=PlainTextResponse,dependencies=[Depends(limit_public_request)])
async def africas_talking_ussd(request:Request,background_tasks:BackgroundTasks,session:Session=Depends(get_db)):
    form=await request.form();session_id=str(form.get('sessionId',''));phone=str(form.get('phoneNumber',''));text=str(form.get('text','')).strip()
    if not session_id or not phone:raise HTTPException(422,'Africa\'s Talking sessionId and phoneNumber are required')
    if not text:return 'CON 1. Report incident\n2. Report flooding\n3. Report safety concern\n4. Report other'
    parts=text.split('*',1);description=parts[1].strip() if len(parts)>1 else text
    if len(description)<3:return 'CON Please describe what happened and include a location if possible.'
    outcome=ingest(session,TextReportIn(text=description,phone_number=phone,source_type='USSD',provider_message_id=session_id),background_tasks)
    return 'END Thank you. Your report has been received as an unverified observation.' if outcome['status']=='accepted' else 'END Your report was already received.'
@router.post('/ivr')
def ivr(payload:IvrWebhookIn,background_tasks:BackgroundTasks,session:Session=Depends(get_db)):
    if not payload.consent:return {'recording_allowed':False,'message':'Consent is required before any recording or transcription is processed.'}
    if not payload.transcription:raise HTTPException(422,'A transcription is required before creating a report')
    outcome=ingest(session,TextReportIn(text=payload.transcription,location_name=payload.location_name,phone_number=payload.caller_number,source_type='IVR',provider_message_id=payload.call_id),background_tasks)
    return {'recording_allowed':True,'report_status':outcome['status'],'public_reference':outcome.get('public_reference')}
