import os
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("ENV", "DEV")
    monkeypatch.setenv("SECRETS_MANAGER_KEY", "test/secret")
    monkeypatch.setenv("API_BASE_URL", "https://api.test.com")


@pytest.fixture
def mock_secrets_client(mocker):
    mock = mocker.patch("clients.secrets_manager.secrets_client")
    mock.get_secret.return_value = {"api_token": "static_test_token"}
    return mock


@pytest.fixture
def mock_http_client(mocker):
    return mocker.patch("clients.http_client.http_client")
