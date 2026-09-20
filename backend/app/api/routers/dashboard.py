from fastapi import APIRouter,Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import require_auth
from app.db.session import get_db
from app.models import Incident
from app.services.clusters import emerging_clusters
router=APIRouter(prefix='/api/v1/dashboard',tags=['dashboard'],dependencies=[Depends(require_auth)])
@router.get('/summary')
def summary(session:Session=Depends(get_db)):
    incidents=session.scalars(select(Incident)).all()
    return {'total_reports':len(incidents),'high_priority':sum(item.risk_score>=50 for item in incidents),'unverified':sum(item.verification_status=='UNVERIFIED' for item in incidents),'verified':sum(item.verification_status=='VERIFIED' for item in incidents),'active_clusters':len(emerging_clusters(session)),'notice':'Automated triage supports prioritization; it is not an official emergency classification.'}
@router.get('/clusters')
def clusters(session:Session=Depends(get_db)):
    return {'clusters':emerging_clusters(session),'notice':'Emerging reporting activity is generated from unverified reports and requires responder review.'}
