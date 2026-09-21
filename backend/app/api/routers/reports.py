import hashlib
from fastapi import APIRouter,BackgroundTasks,Depends,File,Form,HTTPException,UploadFile
from sqlalchemy.orm import Session
from app.api.deps import require_auth,require_role
from app.core.security import limit_public_request
from app.db.session import get_db
from app.models import RawReport
from app.schemas import SourceType,TextReportIn
from app.services.processing import process_audio_report_in_background,process_report_in_background,receive_text_report
router=APIRouter(prefix='/api/v1/reports',tags=['reports'])
@router.post('/text',status_code=202,dependencies=[Depends(limit_public_request)])
def submit_text(payload:TextReportIn,background_tasks:BackgroundTasks,session:Session=Depends(get_db)):
    raw,created=receive_text_report(session,payload)
    if not created:return {'status':'duplicate','report_id':raw.id,'incident_id':raw.incident.id if raw.incident else None}
    background_tasks.add_task(process_report_in_background,raw.id)
    return {'status':'accepted','report_id':raw.id,'processing_status':'RECEIVED'}
@router.post('/audio',status_code=202,dependencies=[Depends(limit_public_request)])
async def submit_audio(background_tasks:BackgroundTasks,audio:UploadFile=File(...),location_name:str|None=Form(default=None),phone_number:str|None=Form(default=None),source_type:SourceType=Form(default='IVR'),transcription:str|None=Form(default=None),session:Session=Depends(get_db)):
    if not (audio.content_type or '').startswith('audio/'):raise HTTPException(415,'Only audio uploads are accepted')
    content=await audio.read(10_000_001)
    if len(content)>10_000_000:raise HTTPException(413,'Audio exceeds the 10 MB MVP limit')
    audio_hash=hashlib.sha256(content).hexdigest();payload=TextReportIn(text='Audio report awaiting transcription.',location_name=location_name,phone_number=phone_number,source_type=source_type,provider_message_id=audio_hash)
    raw,created=receive_text_report(session,payload)
    if not created:return {'status':'duplicate','report_id':raw.id,'audio_retained':False}
    if transcription:
        raw.raw_text=transcription;session.commit()
        background_tasks.add_task(process_report_in_background,raw.id)
    else:
        background_tasks.add_task(process_audio_report_in_background,raw.id,content,audio.content_type or 'audio/webm',audio.filename or 'report.webm')
    return {'status':'accepted','report_id':raw.id,'audio_retained':False,'processing_status':'RECEIVED'}

@router.get('/processing',dependencies=[Depends(require_auth)])
def processing_queue(status:str|None=None,limit:int=50,session:Session=Depends(get_db)):
    safe_limit=max(1,min(limit,100))
    query=session.query(RawReport)
    if status:
        query=query.filter(RawReport.processing_status==status.upper())
    reports=query.order_by(RawReport.created_at.desc()).limit(safe_limit).all()
    return {'items':[{'id':raw.id,'source_type':raw.source_type,'location_name':raw.location_name,'processing_status':raw.processing_status,'processing_error':raw.processing_error,'created_at':raw.created_at,'retryable':raw.processing_status=='FAILED' and raw.raw_text!='Audio report awaiting transcription.'} for raw in reports]}

@router.post('/{report_id}/retry',dependencies=[Depends(require_role('RESPONDER','ADMIN'))])
def retry(report_id:str,background_tasks:BackgroundTasks,session:Session=Depends(get_db)):
    raw=session.get(RawReport,report_id)
    if not raw:raise HTTPException(404,'Report not found')
    if raw.processing_status!='FAILED':raise HTTPException(409,'Only failed reports can be retried')
    if raw.raw_text=='Audio report awaiting transcription.':raise HTTPException(409,'Audio was not retained; ask the reporter to submit it again')
    raw.processing_status='RECEIVED';raw.processing_error=None;session.commit()
    background_tasks.add_task(process_report_in_background,report_id)
    return {'status':'queued','report_id':report_id,'processing_status':'RECEIVED'}
