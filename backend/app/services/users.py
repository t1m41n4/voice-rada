import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import INITIAL_ADMIN_EMAIL,INITIAL_ADMIN_PASSWORD
from app.models import ResponderUser
def hash_password(password:str)->str:return bcrypt.hashpw(password.encode(),bcrypt.gensalt()).decode()
def verify_password(password:str,password_hash:str)->bool:return bcrypt.checkpw(password.encode(),password_hash.encode())
def ensure_initial_admin(session:Session):
    if not INITIAL_ADMIN_PASSWORD:
        return
    if not session.scalar(select(ResponderUser).where(ResponderUser.email==INITIAL_ADMIN_EMAIL)):
        session.add(ResponderUser(email=INITIAL_ADMIN_EMAIL,password_hash=hash_password(INITIAL_ADMIN_PASSWORD),role='ADMIN'));session.commit()
