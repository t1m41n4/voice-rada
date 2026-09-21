"""Initial VoiceRada schema, safe for the MVP database created before migrations."""
from alembic import op
import sqlalchemy as sa

revision='0001_initial_schema'
down_revision=None
branch_labels=None
depends_on=None

def create_if_missing(name, *columns):
 if not sa.inspect(op.get_bind()).has_table(name):op.create_table(name,*columns)

def upgrade():
 create_if_missing('reporter_tokens',sa.Column('id',sa.Integer,primary_key=True),sa.Column('token',sa.String(64),nullable=False,unique=True),sa.Column('source_type',sa.String(24),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.text('now()'),nullable=False))
 create_if_missing('incidents',sa.Column('id',sa.String(36),primary_key=True),sa.Column('public_reference',sa.String(20),nullable=False,unique=True),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.text('now()'),nullable=False),sa.Column('reported_at',sa.DateTime(timezone=True),server_default=sa.text('now()'),nullable=False),sa.Column('category',sa.String(40),sa.CheckConstraint("category IN ('El Niño / Flood Emergency', 'Goon Activity & Intimidation', 'Electoral Tension', 'Resource Dispute')",name='ck_incidents_category'),nullable=False),sa.Column('description',sa.Text,nullable=False),sa.Column('source_type',sa.String(24),nullable=False),sa.Column('risk_level',sa.String(12),nullable=False),sa.Column('risk_score',sa.Integer,nullable=False),sa.Column('confidence',sa.Float,nullable=False),sa.Column('verification_status',sa.String(16),nullable=False,server_default='UNVERIFIED'),sa.Column('location_name',sa.String(200)),sa.Column('latitude',sa.Float),sa.Column('longitude',sa.Float),sa.Column('ai_summary',sa.Text,nullable=False),sa.Column('ai_extraction',sa.JSON,nullable=False),sa.Column('processing_status',sa.String(16),nullable=False,server_default='PROCESSED'),sa.Column('content_hash',sa.String(64),nullable=False,unique=True))
 create_if_missing('verification_events',sa.Column('id',sa.Integer,primary_key=True),sa.Column('incident_id',sa.String(36),sa.ForeignKey('incidents.id'),nullable=False),sa.Column('status',sa.String(16),nullable=False),sa.Column('reviewer_reference',sa.String(100),nullable=False),sa.Column('notes',sa.Text),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.text('now()'),nullable=False))
 create_if_missing('evidence',sa.Column('id',sa.Integer,primary_key=True),sa.Column('incident_id',sa.String(36),sa.ForeignKey('incidents.id'),nullable=False),sa.Column('evidence_type',sa.String(24),nullable=False),sa.Column('content_hash',sa.String(64),nullable=False),sa.Column('storage_key',sa.String(200)),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.text('now()'),nullable=False))

def downgrade():
 for table in ('evidence','verification_events','incidents','reporter_tokens'):
  if sa.inspect(op.get_bind()).has_table(table):op.drop_table(table)
