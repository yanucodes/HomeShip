"""Endpoint tests for the users router."""
# Test names describe the scenario; per-test docstrings would be redundant.
# pylint: disable=missing-function-docstring,redefined-outer-name


def test_create_user_returns_201_without_password_hash(client, test_user_data):
    user = test_user_data["all_fields_correct"]
    response = client.post("/users", json=user)

    assert response.status_code == 201
    body = response.json()
    # The response_model (UserRead) must not leak the hash.
    assert "password_hash" not in body
    assert body["username"] == user["username"]
    assert body["email"] == user["email"]


def test_create_user_rejects_invalid_email(client, test_user_data):
    response = client.post("/users", json=test_user_data["invalid_email"])

    assert response.status_code == 422
