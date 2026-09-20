from alembic import op
import sqlalchemy as sa
revision='0004_responder_users';down_revision='0003_incident_geometry';branch_labels=None;depends_on=None
def upgrade():
    if not sa.inspect(op.get_bind()).has_table('responder_users'):op.create_table('responder_users',sa.Column('id',sa.Integer,primary_key=True),sa.Column('email',sa.String(320),nullable=False,unique=True),sa.Column('password_hash',sa.String(128),nullable=False),sa.Column('role',sa.String(16),nullable=False,server_default='RESPONDER'),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.text('now()'),nullable=False))
def downgrade():
    if sa.inspect(op.get_bind()).has_table('responder_users'):op.drop_table('responder_users')
