"""Restrict incidents to the four Kenya operational categories."""
from alembic import op
import sqlalchemy as sa

revision='0006_enforce_incident_categories'
down_revision='0005_simplify_responder_auth'
branch_labels=None
depends_on=None

CONSTRAINT_NAME='ck_incidents_category'
CONSTRAINT_SQL="category IN ('El Niño / Flood Emergency', 'Goon Activity & Intimidation', 'Electoral Tension', 'Resource Dispute')"

def upgrade():
    bind=op.get_bind()
    inspector=sa.inspect(bind)
    if not inspector.has_table('incidents'):
        return

    # Map every legacy taxonomy value before enforcing the new contract.
    op.execute("""
        UPDATE incidents
        SET category = CASE
            WHEN category IN ('El Niño / Flood Emergency', 'Goon Activity & Intimidation', 'Electoral Tension', 'Resource Dispute') THEN category
            WHEN category IN ('FLOODING', 'LANDSLIDE', 'INFRASTRUCTURE_DAMAGE', 'DISPLACEMENT') THEN 'El Niño / Flood Emergency'
            WHEN category IN ('PUBLIC_SAFETY', 'CROWD_ACTIVITY', 'THREAT_REPORTED') THEN 'Goon Activity & Intimidation'
            WHEN category IN ('ELECTORAL_TENSION', 'COMMUNAL_TENSION') THEN 'Electoral Tension'
            ELSE 'Resource Dispute'
        END
    """)
    constraints={item.get('name') for item in inspector.get_check_constraints('incidents')}
    if CONSTRAINT_NAME not in constraints:
        op.create_check_constraint(CONSTRAINT_NAME,'incidents',CONSTRAINT_SQL)

def downgrade():
    inspector=sa.inspect(op.get_bind())
    if inspector.has_table('incidents') and CONSTRAINT_NAME in {item.get('name') for item in inspector.get_check_constraints('incidents')}:
        op.drop_constraint(CONSTRAINT_NAME,'incidents',type_='check')
