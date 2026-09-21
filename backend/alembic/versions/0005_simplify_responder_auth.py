from alembic import op
import sqlalchemy as sa

revision='0005_simplify_responder_auth'
down_revision='0004_responder_users'
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    inspector=sa.inspect(bind)
    if inspector.has_table('responder_users') and 'role' in {column['name'] for column in inspector.get_columns('responder_users')}:
        op.drop_column('responder_users','role')
    if not inspector.has_table('revoked_tokens'):
        op.create_table('revoked_tokens',sa.Column('token_id',sa.String(36),primary_key=True),sa.Column('expires_at',sa.DateTime(timezone=True),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.text('now()'),nullable=False))

def downgrade():
    bind=op.get_bind()
    if sa.inspect(bind).has_table('revoked_tokens'):
        op.drop_table('revoked_tokens')
    if sa.inspect(bind).has_table('responder_users'):
        op.add_column('responder_users',sa.Column('role',sa.String(16),nullable=False,server_default='RESPONDER'))
