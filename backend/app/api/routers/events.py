import jwt
from fastapi import APIRouter,WebSocket,WebSocketDisconnect
from app.core.config import VOICE_RADAR_SECRET
from app.db.session import SessionLocal
from app.models import RevokedToken
from app.services.realtime import event_hub

router=APIRouter(tags=['events'])
@router.websocket('/api/v1/events')
async def events(websocket:WebSocket):
    token=websocket.query_params.get('token','')
    session=SessionLocal()
    try:
        claims=jwt.decode(token,VOICE_RADAR_SECRET,algorithms=['HS256'])
        if not claims.get('jti') or session.get(RevokedToken,claims['jti']):raise ValueError('revoked')
    except Exception:
        session.close()
        await websocket.close(code=1008)
        return
    session.close()
    await event_hub.connect(websocket)
    try:
        while True:await websocket.receive_text()
    except WebSocketDisconnect:event_hub.disconnect(websocket)
