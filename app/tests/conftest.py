import os
import sys

import pytest

# Add app directory to sys.path so 'src' module can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("ENV", "DEV")
    monkeypatch.setenv("SECRETS_MANAGER_KEY", "test/secret")
    monkeypatch.setenv("API_BASE_URL", "https://api.test.com")


@pytest.fixture
def mock_secrets_client(mocker):
    mock = mocker.patch("src.clients.secrets_manager.secrets_client")
    mock.get_secret.return_value = {"api_token": "static_test_token"}
    return mock


@pytest.fixture
def mock_http_client(mocker):
    return mocker.patch("src.clients.http_client.http_client")


@pytest.fixture
def mock_boto3_client(mocker):
    """Mock boto3 client to prevent actual AWS calls"""
    mock_client = mocker.patch("boto3.client")
    mock_resource = mocker.patch("boto3.resource")
    return mock_client, mock_resource
