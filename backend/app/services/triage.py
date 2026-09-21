from app.schemas import FALLBACK_INCIDENT_CATEGORY,IncidentCategory

def extract_and_triage(text:str)->tuple[IncidentCategory,int,str,list[str]]:
    lowered=text.lower();category=FALLBACK_INCIDENT_CATEGORY;score=20;factors=['details insufficient; assigned operational fallback']
    rules=[
        (('flood','maji imeingia','mafuriko','mudslide','landslide','cut-off bridge','bridge cut','rising river','river overflow','mto umefurika','displaced families'),'El Niño / Flood Emergency',70,'reported flood emergency'),
        (('goon','gang','extortion','intimidation','voter intimidation','rally disruption','market extortion','tishio'),'Goon Activity & Intimidation',65,'reported intimidation or gang activity'),
        (('electoral','election','campaign','hate speech','hate-speech','political tension','inter-community political'),'Electoral Tension',55,'reported electoral tension'),
        (('land dispute','water dispute','water conflict','water shortage','hakuna maji','livestock rustling','cattle rustling','pastoralist','grazing','boundary dispute','ardhi'),'Resource Dispute',45,'reported resource dispute'),
    ]
    for words,candidate,candidate_score,factor in rules:
        if any(word in lowered for word in words):category,score,factors=candidate,candidate_score,[factor];break
    if any(word in lowered for word in ('watu wengi','several','kadhaa')):
        score=min(100,score+10);factors.append('people reportedly affected')
    level='LOW' if score<30 else 'MODERATE' if score<50 else 'HIGH' if score<70 else 'SEVERE' if score<90 else 'CRITICAL'
    return category,score,level,factors
