import json
import httpx
import pytest
from twilio.request_validator import RequestValidator
from app.providers import ProviderUnavailable
from app.providers import openrouter,twilio

class Response:
    def __init__(self,data):self.data=data
    def raise_for_status(self):pass
    def json(self):return self.data
def test_openrouter_validates_structured_response(monkeypatch):
    monkeypatch.setattr(openrouter,'OPENROUTER_API_KEY','test-key')
    payload={'category':'FLOODING','subcategory':None,'summary':'Reported flooding.','reported_event':'Water entered homes.','location_name':'Kibera','severity_indicators':[],'people_affected':None,'immediate_danger':None,'risk_factors':[],'confidence':.7}
    monkeypatch.setattr(openrouter.httpx,'post',lambda *args,**kwargs:Response({'choices':[{'message':{'content':json.dumps(payload)}}]}))
    assert openrouter.OpenRouterExtractionProvider().extract('Water entered homes.').category=='FLOODING'
def test_openrouter_rejects_invalid_model_json(monkeypatch):
    monkeypatch.setattr(openrouter,'OPENROUTER_API_KEY','test-key')
    monkeypatch.setattr(openrouter.httpx,'post',lambda *args,**kwargs:Response({'choices':[{'message':{'content':'{}'}}]}))
    with pytest.raises(ProviderUnavailable):openrouter.OpenRouterExtractionProvider().extract('text')
def test_twilio_signature_validation(monkeypatch):
    url='https://example.test/api/v1/webhooks/twilio/whatsapp';params={'Body':'hello','From':'whatsapp:+254700000000'};token='test-token'
    monkeypatch.setattr(twilio,'TWILIO_AUTH_TOKEN',token);monkeypatch.setattr(twilio,'TWILIO_WHATSAPP_WEBHOOK_URL',url)
    signature=RequestValidator(token).compute_signature(url,params)
    assert twilio.validate_whatsapp_webhook(url,params,signature)
    assert not twilio.validate_whatsapp_webhook(url,params,'invalid')
