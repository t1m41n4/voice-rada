from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import CLUSTER_RADIUS_METERS,VELOCITY_REPORT_THRESHOLD,VELOCITY_WINDOW_MINUTES

def set_incident_geometry(session:Session,incident_id:str,latitude:float|None,longitude:float|None):
    if latitude is not None and longitude is not None:session.execute(text('UPDATE incidents SET geom=ST_SetSRID(ST_MakePoint(:longitude,:latitude),4326) WHERE id=:id'),{'id':incident_id,'latitude':latitude,'longitude':longitude})
def nearby_incident_ids(session:Session,latitude:float,longitude:float,radius_meters:int=CLUSTER_RADIUS_METERS):
    rows=session.execute(text('SELECT id FROM incidents WHERE geom IS NOT NULL AND ST_DWithin(geom::geography,ST_SetSRID(ST_MakePoint(:longitude,:latitude),4326)::geography,:radius)'),{'latitude':latitude,'longitude':longitude,'radius':radius_meters}).all()
    return [row[0] for row in rows]
def spatial_clusters(session:Session):
    rows=session.execute(text('''SELECT id,public_reference,location_name,latitude,longitude FROM incidents WHERE geom IS NOT NULL AND created_at >= now() - (:minutes * interval '1 minute')'''),{'minutes':VELOCITY_WINDOW_MINUTES}).mappings().all()
    clusters=[];seen=set()
    for row in rows:
        if row['id'] in seen:continue
        members=nearby_incident_ids(session,row['latitude'],row['longitude'])
        recent=[item for item in rows if item['id'] in members]
        if len(recent)>=VELOCITY_REPORT_THRESHOLD:
            seen.update(item['id'] for item in recent)
            clusters.append({'location_name':row['location_name'],'report_count':len(recent),'window_minutes':VELOCITY_WINDOW_MINUTES,'radius_meters':CLUSTER_RADIUS_METERS,'incident_references':[item['public_reference'] for item in recent]})
    return clusters
