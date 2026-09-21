"""Add PostGIS incident geometry and spatial index."""
from alembic import op
import sqlalchemy as sa
revision='0003_incident_geometry'
down_revision='0002_raw_reports'
branch_labels=None
depends_on=None
def upgrade():
    columns={column['name'] for column in sa.inspect(op.get_bind()).get_columns('incidents')}
    if 'geom' not in columns:
        op.execute('ALTER TABLE incidents ADD COLUMN geom geometry(Point, 4326)')
        op.execute('UPDATE incidents SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) WHERE longitude IS NOT NULL AND latitude IS NOT NULL')
        op.execute('CREATE INDEX ix_incidents_geom ON incidents USING GIST (geom)')
def downgrade():
    op.execute('DROP INDEX IF EXISTS ix_incidents_geom')
    op.execute('ALTER TABLE incidents DROP COLUMN IF EXISTS geom')
