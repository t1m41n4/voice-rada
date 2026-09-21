from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import require_auth
from app.db.session import get_db
from app.models import Incident,VerificationEvent
from app.schemas import IncidentCategory,VerifyIn
from app.services.serialization import incident_response
from app.services.realtime import event_hub
from app.services.spatial import nearby_incident_ids
router=APIRouter(prefix='/api/v1/incidents',tags=['incidents'],dependencies=[Depends(require_auth)])
@router.get('')
def list_incidents(page:int=Query(default=1,ge=1),page_size:int=Query(default=25,ge=1,le=100),risk_level:str|None=None,verification_status:str|None=None,category:IncidentCategory|None=None,session:Session=Depends(get_db)):
    query=select(Incident)
    if risk_level:query=query.where(Incident.risk_level==risk_level.upper())
    if verification_status:query=query.where(Incident.verification_status==verification_status.upper())
    if category:query=query.where(Incident.category==category)
    results=session.scalars(query.order_by(Incident.created_at.desc())).all();start=(page-1)*page_size
    return {'items':[incident_response(item) for item in results[start:start+page_size]],'page':page,'page_size':page_size,'total':len(results)}
@router.get('/nearby')
def nearby(latitude:float=Query(ge=-90,le=90),longitude:float=Query(ge=-180,le=180),radius_meters:int=Query(default=1500,ge=100,le=50000),session:Session=Depends(get_db)):
    identifiers=nearby_incident_ids(session,latitude,longitude,radius_meters)
    incidents=session.scalars(select(Incident).where(Incident.id.in_(identifiers))).all()
    return {'items':[incident_response(item) for item in incidents],'radius_meters':radius_meters}
@router.get('/{incident_id}')
def get_incident(incident_id:str,session:Session=Depends(get_db)):
    incident=session.get(Incident,incident_id)
    if not incident:raise HTTPException(404,'Incident not found')
    return incident_response(incident,include_evidence=True)
@router.patch('/{incident_id}/verification')
def verify(incident_id:str,payload:VerifyIn,session:Session=Depends(get_db),claims:dict=Depends(require_auth)):
    incident=session.get(Incident,incident_id)
    if not incident:raise HTTPException(404,'Incident not found')
    incident.verification_status=payload.status;session.add(VerificationEvent(incident_id=incident.id,status=payload.status,reviewer_reference=claims['sub'],notes=payload.notes));session.commit();session.refresh(incident)
    event_hub.publish({'type':'incident.verified','incident_id':incident.id,'verification_status':incident.verification_status})
    return incident_response(incident,include_evidence=True)
