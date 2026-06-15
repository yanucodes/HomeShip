"""Environment-backed application settings.

Loads configuration from the environment (`.env`) into a single `settings`
object that the rest of the app imports, so nothing reads `os.environ`
directly.
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed app settings.

    Attributes:
        database_url: Connection URL for the application database.
        test_database_url: Connection URL for the test database, or None
            when not running tests.
        supply_deadline_red_days: For a not-in-stock supply with a deadline,
            the alert is RED once the deadline is within this many days
            (default 1 = today or tomorrow).
        supply_deadline_yellow_days: For a not-in-stock supply with a
            deadline, the alert is YELLOW once the deadline is within this many
            days (and GREEN while further out). Must be >= the RED window.
        daily_rollover_hour: Local hour (0-23) at which a ship's day rolls over
            and the hourly cron advances it. Default 3 (3 AM) gives night owls
            a grace window to finish a last chore after midnight.
    """
    model_config = SettingsConfigDict(env_file=".env")
    database_url: str
    test_database_url: str | None = None
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    default_postpone_days: int = 3
    supply_deadline_red_days: int = 1
    supply_deadline_yellow_days: int = 7
    daily_rollover_hour: int = 3

    @field_validator("database_url", "test_database_url")
    @classmethod
    def _use_psycopg_driver(cls, value: str | None) -> str | None:
        """Force the psycopg (v3) driver on bare PostgreSQL URLs.

        Hosts like Render expose a connection string as `postgres://...` or
        `postgresql://...`, both of which SQLAlchemy maps to the psycopg2
        driver — which this project does not install (it uses psycopg 3). This
        rewrites such URLs to the explicit `postgresql+psycopg://` form.

        Args:
            value: The raw connection URL, or None.

        Returns:
            The URL with the psycopg driver made explicit, or None unchanged.
        """
        if value is None:
            return value
        if value.startswith("postgres://"):
            value = "postgresql://" + value[len("postgres://"):]
        if value.startswith("postgresql://"):
            value = "postgresql+psycopg://" + value[len("postgresql://"):]
        return value


settings = Settings()
