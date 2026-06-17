"""Endpoint tests for the users router."""
# Test names describe the scenario; per-test docstrings would be redundant.
# pylint: disable=missing-function-docstring,redefined-outer-name
import pytest


@pytest.fixture
def user_data():
    """User payloads owned by this module so the endpoint tests stay
    independent of other test files' data."""
    return {
        "all_fields_correct": {
            "username": "mustermann",
            "email": "max.mustermann@example.com",
            "password": "SomeNumbers-84927#",
        },
        "invalid_email": {
            "username": "mustermann",
            "email": "not-an-email",
            "password": "SomeNumbers-84927#",
        },
    }


def test_create_user_returns_201_without_password_hash(client, user_data):
    user = user_data["all_fields_correct"]
    response = client.post("/users", json=user)

    assert response.status_code == 201
    body = response.json()
    # The response_model (UserRead) must not leak the hash.
    assert "password_hash" not in body
    assert body["username"] == user["username"]
    assert body["email"] == user["email"]


def test_create_user_rejects_invalid_email(client, user_data):
    response = client.post("/users", json=user_data["invalid_email"])

    assert response.status_code == 422
