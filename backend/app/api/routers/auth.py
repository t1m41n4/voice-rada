from datetime import datetime,timedelta,timezone
import jwt
from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import VOICE_RADAR_SECRET
from app.db.session import get_db
from app.models import ResponderUser
from app.api.deps import require_role
from app.schemas import LoginIn,ResponderUserIn
from app.services.users import hash_password,verify_password
router=APIRouter(prefix='/api/v1/auth',tags=['authentication'])
@router.post('/login')
def login(payload:LoginIn,session:Session=Depends(get_db)):
    user=session.scalar(select(ResponderUser).where(ResponderUser.email==payload.email.lower()))
    if user and verify_password(payload.password,user.password_hash):return {'access_token':jwt.encode({'sub':user.email,'role':user.role,'exp':datetime.now(timezone.utc)+timedelta(hours=8)},VOICE_RADAR_SECRET,algorithm='HS256')}
    raise HTTPException(401,'Invalid credentials')

@router.post('/users',status_code=status.HTTP_201_CREATED)
def create_responder(payload:ResponderUserIn,session:Session=Depends(get_db),_:dict=Depends(require_role('ADMIN'))):
    email=payload.email.lower()
    if session.scalar(select(ResponderUser).where(ResponderUser.email==email)):
        raise HTTPException(409,'A user with this email already exists')
    user=ResponderUser(email=email,password_hash=hash_password(payload.password),role=payload.role)
    session.add(user);session.commit();session.refresh(user)
    return {'id':user.id,'email':user.email,'role':user.role}
