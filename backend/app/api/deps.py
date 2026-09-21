import jwt
from fastapi import Depends,HTTPException,Request
from sqlalchemy.orm import Session
from app.core.config import VOICE_RADAR_SECRET
from app.db.session import get_db
from app.models import RevokedToken

def require_auth(request:Request,session:Session=Depends(get_db)):
    token=request.headers.get('authorization','').removeprefix('Bearer ')
    try:
        claims=jwt.decode(token,VOICE_RADAR_SECRET,algorithms=['HS256'])
        if not claims.get('jti') or session.get(RevokedToken,claims['jti']):
            raise HTTPException(401,'Responder authentication required')
        return claims
    except HTTPException:raise
    except Exception:raise HTTPException(401,'Responder authentication required')

DbSession=Depends(get_db)
Responder=Depends(require_auth)
