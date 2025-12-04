import pytest
from src.services.credly_badges_service import CredlyBadgesService
from src.services.credly_templates_service import CredlyTemplatesService


@pytest.fixture
def mock_credly_client(mocker):
    return mocker.patch("src.services.credly_badges_service.credly_client")


@pytest.fixture
def mock_credly_client_templates(mocker):
    return mocker.patch("src.services.credly_templates_service.credly_client")


@pytest.fixture
def mock_s3_writer(mocker):
    return mocker.patch("src.services.credly_badges_service.s3_writer")


@pytest.fixture
def mock_s3_writer_templates(mocker):
    return mocker.patch("src.services.credly_templates_service.s3_writer")


@pytest.fixture
def mock_dynamodb_client(mocker):
    return mocker.patch("src.services.credly_templates_service.dynamodb_client")


def test_badges_mapping(mock_credly_client, mock_s3_writer, mocker):
    # Mock DynamoDB to avoid actual calls
    mock_dynamodb = mocker.patch("src.clients.dynamodb_client.dynamodb_client")
    mock_dynamodb.get_metadata.return_value = {}  # No watermark

    # Mock data
    mock_data = [
        {
            "id": 123,
            "issued_to": "John Doe",
            "user": {"id": 999, "url": "http://user"},
            "badge_template": {"id": 55, "name": "Best Badge"},
            "issuer": {"entities": [{"id": 1, "name": "Acme"}]},
            "issued_at": "2023-01-01",
        }
    ]
    # Return tuple: (items, next_page_url)
    mock_credly_client.get_badges.return_value = (mock_data, None)

    service = CredlyBadgesService()
    service.process("daily")

    # Verify S3 write
    mock_s3_writer.write_parquet.assert_called()
    args, _ = mock_s3_writer.write_parquet.call_args
    table_name, data, _, _ = args

    assert table_name == "badges_emitidas"
    assert len(data) == 1
    item = data[0]
    assert item["badge_id"] == "123"
    assert item["user_id"] == "999"
    assert item["badge_template_name"] == "Best Badge"
    assert item["organization_name"] == "Acme"


def test_templates_hash_validation(
    mock_credly_client_templates, mock_s3_writer_templates, mock_dynamodb_client
):
    mock_data = [
        {
            "id": 100,
            "name": "Template 1",
            "updated_at": "2023-01-01T00:00:00",
            "skills": [{"name": "Python"}, {"name": "AWS"}],
            "owner": {"id": 1, "name": "Org"},
            "badge_template_activities": [{"id": "a1", "title": "Activity 1"}],
        }
    ]
    # Return tuple: (items, next_page_url)
    mock_credly_client_templates.get_templates.return_value = (mock_data, None)

    # Case 1: Hash mismatch (should write)
    mock_dynamodb_client.get_metadata.return_value = {"payload_hash": "old_hash"}

    service = CredlyTemplatesService()
    result = service.process("daily")

    # Check calls
    assert mock_s3_writer_templates.write_parquet.call_count >= 2
    mock_dynamodb_client.update_metadata.assert_called_once()

    # Verify update metadata call
    args, _ = mock_dynamodb_client.update_metadata.call_args
    assert args[0] == "badges_templates"
    assert "payload_hash" in args[1]
    assert result["records_processed"] == 1

    # Case 2: Hash match (should skip)
    # Calculate expected hash for mock data
    import hashlib

    expected_hash = hashlib.sha256("100-2023-01-01T00:00:00".encode()).hexdigest()

    mock_dynamodb_client.get_metadata.return_value = {"payload_hash": expected_hash}
    mock_s3_writer_templates.reset_mock()
    mock_dynamodb_client.reset_mock()

    result = service.process("daily")

    # Should NOT write to S3 or update DynamoDB
    mock_s3_writer_templates.write_parquet.assert_not_called()
    mock_dynamodb_client.update_metadata.assert_not_called()
    assert result["records_processed"] == 0
