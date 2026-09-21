"""Persist responder-only, time-bounded public-web corroboration signals."""

from alembic import op
import sqlalchemy as sa


revision = '0007_add_web_corroboration'
down_revision = '0006_enforce_incident_categories'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table('incidents'):
        return
    columns = {column['name'] for column in inspector.get_columns('incidents')}
    if 'web_corroboration' not in columns:
        op.add_column('incidents', sa.Column('web_corroboration', sa.JSON(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table('incidents') and 'web_corroboration' in {column['name'] for column in inspector.get_columns('incidents')}:
        op.drop_column('incidents', 'web_corroboration')
