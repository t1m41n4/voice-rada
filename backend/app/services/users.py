import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import DEMO_RESPONDER_EMAIL,DEMO_RESPONDER_PASSWORD
from app.models import ResponderUser
def hash_password(password:str)->str:return bcrypt.hashpw(password.encode(),bcrypt.gensalt()).decode()
def verify_password(password:str,password_hash:str)->bool:return bcrypt.checkpw(password.encode(),password_hash.encode())
def ensure_demo_responder(session:Session):
    """Create or securely rotate the explicitly configured demo responder."""
    if not DEMO_RESPONDER_EMAIL or not DEMO_RESPONDER_PASSWORD:
        return
    email=DEMO_RESPONDER_EMAIL.lower()
    responder=session.scalar(select(ResponderUser).where(ResponderUser.email==email))
    if not responder:
        session.add(ResponderUser(email=email,password_hash=hash_password(DEMO_RESPONDER_PASSWORD)))
        session.commit()
    elif not verify_password(DEMO_RESPONDER_PASSWORD,responder.password_hash):
        responder.password_hash=hash_password(DEMO_RESPONDER_PASSWORD)
        session.commit()
