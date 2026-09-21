def extract_and_triage(text:str):
    lowered=text.lower();category='OTHER';score=20;factors=[]
    rules=[(('flood','maji imeingia','mafuriko'),'FLOODING',70,'reported flooding'),(('fire','moto'),'FIRE',75,'reported fire'),(('threat','tishio'),'THREAT_REPORTED',65,'reported immediate threat'),(('injur','jeraha'),'MEDICAL_EMERGENCY',80,'reported injuries'),(('crowd','mkusanyiko'),'CROWD_ACTIVITY',40,'reported crowd activity'),(('water shortage','hakuna maji'),'WATER_SHORTAGE',45,'reported water shortage')]
    for words,candidate,candidate_score,factor in rules:
        if any(word in lowered for word in words):category,score,factors=candidate,candidate_score,[factor];break
    if any(word in lowered for word in ('watu wengi','several','kadhaa')):
        score=min(100,score+10);factors.append('people reportedly affected')
    level='LOW' if score<30 else 'MODERATE' if score<50 else 'HIGH' if score<70 else 'SEVERE' if score<90 else 'CRITICAL'
    return category,score,level,factors
