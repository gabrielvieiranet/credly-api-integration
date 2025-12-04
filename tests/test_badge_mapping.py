import pytest
from src.services.credly_badges_service import CredlyBadgesService


@pytest.fixture
def service():
    return CredlyBadgesService()


def test_map_badge_complete(service):
    """Test complete badge mapping"""
    item = {
        "id": 123,
        "issued_to": "John Doe",
        "issued_to_first_name": "John",
        "issued_to_middle_name": "M",
        "issued_to_last_name": "Doe",
        "user": {"id": 999},
        "recipient_email": "john@example.com",
        "badge_template": {"id": 55, "name": "Best Badge", "image_url": "http://img"},
        "locale": "en",
        "public": True,
        "state": "accepted",
        "issued_at": "2023-01-01",
        "expires_at": "2024-01-01",
        "created_at": "2022-12-01",
        "updated_at": "2023-01-02",
        "state_updated_at": "2023-01-01",
        "issuer": {"entities": [{"id": 1, "name": "Acme"}]},
    }

    result = service._map_badge(item)

    assert result["badge_id"] == "123"
    assert result["issued_to"] == "John Doe"
    assert result["issued_to_first_name"] == "John"
    assert result["issued_to_middle_name"] == "M"
    assert result["issued_to_last_name"] == "Doe"
    assert result["user_id"] == "999"
    assert result["recipient_email"] == "john@example.com"
    assert result["badge_template_id"] == "55"
    assert result["badge_template_name"] == "Best Badge"
    assert result["image_url"] == "http://img"
    assert result["locale"] == "en"
    assert result["public"] == "True"
    assert result["state"] == "accepted"
    assert result["organization_id"] == "1"
    assert result["organization_name"] == "Acme"


def test_map_badge_minimal(service):
    """Test badge mapping with minimal data"""
    item = {
        "id": 456,
        "issued_to": "Jane",
        "user": {},
        "badge_template": {},
        "issuer": {"entities": []},
    }

    result = service._map_badge(item)

    assert result["badge_id"] == "456"
    assert result["issued_to"] == "Jane"
    assert result["user_id"] == ""
    assert result["organization_name"] == ""


def test_map_badge_no_issuer_entities(service):
    """Test badge mapping without issuer entities"""
    item = {
        "id": 789,
        "issued_to": "Bob",
        "user": {"id": 111},
        "badge_template": {"id": 22, "name": "Badge"},
        "issuer": {},
    }

    result = service._map_badge(item)

    assert result["badge_id"] == "789"
    assert result["organization_id"] == ""
