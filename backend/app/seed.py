"""Create clearly fictional local demo incidents; safe to run repeatedly."""
from app.db.session import SessionLocal
from app.schemas import TextReportIn
from app.services.processing import process_report,receive_text_report

DEMO_REPORTS=[
 ('Maji imeingia kwa nyumba kadhaa karibu na mto. DEMO DATA: watu wanahitaji msaada.','Kibera'),
 ('DEMO DATA: Road blockage reported after heavy rain; no injuries confirmed.','Nairobi'),
 ('DEMO DATA: Community reports water shortage affecting several households.','Garissa'),
 ('DEMO DATA: Small crowd activity reported near the market; details remain unverified.','Kisumu'),
 ('DEMO DATA: Fire reported near a storage area; emergency services may be needed.','Mombasa'),
]
def main():
    session=SessionLocal()
    try:
        created=0
        for number,(text,location) in enumerate(DEMO_REPORTS,1):
            raw,is_new=receive_text_report(session,TextReportIn(text=text,location_name=location,source_type='SEED',provider_message_id=f'demo-seed-{number}'))
            if is_new:process_report(session,raw);created+=1
        print(f'DEMO DATA: {created} incident(s) created; repeated runs are idempotent.')
    finally:session.close()
if __name__=='__main__':main()
