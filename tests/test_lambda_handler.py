from unittest.mock import MagicMock

import pytest
from lambda_function import lambda_handler


@pytest.fixture
def mock_badges_service(mocker):
    return mocker.patch("lambda_function.credly_badges_service")


@pytest.fixture
def mock_templates_service(mocker):
    return mocker.patch("lambda_function.credly_templates_service")


def test_lambda_handler_badges_success(mock_badges_service):
    """Test successful badges processing"""
    mock_badges_service.process.return_value = {
        "records_processed": 100,
        "next_page": None,
    }

    event = {"load_type": "badges", "mode": "daily"}
    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    assert result["body"]["records_processed"] == 100
    assert result["body"]["next_page"] is None
    mock_badges_service.process.assert_called_once_with(
        "daily", page=None, is_first_page=True
    )


def test_lambda_handler_badges_with_page(mock_badges_service):
    """Test badges processing with pagination"""
    mock_badges_service.process.return_value = {
        "records_processed": 50,
        "next_page": "http://next-page",
    }

    event = {"load_type": "badges", "mode": "historical", "page": "http://current-page"}
    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    assert result["body"]["next_page"] == "http://next-page"
    mock_badges_service.process.assert_called_once_with(
        "historical", page="http://current-page", is_first_page=False
    )


def test_lambda_handler_templates_success(mock_templates_service):
    """Test successful templates processing"""
    mock_templates_service.process.return_value = {
        "records_processed": 25,
        "next_page": None,
    }

    event = {"load_type": "templates", "mode": "daily"}
    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    assert result["body"]["records_processed"] == 25
    mock_templates_service.process.assert_called_once_with("daily")


def test_lambda_handler_missing_load_type():
    """Test error when load_type is missing"""
    event = {"mode": "daily"}

    with pytest.raises(ValueError, match="Missing 'load_type' in event"):
        lambda_handler(event, None)


def test_lambda_handler_unknown_load_type(mock_badges_service, mock_templates_service):
    """Test error with unknown load_type"""
    event = {"load_type": "unknown", "mode": "daily"}

    with pytest.raises(ValueError, match="Unknown load_type: unknown"):
        lambda_handler(event, None)


def test_lambda_handler_service_exception(mock_badges_service):
    """Test error handling when service raises exception"""
    mock_badges_service.process.side_effect = RuntimeError("API Error")

    event = {"load_type": "badges", "mode": "daily"}

    with pytest.raises(RuntimeError, match="API Error"):
        lambda_handler(event, None)
