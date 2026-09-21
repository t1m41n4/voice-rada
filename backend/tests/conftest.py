import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
import app.models
from app.db.session import get_db
from app import main
from app.main import app
from app.services import processing
from app.services import users

@pytest.fixture
def client(monkeypatch):
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    testing_session=sessionmaker(bind=engine,autoflush=False)
    Base.metadata.create_all(engine)
    monkeypatch.setattr(users,'DEMO_RESPONDER_EMAIL','demo@example.test')
    monkeypatch.setattr(users,'DEMO_RESPONDER_PASSWORD','demo-password-123')
    bootstrap=testing_session();users.ensure_demo_responder(bootstrap);bootstrap.close()
    def override_db():
        session=testing_session()
        try:yield session
        finally:session.close()
    app.dependency_overrides[get_db]=override_db
    monkeypatch.setattr(main,'SessionLocal',testing_session)
    monkeypatch.setattr(processing,'SessionLocal',testing_session)
    monkeypatch.setattr(processing,'set_incident_geometry',lambda *args:None)
    with TestClient(app) as test_client:yield test_client
    app.dependency_overrides.clear()
