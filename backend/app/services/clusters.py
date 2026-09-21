from sqlalchemy.orm import Session
from app.services.spatial import spatial_clusters

def emerging_clusters(session:Session):
    return spatial_clusters(session)
