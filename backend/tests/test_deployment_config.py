from app.core.config import comma_separated_values, normalize_database_url
from app.core.security import InMemoryRateLimiter
from fastapi import HTTPException
import pytest


def test_normalize_database_url_uses_psycopg_for_railway_postgres_urls():
    assert normalize_database_url('postgresql://user:password@postgres:5432/voicerada') == 'postgresql+psycopg://user:password@postgres:5432/voicerada'
    assert normalize_database_url('postgres://user:password@postgres:5432/voicerada') == 'postgresql+psycopg://user:password@postgres:5432/voicerada'


def test_allowed_origins_are_trimmed_and_normalized():
    assert comma_separated_values(' https://app.example.com/ , http://localhost:3001 ') == ['https://app.example.com', 'http://localhost:3001']


def test_login_rate_limiter_rejects_repeated_attempts():
    limiter=InMemoryRateLimiter(limit=1,window_seconds=60)
    limiter.check('127.0.0.1')
    with pytest.raises(HTTPException) as error:
        limiter.check('127.0.0.1')
    assert error.value.status_code==429
