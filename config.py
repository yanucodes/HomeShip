"""Environment-backed application settings.

Loads configuration from the environment (`.env`) into a single `settings`
object that the rest of the app imports, so nothing reads `os.environ`
directly.
"""
from urllib.parse import urlsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed app settings.

    Attributes:
        database_url: Connection URL for the application database.
        test_database_url: Connection URL for the test database, or None
            when not running tests.
        jwt_secret_key: Secret key used to sign and verify JWT access tokens
            (HMAC). Has no default and must be supplied via the environment.
        jwt_algorithm: Algorithm used to sign access tokens. Defaults to
            HS256 (symmetric HMAC), matching the single shared jwt_secret_key.
        access_token_expire_minutes: Lifetime of an issued access token, in
            minutes (default 60).
        default_postpone_days: Days a task is pushed out when postponed without
            an explicit interval (default 3).
        supply_deadline_red_days: For a not-in-stock supply with a deadline,
            the alert is RED once the deadline is within this many days
            (default 1 = today or tomorrow).
        supply_deadline_yellow_days: For a not-in-stock supply with a
            deadline, the alert is YELLOW once the deadline is within this many
            days (and GREEN while further out). Must be >= the RED window.
        daily_rollover_hour: Local hour (0-23) at which a ship's day rolls over
            and the hourly cron advances it. Default 3 (3 AM) gives night owls
            a grace window to finish a last chore after midnight.
        cors_allowed_origins: Browser origins allowed to call the API, each as
            `scheme://host[:port]`. Defaults to the Vite dev server. Set in the
            environment as a JSON list.
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
    cors_allowed_origins: list[str] = ["http://localhost:5173"]

    @field_validator("cors_allowed_origins")
    @classmethod
    def _require_exact_origins(cls, value: list[str]) -> list[str]:
        """Reject entries that are wildcards or can never match a browser origin.

        Browsers send the origin as lowercase `scheme://host[:port]` and the
        CORS middleware compares it by exact string, so a trailing slash, a
        path or uppercase letters would block every request with no error on
        the server. Failing at startup makes that mistake visible.

        Args:
            value: The configured origins.

        Returns:
            The origins, unchanged.

        Raises:
            ValueError: If an entry is not an exact http(s) origin.
        """
        for origin in value:
            parts = urlsplit(origin)
            exact_origin = f"{parts.scheme}://{parts.netloc}".lower()
            if (
                parts.scheme not in ("http", "https")
                or not parts.netloc
                or "*" in origin
                or origin != exact_origin
            ):
                raise ValueError(
                    f"Invalid CORS origin {origin!r}: expected lowercase "
                    "scheme://host[:port], with no wildcard, path or trailing slash"
                )
        return value

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
