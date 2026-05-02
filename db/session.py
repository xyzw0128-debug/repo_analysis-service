from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


_ENGINE = None
_SESSION_LOCAL = None


def create_engine_from_url(database_url: str):
    return create_engine(database_url, future=True)


def get_engine(database_url: str):
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = create_engine_from_url(database_url)
    return _ENGINE


def get_session_local(database_url: str):
    global _SESSION_LOCAL
    if _SESSION_LOCAL is None:
        _SESSION_LOCAL = sessionmaker(bind=get_engine(database_url), autocommit=False, autoflush=False)
    return _SESSION_LOCAL
