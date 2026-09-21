from app.schemas import GeocodingResult,IncidentExtraction
from app.providers import ProviderUnavailable
from app.services import processing

class Extraction:
    def extract(self,text):return IncidentExtraction(category='FLOODING',summary='Reporter described flooding.',reported_event=text,location_name='Kibera',severity_indicators=['water entry'],people_affected=None,immediate_danger=None,risk_factors=['reported flooding'],confidence=.8)
class Geocoder:
    def geocode(self,location):return GeocodingResult(latitude=-1.3133,longitude=36.7852,display_name=location,confidence=.9)
def authenticate(client):
    response=client.post('/api/v1/auth/login',json={'email':'responder@voicerada.local','password':'test-password-123'})
    return {'Authorization':'Bearer '+response.json()['access_token']}
def test_report_to_verification_flow(client,monkeypatch):
    monkeypatch.setattr(processing,'OpenRouterExtractionProvider',Extraction)
    monkeypatch.setattr(processing,'MapboxGeocodingProvider',Geocoder)
    created=client.post('/api/v1/reports/text',json={'text':'Maji imeingia kwa nyumba kadhaa.','location_name':'Kibera','phone_number':'0712 345 678','source_type':'PWA'})
    assert created.status_code==202
    report=created.json();assert report['processing_status']=='RECEIVED'
    assert client.get('/api/v1/incidents').status_code==401
    headers=authenticate(client)
    listed=client.get('/api/v1/incidents?page=1&page_size=10&risk_level=SEVERE',headers=headers)
    assert listed.status_code==200 and listed.json()['total']==1
    incident_id=listed.json()['items'][0]['id']
    detail=client.get('/api/v1/incidents/'+incident_id,headers=headers)
    assert detail.json()['category']=='FLOODING'
    verified=client.patch('/api/v1/incidents/'+incident_id+'/verification',headers=headers,json={'status':'VERIFIED','notes':'Reviewed in test.'})
    assert verified.json()['verification_status']=='VERIFIED'
    assert verified.json()['verification_events'][0]['status']=='VERIFIED'
def test_duplicate_report_is_idempotent(client,monkeypatch):
    monkeypatch.setattr(processing,'OpenRouterExtractionProvider',Extraction);monkeypatch.setattr(processing,'MapboxGeocodingProvider',Geocoder)
    payload={'text':'Flood water reported near homes.','location_name':'Kibera','source_type':'PWA'}
    assert client.post('/api/v1/reports/text',json=payload).json()['status']=='accepted'
    assert client.post('/api/v1/reports/text',json=payload).json()['status']=='duplicate'
def test_audio_rejects_invalid_content_type(client):
    response=client.post('/api/v1/reports/audio',files={'audio':('report.txt',b'not audio','text/plain')})
    assert response.status_code==415

def test_admin_can_provision_a_responder(client):
    headers=authenticate(client)
    created=client.post('/api/v1/auth/users',headers=headers,json={'email':'field.responder@example.test','password':'strong-test-password','role':'RESPONDER'})
    assert created.status_code==201
    assert created.json()['role']=='RESPONDER'
    login=client.post('/api/v1/auth/login',json={'email':'field.responder@example.test','password':'strong-test-password'})
    assert login.status_code==200
    responder_headers={'Authorization':'Bearer '+login.json()['access_token']}
    denied=client.post('/api/v1/auth/users',headers=responder_headers,json={'email':'another@example.test','password':'strong-test-password','role':'RESPONDER'})
    assert denied.status_code==403

def test_failed_processing_is_visible_and_retryable(client,monkeypatch):
    class FailingExtraction:
        def extract(self,text):raise ProviderUnavailable('unavailable')
    monkeypatch.setattr(processing,'OpenRouterExtractionProvider',FailingExtraction)
    report=client.post('/api/v1/reports/text',json={'text':'Bridge damage reported in town.','source_type':'PWA'}).json()
    headers=authenticate(client)
    queue=client.get('/api/v1/reports/processing?status=FAILED',headers=headers)
    failed=next(item for item in queue.json()['items'] if item['id']==report['report_id'])
    assert failed['processing_status']=='FAILED' and failed['retryable'] is True
    retried=client.post('/api/v1/reports/'+report['report_id']+'/retry',headers=headers)
    assert retried.status_code==200 and retried.json()['processing_status']=='RECEIVED'
