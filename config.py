"""Environment-backed application settings.

Loads configuration from the environment (`.env`) into a single `settings`
object that the rest of the app imports, so nothing reads `os.environ`
directly.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed app settings.

    Attributes:
        database_url: Connection URL for the application database.
        test_database_url: Connection URL for the test database, or None
            when not running tests.
    """
    model_config = SettingsConfigDict(env_file=".env")
    database_url: str
    test_database_url: str | None = None
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int = 60
    default_postpone_days: int = 3


settings = Settings()