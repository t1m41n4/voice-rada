from datetime import datetime,timedelta,timezone
import uuid
import jwt
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import require_auth
from app.core.config import VOICE_RADAR_SECRET
from app.db.session import get_db
from app.models import ResponderUser,RevokedToken
from app.schemas import LoginIn
from app.services.users import verify_password

router=APIRouter(prefix='/api/v1/auth',tags=['authentication'])

@router.post('/login')
def login(payload:LoginIn,session:Session=Depends(get_db)):
    user=session.scalar(select(ResponderUser).where(ResponderUser.email==payload.email.lower()))
    if not user or not verify_password(payload.password,user.password_hash):
        raise HTTPException(401,'Invalid responder credentials')
    expires_at=datetime.now(timezone.utc)+timedelta(hours=8)
    token=jwt.encode({'sub':user.email,'jti':str(uuid.uuid4()),'exp':expires_at},VOICE_RADAR_SECRET,algorithm='HS256')
    return {'access_token':token,'token_type':'bearer','expires_at':expires_at}

@router.get('/me')
def me(claims:dict=Depends(require_auth)):
    return {'email':claims['sub']}

@router.post('/logout')
def logout(claims:dict=Depends(require_auth),session:Session=Depends(get_db)):
    expires_at=datetime.fromtimestamp(claims['exp'],timezone.utc)
    session.add(RevokedToken(token_id=claims['jti'],expires_at=expires_at))
    session.commit()
    return {'status':'logged_out'}
