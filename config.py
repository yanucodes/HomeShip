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
    jwt_algorithm: str
    access_token_expire_minutes: int = 60
    default_postpone_days: int = 3
    supply_deadline_red_days: int = 1
    supply_deadline_yellow_days: int = 7
    daily_rollover_hour: int = 3


settings = Settings()