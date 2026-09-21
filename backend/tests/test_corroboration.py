from datetime import datetime,timezone

from app.services.corroboration import _recent_sources,_status_for


def test_corroboration_keeps_only_sources_from_the_last_48_hours():
    now=datetime(2026,9,21,12,tzinfo=timezone.utc)
    sources=_recent_sources([
        {'title':'Recent source','source':'Kenya News','date':'2026-09-20T14:00:00Z','url':'https://news.example/recent'},
        {'title':'Old source','source':'Kenya News','date':'2026-09-18T11:59:00Z','url':'https://news.example/old'},
        {'title':'Undated source','source':'Kenya News','url':'https://news.example/undated'},
    ],now)
    assert [item['title'] for item in sources]==['Recent source']
    assert _status_for(sources)=='MEDIUM'


def test_corroboration_high_signal_requires_multiple_publishers():
    sources=[
        {'title':'A','source':'News A','published_at':'','url':'https://a.test'},
        {'title':'B','source':'News B','published_at':'','url':'https://b.test'},
        {'title':'C','source':'News C','published_at':'','url':'https://c.test'},
    ]
    assert _status_for(sources)=='HIGH'
