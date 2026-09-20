from fastapi import APIRouter,Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
router=APIRouter(tags=['health'])
@router.get('/health')
def health():return {'status':'ok'}
@router.get('/health/live')
def live():return {'status':'live'}
@router.get('/health/ready')
def ready(session:Session=Depends(get_db)):session.execute(select(1));return {'status':'ready'}
