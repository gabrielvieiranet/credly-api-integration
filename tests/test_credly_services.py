from unittest.mock import MagicMock, call

import pytest

from services.credly_badges_service import CredlyBadgesService
from services.credly_templates_service import CredlyTemplatesService


@pytest.fixture
def mock_credly_client(mocker):
    return mocker.patch("services.credly_badges_service.credly_client")


@pytest.fixture
def mock_credly_client_templates(mocker):
    return mocker.patch("services.credly_templates_service.credly_client")


@pytest.fixture
def mock_s3_writer(mocker):
    return mocker.patch("services.credly_badges_service.s3_writer")


@pytest.fixture
def mock_s3_writer_templates(mocker):
    return mocker.patch("services.credly_templates_service.s3_writer")


def test_badges_mapping(mock_credly_client, mock_s3_writer):
    # Mock data
    mock_data = [
        {
            "id": 123,
            "issued_to": "John Doe",
            "user": {"id": 999, "url": "http://user"},
            "badge_template": {"id": 55, "name": "Best Badge"},
            "organization": {"id": 1, "name": "Acme"},
            "issued_at": "2023-01-01",
        }
    ]
    mock_credly_client.get_badges.return_value = [mock_data]

    service = CredlyBadgesService()
    service.process("daily")

    # Verify S3 write
    mock_s3_writer.write_json.assert_called()
    args, _ = mock_s3_writer.write_json.call_args
    table_name, data, _ = args

    assert table_name == "badges_emitidas"
    assert len(data) == 1
    item = data[0]
    assert item["badge_id"] == "123"
    assert item["user_id"] == "999"
    assert item["badge_template_name"] == "Best Badge"
    assert item["organization_name"] == "Acme"


def test_templates_flattening(mock_credly_client_templates, mock_s3_writer_templates):
    mock_data = [
        {
            "id": 100,
            "name": "Template 1",
            "skills": [{"name": "Python"}, {"name": "AWS"}],
            "badge_template_activities": [{"id": "a1", "title": "Activity 1"}],
        }
    ]
    mock_credly_client_templates.get_templates.return_value = [mock_data]

    service = CredlyTemplatesService()
    service.process("daily")

    # Check calls
    assert mock_s3_writer_templates.write_json.call_count >= 2

    # Inspect calls to ensure both tables were written
    calls = mock_s3_writer_templates.write_json.call_args_list
    tables_written = [c[0][0] for c in calls]
    assert "badges_templates" in tables_written
    assert "badges_templates_activities" in tables_written

    # Check flattening of skills
    # Find the call for templates
    for args, _ in calls:
        if args[0] == "badges_templates":
            item = args[1][0]
            assert item["skills"] == "Python;AWS"
            assert item["badge_template_id"] == "100"
