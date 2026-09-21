from datetime import datetime
import uuid
from sqlalchemy import CheckConstraint,DateTime,Float,ForeignKey,Integer,JSON,String,Text,func
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.db.base import Base

class ReporterToken(Base):
    __tablename__='reporter_tokens'
    id:Mapped[int]=mapped_column(primary_key=True)
    token:Mapped[str]=mapped_column(String(64),unique=True)
    source_type:Mapped[str]=mapped_column(String(24))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
class ResponderUser(Base):
    __tablename__='responder_users'
    id:Mapped[int]=mapped_column(primary_key=True)
    email:Mapped[str]=mapped_column(String(320),unique=True)
    password_hash:Mapped[str]=mapped_column(String(128))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())

class RevokedToken(Base):
    __tablename__='revoked_tokens'
    token_id:Mapped[str]=mapped_column(String(36),primary_key=True)
    expires_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())

class RawReport(Base):
    __tablename__='raw_reports'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
    source_type:Mapped[str]=mapped_column(String(24))
    raw_text:Mapped[str]=mapped_column(Text)
    location_name:Mapped[str|None]=mapped_column(String(200),nullable=True)
    provider_message_id:Mapped[str|None]=mapped_column(String(128),nullable=True,unique=True)
    reporter_token_id:Mapped[int|None]=mapped_column(ForeignKey('reporter_tokens.id'),nullable=True)
    content_hash:Mapped[str]=mapped_column(String(64),unique=True)
    processing_status:Mapped[str]=mapped_column(String(16),default='RECEIVED')
    processing_error:Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    processed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    incident:Mapped['Incident|None']=relationship(back_populates='raw_report',uselist=False)

class Incident(Base):
    __tablename__='incidents'
    __table_args__=(CheckConstraint("category IN ('El Niño / Flood Emergency', 'Goon Activity & Intimidation', 'Electoral Tension', 'Resource Dispute')",name='ck_incidents_category'),)
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
    public_reference:Mapped[str]=mapped_column(String(20),unique=True)
    raw_report_id:Mapped[str|None]=mapped_column(ForeignKey('raw_reports.id'),nullable=True,unique=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    reported_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    category:Mapped[str]=mapped_column(String(40),nullable=False)
    description:Mapped[str]=mapped_column(Text)
    source_type:Mapped[str]=mapped_column(String(24))
    risk_level:Mapped[str]=mapped_column(String(12))
    risk_score:Mapped[int]=mapped_column(Integer)
    confidence:Mapped[float]=mapped_column(Float)
    verification_status:Mapped[str]=mapped_column(String(16),default='UNVERIFIED')
    location_name:Mapped[str|None]=mapped_column(String(200),nullable=True)
    latitude:Mapped[float|None]=mapped_column(Float,nullable=True)
    longitude:Mapped[float|None]=mapped_column(Float,nullable=True)
    ai_summary:Mapped[str]=mapped_column(Text)
    ai_extraction:Mapped[dict]=mapped_column(JSON)
    processing_status:Mapped[str]=mapped_column(String(16),default='PROCESSED')
    content_hash:Mapped[str]=mapped_column(String(64),unique=True)
    raw_report:Mapped['RawReport|None']=relationship(back_populates='incident')
    events:Mapped[list['VerificationEvent']]=relationship(back_populates='incident')
    evidence:Mapped[list['Evidence']]=relationship(back_populates='incident')

class Evidence(Base):
    __tablename__='evidence'
    id:Mapped[int]=mapped_column(primary_key=True)
    incident_id:Mapped[str]=mapped_column(ForeignKey('incidents.id'))
    evidence_type:Mapped[str]=mapped_column(String(24))
    content_hash:Mapped[str]=mapped_column(String(64))
    storage_key:Mapped[str|None]=mapped_column(String(200),nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    incident:Mapped[Incident]=relationship(back_populates='evidence')

class VerificationEvent(Base):
    __tablename__='verification_events'
    id:Mapped[int]=mapped_column(primary_key=True)
    incident_id:Mapped[str]=mapped_column(ForeignKey('incidents.id'))
    status:Mapped[str]=mapped_column(String(16))
    reviewer_reference:Mapped[str]=mapped_column(String(100))
    notes:Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    incident:Mapped[Incident]=relationship(back_populates='events')
