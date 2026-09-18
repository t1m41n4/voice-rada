import hashlib, hmac, os, re, secrets, uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Literal
import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

DATABASE_URL=os.getenv('DATABASE_URL','sqlite:///./voicerada.db')
SECRET=os.getenv('VOICE_RADAR_SECRET','unsafe-local-secret')
engine=create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal=sessionmaker(bind=engine, autoflush=False)
class Base(DeclarativeBase): pass
class ReporterToken(Base):
    __tablename__='reporter_tokens'; id:Mapped[int]=mapped_column(primary_key=True); token:Mapped[str]=mapped_column(String(64),unique=True); source_type:Mapped[str]=mapped_column(String(24)); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
class Incident(Base):
    __tablename__='incidents'; id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4())); public_reference:Mapped[str]=mapped_column(String(20),unique=True); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now()); reported_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now()); category:Mapped[str]=mapped_column(String(40)); description:Mapped[str]=mapped_column(Text); source_type:Mapped[str]=mapped_column(String(24)); risk_level:Mapped[str]=mapped_column(String(12)); risk_score:Mapped[int]=mapped_column(Integer); confidence:Mapped[float]=mapped_column(Float); verification_status:Mapped[str]=mapped_column(String(16),default='UNVERIFIED'); location_name:Mapped[str|None]=mapped_column(String(200),nullable=True); latitude:Mapped[float|None]=mapped_column(Float,nullable=True); longitude:Mapped[float|None]=mapped_column(Float,nullable=True); ai_summary:Mapped[str]=mapped_column(Text); ai_extraction:Mapped[dict]=mapped_column(JSON); processing_status:Mapped[str]=mapped_column(String(16),default='PROCESSED'); content_hash:Mapped[str]=mapped_column(String(64),unique=True); events:Mapped[list['VerificationEvent']]=relationship(back_populates='incident')
class VerificationEvent(Base):
    __tablename__='verification_events'; id:Mapped[int]=mapped_column(primary_key=True); incident_id:Mapped[str]=mapped_column(ForeignKey('incidents.id')); status:Mapped[str]=mapped_column(String(16)); reviewer_reference:Mapped[str]=mapped_column(String(100)); notes:Mapped[str|None]=mapped_column(Text,nullable=True); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now()); incident:Mapped[Incident]=relationship(back_populates='events')
class TextReport(BaseModel): text:str=Field(min_length=3,max_length=5000); location_name:str|None=Field(default=None,max_length=200); phone_number:str|None=None; source_type:Literal['PWA','WHATSAPP','USSD','IVR','MOCK']='PWA'; provider_message_id:str|None=None
class Verify(BaseModel): status:Literal['VERIFIED','DISMISSED','NEEDS_REVIEW']; notes:str|None=Field(default=None,max_length=1000)
class Login(BaseModel): email:str; password:str
def db():
    s=SessionLocal()
    try: yield s
    finally:s.close()
def normalize_phone(v:str)->str: return '+'+re.sub(r'\D','',v).lstrip('0')
def reporter_hash(v:str)->str:return hmac.new(SECRET.encode(),normalize_phone(v).encode(),hashlib.sha256).hexdigest()
def extraction(text:str, location:str|None):
    t=text.lower(); cat='OTHER'; score=20; factors=[]
    rules=[(('flood','maji imeingia','mafuriko'),'FLOODING',70,'reported flooding'),(('fire','moto'),'FIRE',75,'reported fire'),(('threat','tishio'),'THREAT_REPORTED',65,'reported immediate threat'),(('injur','jeraha'),'MEDICAL_EMERGENCY',80,'reported injuries'),(('crowd','mkusanyiko'),'CROWD_ACTIVITY',40,'reported crowd activity'),(('water shortage','hakuna maji'),'WATER_SHORTAGE',45,'reported water shortage')]
    for words,c,s,f in rules:
      if any(w in t for w in words):cat,score,factors=c,s,[f];break
    if any(w in t for w in ('watu wengi','several','kadhaa')):score=min(100,score+10);factors.append('people reportedly affected')
    level='LOW' if score<30 else 'MODERATE' if score<50 else 'HIGH' if score<70 else 'SEVERE' if score<90 else 'CRITICAL'
    return cat,score,level,factors
def geo(name):
    known={'nairobi':(-1.2864,36.8172),'kibera':(-1.3133,36.7852),'kisumu':(-0.1022,34.7617),'mombasa':(-4.0435,39.6682),'garissa':(-0.4536,39.6401)}
    if not name:return None,None
    for k,p in known.items():
      if k in name.lower():return p
    return None,None
def serialize(i:Incident):return {'id':i.id,'public_reference':i.public_reference,'created_at':i.created_at,'category':i.category,'description':i.description,'source_type':i.source_type,'risk_level':i.risk_level,'risk_score':i.risk_score,'confidence':i.confidence,'verification_status':i.verification_status,'location_name':i.location_name,'latitude':i.latitude,'longitude':i.longitude,'ai_summary':i.ai_summary,'ai_extraction':i.ai_extraction,'processing_status':i.processing_status,'verification_events':[{'status':e.status,'reviewer_reference':e.reviewer_reference,'notes':e.notes,'created_at':e.created_at} for e in i.events]}
def user(token:str=Depends(lambda: None)): return token
def require_auth(request:Request):
    raw=request.headers.get('authorization','').removeprefix('Bearer ')
    try:return jwt.decode(raw,SECRET,algorithms=['HS256'])
    except Exception:raise HTTPException(401,'Responder authentication required')
@asynccontextmanager
async def lifespan(app): Base.metadata.create_all(engine); yield
app=FastAPI(title='VoiceRada API',version='0.1.0',lifespan=lifespan);app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:3000'],allow_methods=['*'],allow_headers=['*'])
@app.get('/health')
def health():return {'status':'ok'}
@app.get('/health/live')
def live():return {'status':'live'}
@app.get('/health/ready')
def ready(s:Session=Depends(db)):s.execute(select(1));return {'status':'ready'}
@app.post('/api/v1/auth/login')
def login(body:Login):
 if body.email==os.getenv('DEMO_RESPONDER_EMAIL','responder@voicerada.local') and secrets.compare_digest(body.password,os.getenv('DEMO_RESPONDER_PASSWORD','change-me')):return {'access_token':jwt.encode({'sub':body.email,'role':'RESPONDER','exp':datetime.now(timezone.utc)+timedelta(hours=8)},SECRET,algorithm='HS256')}
 raise HTTPException(401,'Invalid credentials')
@app.post('/api/v1/reports/text',status_code=202)
def report(body:TextReport,s:Session=Depends(db)):
 h=hashlib.sha256((body.source_type+'|'+body.text.strip().lower()+'|'+str(body.location_name)).encode()).hexdigest(); old=s.scalar(select(Incident).where(Incident.content_hash==h))
 if old:return {'status':'duplicate','incident_id':old.id}
 if body.phone_number:
  token=reporter_hash(body.phone_number)
  if not s.scalar(select(ReporterToken).where(ReporterToken.token==token)):s.add(ReporterToken(token=token,source_type=body.source_type))
 cat,score,level,factors=extraction(body.text,body.location_name);lat,lng=geo(body.location_name); ref='VR-'+uuid.uuid4().hex[:8].upper(); i=Incident(public_reference=ref,category=cat,description=body.text,source_type=body.source_type,risk_level=level,risk_score=score,confidence=.72 if cat!='OTHER' else .4,location_name=body.location_name,latitude=lat,longitude=lng,ai_summary='Automated extraction of an unverified report: '+body.text[:240],ai_extraction={'reported_event':body.text,'risk_factors':factors,'provider':'mock','untrusted_input':True},content_hash=h);s.add(i);s.commit();s.refresh(i);return {'status':'accepted','incident_id':i.id,'public_reference':ref}
@app.post('/api/v1/reports/mock',status_code=202)
def mock(s:Session=Depends(db)):return report(TextReport(text='Maji imeingia kwa nyumba kadhaa. Watu wanahitaji msaada na barabara imefungwa.',location_name='Kibera',source_type='MOCK'),s)
@app.post('/api/v1/webhooks/twilio/whatsapp',status_code=202)
def whatsapp(request:Request,body:dict,s:Session=Depends(db)):return report(TextReport(text=str(body.get('Body','')),phone_number=body.get('From'),location_name=body.get('Location'),source_type='WHATSAPP',provider_message_id=body.get('MessageSid')),s)
@app.get('/api/v1/incidents')
def incidents(limit:int=50,s:Session=Depends(db),_:dict=Depends(require_auth)):return [serialize(x) for x in s.scalars(select(Incident).order_by(Incident.created_at.desc()).limit(min(limit,100))).all()]
@app.get('/api/v1/incidents/{incident_id}')
def incident(incident_id:str,s:Session=Depends(db),_:dict=Depends(require_auth)):
 i=s.get(Incident,incident_id)
 if not i:raise HTTPException(404,'Incident not found')
 return serialize(i)
@app.patch('/api/v1/incidents/{incident_id}/verification')
def verify(incident_id:str,body:Verify,s:Session=Depends(db),claims:dict=Depends(require_auth)):
 i=s.get(Incident,incident_id)
 if not i:raise HTTPException(404,'Incident not found')
 i.verification_status=body.status;s.add(VerificationEvent(incident_id=i.id,status=body.status,reviewer_reference=claims['sub'],notes=body.notes));s.commit();s.refresh(i);return serialize(i)
@app.get('/api/v1/dashboard/summary')
def summary(s:Session=Depends(db),_:dict=Depends(require_auth)):
 rows=s.scalars(select(Incident)).all();return {'total_reports':len(rows),'high_priority':sum(x.risk_score>=50 for x in rows),'unverified':sum(x.verification_status=='UNVERIFIED' for x in rows),'verified':sum(x.verification_status=='VERIFIED' for x in rows),'active_clusters':0,'notice':'Automated triage supports prioritization; it is not an official emergency classification.'}
