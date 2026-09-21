import json
import httpx
import pytest
from twilio.request_validator import RequestValidator
from app.providers import ProviderUnavailable
from app.providers import mapbox,openrouter,twilio

class Response:
    def __init__(self,data):self.data=data
    def raise_for_status(self):pass
    def json(self):return self.data
def test_openrouter_validates_structured_response(monkeypatch):
    monkeypatch.setattr(openrouter,'OPENROUTER_API_KEY','test-key')
    payload={'category':'El Niño / Flood Emergency','subcategory':None,'summary':'Reported flooding.','reported_event':'Water entered homes.','location_name':'Kibera','severity_indicators':[],'people_affected':None,'immediate_danger':None,'risk_factors':[],'confidence':.7}
    monkeypatch.setattr(openrouter.httpx,'post',lambda *args,**kwargs:Response({'choices':[{'message':{'content':json.dumps(payload)}}]}))
    assert openrouter.OpenRouterExtractionProvider().extract('Water entered homes.').category=='El Niño / Flood Emergency'
def test_openrouter_rejects_invalid_model_json(monkeypatch):
    monkeypatch.setattr(openrouter,'OPENROUTER_API_KEY','test-key')
    monkeypatch.setattr(openrouter.httpx,'post',lambda *args,**kwargs:Response({'choices':[{'message':{'content':'{}'}}]}))
    with pytest.raises(ProviderUnavailable):openrouter.OpenRouterExtractionProvider().extract('text')

def test_openrouter_rejects_a_category_outside_the_operational_taxonomy(monkeypatch):
    monkeypatch.setattr(openrouter,'OPENROUTER_API_KEY','test-key')
    payload={'category':'Invalid Category','subcategory':None,'summary':'Reported flooding.','reported_event':'Water entered homes.','location_name':'Kibera','severity_indicators':[],'people_affected':None,'immediate_danger':None,'risk_factors':[],'confidence':.7}
    monkeypatch.setattr(openrouter.httpx,'post',lambda *args,**kwargs:Response({'choices':[{'message':{'content':json.dumps(payload)}}]}))
    with pytest.raises(ProviderUnavailable):openrouter.OpenRouterExtractionProvider().extract('Water entered homes.')

def test_openrouter_web_audit_is_structured_and_time_aware(monkeypatch):
    monkeypatch.setattr(openrouter,'OPENROUTER_API_KEY','test-key')
    payload={'status':'MEDIUM','summary':'One recent public source indicates a possible related event.'}
    captured={}
    def post(*args,**kwargs):
        captured.update(kwargs['json']);return Response({'choices':[{'message':{'content':json.dumps(payload)}}]})
    monkeypatch.setattr(openrouter.httpx,'post',post)
    result=openrouter.OpenRouterExtractionProvider().audit_web_corroboration('Resource Dispute','Baringo County',[{'title':'Water report','source':'Example News','published_at':'2026-09-21T10:00:00+00:00','url':'https://example.test'}])
    assert result.status=='MEDIUM'
    assert 'Current UTC time:' in captured['messages'][0]['content']

def test_mapbox_reverses_browser_coordinates_into_a_place(monkeypatch):
    monkeypatch.setattr(mapbox,'MAPBOX_ACCESS_TOKEN','test-token')
    captured={}
    def get(url,**kwargs):
        captured['url']=url;captured['params']=kwargs['params']
        return Response({'features':[{'geometry':{'coordinates':[36.8172,-1.2864]},'properties':{'full_address':'Nairobi, Kenya'}}]})
    monkeypatch.setattr(mapbox.httpx,'get',get)
    result=mapbox.MapboxGeocodingProvider().geocode('-1.28640, 36.81720')
    assert captured['url'].endswith('/reverse')
    assert captured['params']['longitude']==36.8172
    assert result.display_name=='Nairobi, Kenya'
def test_twilio_signature_validation(monkeypatch):
    url='https://example.test/api/v1/webhooks/twilio/whatsapp';params={'Body':'hello','From':'whatsapp:+254700000000'};token='test-token'
    monkeypatch.setattr(twilio,'TWILIO_AUTH_TOKEN',token);monkeypatch.setattr(twilio,'TWILIO_WHATSAPP_WEBHOOK_URL',url)
    signature=RequestValidator(token).compute_signature(url,params)
    assert twilio.validate_whatsapp_webhook(url,params,signature)
    assert not twilio.validate_whatsapp_webhook(url,params,'invalid')
