from app.models import Incident

def incident_response(incident:Incident,include_evidence:bool=False):
    result={'id':incident.id,'public_reference':incident.public_reference,'created_at':incident.created_at,'reported_at':incident.reported_at,'category':incident.category,'source_type':incident.source_type,'risk_level':incident.risk_level,'risk_score':incident.risk_score,'confidence':incident.confidence,'verification_status':incident.verification_status,'location_name':incident.location_name,'latitude':incident.latitude,'longitude':incident.longitude,'ai_summary':incident.ai_summary,'ai_extraction':incident.ai_extraction,'web_corroboration':incident.web_corroboration,'processing_status':incident.processing_status,'verification_events':[{'status':event.status,'reviewer_reference':event.reviewer_reference,'notes':event.notes,'created_at':event.created_at} for event in incident.events]}
    if include_evidence:
        # Exact raw report text is deliberately detail-only for authenticated responders.
        result['description']=incident.description
        result['evidence']=[{'evidence_type':item.evidence_type,'content_hash':item.content_hash,'created_at':item.created_at} for item in incident.evidence]
    return result
