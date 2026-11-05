"""Unit tests for the CORS policy and its configuration.

No database: the CORS middleware answers preflights itself, and `GET /` doesn't
touch the session. Importing the app still needs the required settings in the
environment (`DATABASE_URL`, `JWT_SECRET_KEY`).
"""
# Test names describe the scenario; per-test docstrings would be redundant.
# pylint: disable=missing-function-docstring
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from config import Settings, settings
from main import app

ALLOWED_ORIGIN = settings.cors_allowed_origins[0]
OTHER_ORIGIN = "https://other.example"

client = TestClient(app)


def preflight(origin, method="POST"):
    return client.options(
        "/ships",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )


def settings_without_env_file(**values):
    # Required settings are passed in, so only the value under test can fail.
    return Settings(
        _env_file=None,
        database_url="postgresql://unused",
        jwt_secret_key="unused",
        **values,
    )


class TestPreflight:
    """Tests for the browser's OPTIONS check before a non-simple request."""

    def test_allowed_origin_is_echoed_back(self):
        response = preflight(ALLOWED_ORIGIN)
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN

    def test_other_origin_is_refused(self):
        response = preflight(OTHER_ORIGIN)
        assert response.status_code == 400
        assert "access-control-allow-origin" not in response.headers

    @pytest.mark.parametrize("method", ["GET", "POST", "PATCH", "DELETE"])
    def test_methods_the_api_uses_are_allowed(self, method):
        assert preflight(ALLOWED_ORIGIN, method=method).status_code == 200

    def test_credentials_are_not_allowed(self):
        response = preflight(ALLOWED_ORIGIN)
        assert "access-control-allow-credentials" not in response.headers


class TestActualRequest:
    """Tests for the CORS headers on a normal response."""

    def test_allowed_origin_can_read_the_response(self):
        response = client.get("/", headers={"Origin": ALLOWED_ORIGIN})
        assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN

    def test_other_origin_gets_no_allow_header(self):
        response = client.get("/", headers={"Origin": OTHER_ORIGIN})
        assert "access-control-allow-origin" not in response.headers


class TestAllowedOriginsSetting:
    """Tests for how CORS_ALLOWED_ORIGINS is parsed and validated."""

    def test_env_var_is_read_as_a_json_list(self, monkeypatch):
        monkeypatch.setenv(
            "CORS_ALLOWED_ORIGINS",
            '["https://app.example", "http://localhost:5173"]',
        )
        assert settings_without_env_file().cors_allowed_origins == [
            "https://app.example",
            "http://localhost:5173",
        ]

    @pytest.mark.parametrize(
        "origin",
        [
            "*",
            "https://*.example",
            "https://app.example/",
            "https://app.example/path",
            "https://App.example",
            "app.example",
            "ftp://app.example",
            "https://",
        ],
    )
    def test_invalid_origin_is_rejected(self, origin):
        with pytest.raises(ValidationError):
            settings_without_env_file(cors_allowed_origins=[origin])

    @pytest.mark.parametrize(
        "origin",
        ["https://app.example", "http://localhost:5173", "http://127.0.0.1:5173"],
    )
    def test_exact_origin_is_accepted(self, origin):
        parsed = settings_without_env_file(cors_allowed_origins=[origin])
        assert parsed.cors_allowed_origins == [origin]
