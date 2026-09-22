from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import auth,dashboard,events,health,incidents,reports,webhooks
from app.services.realtime import event_hub
from app.core.middleware import SafeRequestLoggingMiddleware
from app.core.config import ALLOWED_ORIGINS
from app.db.session import SessionLocal
from app.services.users import ensure_demo_responder

@asynccontextmanager
async def lifespan(_:FastAPI):
    event_hub.attach_loop()
    session=SessionLocal()
    try:ensure_demo_responder(session)
    finally:session.close()
    yield
app=FastAPI(title='VoiceRada API',version='0.2.0',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=ALLOWED_ORIGINS,allow_methods=['*'],allow_headers=['*'])
app.add_middleware(SafeRequestLoggingMiddleware)
for router in (health.router,auth.router,reports.router,webhooks.router,incidents.router,dashboard.router,events.router):
    app.include_router(router)
