from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import DATABASE_URL

engine=create_engine(DATABASE_URL,pool_pre_ping=True)
SessionLocal=sessionmaker(bind=engine,autoflush=False)

def get_db():
    session=SessionLocal()
    try:
        yield session
    finally:
        session.close()
