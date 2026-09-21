"""Add raw report processing records and their incident relationship."""
from alembic import op
import sqlalchemy as sa
revision='0002_raw_reports'
down_revision='0001_initial_schema'
branch_labels=None
depends_on=None
def upgrade():
    bind=op.get_bind();inspector=sa.inspect(bind)
    if not inspector.has_table('raw_reports'):
        op.create_table('raw_reports',sa.Column('id',sa.String(36),primary_key=True),sa.Column('source_type',sa.String(24),nullable=False),sa.Column('raw_text',sa.Text,nullable=False),sa.Column('location_name',sa.String(200)),sa.Column('provider_message_id',sa.String(128),unique=True),sa.Column('reporter_token_id',sa.Integer,sa.ForeignKey('reporter_tokens.id')),sa.Column('content_hash',sa.String(64),nullable=False,unique=True),sa.Column('processing_status',sa.String(16),nullable=False,server_default='RECEIVED'),sa.Column('processing_error',sa.Text),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.text('now()'),nullable=False),sa.Column('processed_at',sa.DateTime(timezone=True)))
    names={column['name'] for column in inspector.get_columns('incidents')}
    if 'raw_report_id' not in names:op.add_column('incidents',sa.Column('raw_report_id',sa.String(36),nullable=True))
def downgrade():
    if 'raw_report_id' in {column['name'] for column in sa.inspect(op.get_bind()).get_columns('incidents')}:op.drop_column('incidents','raw_report_id')
    if sa.inspect(op.get_bind()).has_table('raw_reports'):op.drop_table('raw_reports')
