import pytest
from app.services.privacy import normalize_phone, reporter_hash
from app.services.triage import extract_and_triage

def test_normalizes_common_kenyan_phone_formats():
    assert normalize_phone('0712 345 678') == '+254712345678'
    assert normalize_phone('+254 712 345 678') == '+254712345678'
    assert normalize_phone('712345678') == '+254712345678'

def test_reporter_token_is_stable_and_non_reversible():
    token=reporter_hash('0712 345 678')
    assert token == reporter_hash('+254712345678')
    assert len(token)==64
    assert '712345678' not in token

def test_flooding_triage_is_transparent_and_report_based():
    category,score,level,factors=extract_and_triage('Maji imeingia kwa nyumba kadhaa; watu wanahitaji msaada.')
    assert category=='El Niño / Flood Emergency'
    assert score==80
    assert level=='SEVERE'
    assert 'reported flood emergency' in factors

@pytest.mark.parametrize(('report','expected_category'),[
    ('Market traders report an extortion gang intimidating them.','Goon Activity & Intimidation'),
    ('Campaign friction and hate speech rumours are increasing.','Electoral Tension'),
    ('Pastoralists report a water dispute and livestock rustling.','Resource Dispute'),
])
def test_operational_triage_uses_only_the_four_categories(report,expected_category):
    category,_,_,_=extract_and_triage(report)
    assert category==expected_category

def test_unknown_report_keeps_low_confidence_category():
    category,score,level,_=extract_and_triage('A report was received but details are unclear.')
    assert (category,score,level)==('Resource Dispute',20,'LOW')
