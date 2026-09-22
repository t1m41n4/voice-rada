from app.core.config import comma_separated_values, normalize_database_url


def test_normalize_database_url_uses_psycopg_for_railway_postgres_urls():
    assert normalize_database_url('postgresql://user:password@postgres:5432/voicerada') == 'postgresql+psycopg://user:password@postgres:5432/voicerada'
    assert normalize_database_url('postgres://user:password@postgres:5432/voicerada') == 'postgresql+psycopg://user:password@postgres:5432/voicerada'


def test_allowed_origins_are_trimmed_and_normalized():
    assert comma_separated_values(' https://app.example.com/ , http://localhost:3001 ') == ['https://app.example.com', 'http://localhost:3001']
