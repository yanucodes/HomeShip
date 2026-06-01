from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    database_url: str


settings = Settings()
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)


def get_session():
    """Provide a request-scoped session.

    If the endpoint returns normally, the session is committed; if anything
    raises, the entire request is rolled back. Repositories only flush (to
    populate PKs mid-request) — the durable commit happens here at the end.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
