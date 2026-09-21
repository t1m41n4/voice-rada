"""Create clearly fictional local demo incidents; safe to run repeatedly."""
from app.db.session import SessionLocal
from app.schemas import GeocodingResult,IncidentExtraction,TextReportIn
from app.services.processing import process_report,receive_text_report

# Seed records are deliberately fixed fictional data. They exercise the normal
# raw-report -> incident pipeline without calling external providers and keep
# demo dashboards stable for judges.
DEMO_REPORTS=[
    {
        'category':'El Niño / Flood Emergency',
        'text':'DEMO DATA: Flash flooding has cut off a bridge near several homes after heavy rain.',
        'location_name':'Baringo County',
        'latitude':-0.491,
        'longitude':35.743,
    },
    {
        'category':'Resource Dispute',
        'text':'DEMO DATA: Pastoralist families report a water-point dispute and livestock access friction.',
        'location_name':'Tana River County',
        'latitude':-1.482,
        'longitude':40.033,
    },
    {
        'category':'Goon Activity & Intimidation',
        'text':'DEMO DATA: Market traders report an extortion ring intimidating people near the market.',
        'location_name':'Kisumu County',
        'latitude':-0.1022,
        'longitude':34.7617,
    },
    {
        'category':'Electoral Tension',
        'text':'DEMO DATA: Residents report campaign friction and unverified hate-speech rumours.',
        'location_name':'Nairobi County',
        'latitude':-1.286389,
        'longitude':36.817223,
    },
    {
        'category':'Goon Activity & Intimidation',
        'text':'DEMO DATA: A community reports voter intimidation near a campaign gathering.',
        'location_name':'Uasin Gishu County (Eldoret)',
        'latitude':0.5143,
        'longitude':35.2698,
    },
]

class SeedExtractionProvider:
    def __init__(self,report:dict):self.report=report
    def extract(self,text:str)->IncidentExtraction:
        return IncidentExtraction(category=self.report['category'],summary='Fictional demo report requiring responder review.',reported_event=text,location_name=self.report['location_name'],severity_indicators=[],people_affected=None,immediate_danger=None,risk_factors=['fictional demo seed'],confidence=0.5)

class SeedGeocodingProvider:
    def __init__(self,report:dict):self.report=report
    def geocode(self,location_name:str)->GeocodingResult:
        return GeocodingResult(latitude=self.report['latitude'],longitude=self.report['longitude'],display_name=self.report['location_name'],confidence=1)

def main():
    session=SessionLocal()
    try:
        created=0
        for number,report in enumerate(DEMO_REPORTS,1):
            raw,is_new=receive_text_report(session,TextReportIn(text=report['text'],location_name=report['location_name'],source_type='SEED',provider_message_id=f'demo-seed-{number}'))
            if is_new:
                process_report(session,raw,SeedExtractionProvider(report),SeedGeocodingProvider(report))
                created+=1
        print(f'DEMO DATA: {created} incident(s) created; repeated runs are idempotent.')
    finally:session.close()

if __name__=='__main__':main()
