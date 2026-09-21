"""Non-blocking, privacy-preserving public-web corroboration for responders."""

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.core.config import WEB_CORROBORATION_ENABLED
from app.models import Incident
from app.providers import ProviderUnavailable
from app.providers.news import DuckDuckGoNewsProvider
from app.providers.openrouter import OpenRouterExtractionProvider
from app.db.session import SessionLocal
from app.services.realtime import event_hub

MAX_SOURCE_AGE = timedelta(hours=48)


def _published_at(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace('Z', '+00:00'))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def _recent_sources(results: list[dict[str, Any]], now: datetime) -> list[dict[str, str]]:
    recent: list[dict[str, str]] = []
    for item in results:
        published = _published_at(item.get('date'))
        if not published or published > now + timedelta(minutes=5) or now - published > MAX_SOURCE_AGE:
            continue
        url = str(item.get('url') or '')
        publisher = str(item.get('source') or urlparse(url).netloc or 'Unknown publisher')
        title = str(item.get('title') or '').strip()
        if not title or not url:
            continue
        recent.append({'title': title[:300], 'source': publisher[:160], 'published_at': published.isoformat(), 'url': url[:1000]})
    return recent


def _status_for(sources: list[dict[str, str]]) -> str:
    publishers = {source['source'].lower() for source in sources}
    if len(sources) >= 3 and len(publishers) >= 2:
        return 'HIGH'
    if sources:
        return 'MEDIUM'
    return 'UNVERIFIED'


def _fallback_summary(category: str, location_name: str | None, sources: list[dict[str, str]]) -> str:
    if not location_name:
        return 'No resolved Kenya location is available for a privacy-safe public-web check.'
    if not sources:
        return f'No recent public sources corroborating {category} near {location_name} were found in the last 48 hours.'
    return f'{len(sources)} recent public source(s) mention {category} near {location_name}; this is a signal for responder review, not verification.'


def corroborate_incident(
    session: Session,
    incident: Incident,
    *,
    news_provider: DuckDuckGoNewsProvider | None = None,
    audit_provider: OpenRouterExtractionProvider | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Store a time-bounded signal. Failure never blocks the incident lifecycle."""
    now = now or datetime.now(timezone.utc)
    if not WEB_CORROBORATION_ENABLED:
        result = {'status': 'UNVERIFIED', 'summary': 'Public-web corroboration is disabled for this environment.', 'sources': [], 'checked_at': now.isoformat(), 'availability': 'DISABLED'}
    elif not incident.location_name:
        result = {'status': 'UNVERIFIED', 'summary': _fallback_summary(incident.category, None, []), 'sources': [], 'checked_at': now.isoformat(), 'availability': 'AVAILABLE'}
    else:
        try:
            # The query uses only the category and resolver-produced place label.
            sources = _recent_sources((news_provider or DuckDuckGoNewsProvider()).search(incident.category, incident.location_name), now)
            summary = _fallback_summary(incident.category, incident.location_name, sources)
            audit_status = None
            if sources:
                try:
                    audit = (audit_provider or OpenRouterExtractionProvider()).audit_web_corroboration(
                        incident.category, incident.location_name, sources, now
                    )
                    summary = audit.summary
                    audit_status = audit.status
                except ProviderUnavailable:
                    # News evidence is still useful when the optional model audit is unavailable.
                    pass
            result = {
                'status': _status_for(sources),
                'summary': summary,
                'sources': sources,
                'checked_at': now.isoformat(),
                'availability': 'AVAILABLE',
                'ai_audit_status': audit_status,
            }
        except ProviderUnavailable:
            result = {
                'status': 'UNVERIFIED',
                'summary': 'Recent public-web corroboration is temporarily unavailable; responder review is still required.',
                'sources': [],
                'checked_at': now.isoformat(),
                'availability': 'UNAVAILABLE',
            }
    incident.web_corroboration = result
    session.commit()
    return result


def corroborate_incident_in_background(incident_id: str) -> None:
    session = SessionLocal()
    try:
        incident = session.get(Incident, incident_id)
        if not incident:
            return
        result = corroborate_incident(session, incident)
        event_hub.publish({'type': 'incident.corroborated', 'incident_id': incident.id, 'status': result['status']})
    finally:
        session.close()
