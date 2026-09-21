import jwt
from fastapi import Depends,HTTPException,Request
from sqlalchemy.orm import Session
from app.core.config import VOICE_RADAR_SECRET
from app.db.session import get_db

def require_auth(request:Request):
    token=request.headers.get('authorization','').removeprefix('Bearer ')
    try:return jwt.decode(token,VOICE_RADAR_SECRET,algorithms=['HS256'])
    except Exception:raise HTTPException(401,'Responder authentication required')

def require_role(*roles:str):
    def check(claims:dict=Depends(require_auth)):
        if claims.get('role') not in roles:
            raise HTTPException(403,'Your responder role cannot perform this action')
        return claims
    return check

DbSession=Depends(get_db)
Responder=Depends(require_auth)
