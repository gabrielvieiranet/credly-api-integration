import pytest
from src.services.credly_templates_service import CredlyTemplatesService


@pytest.fixture
def service():
    return CredlyTemplatesService()


def test_map_template_basic(service):
    """Test basic template mapping"""
    item = {
        "id": 100,
        "primary_badge_template_id": "",
        "variant_name": "",
        "name": "Python Expert",
        "description": "Advanced Python skills",
        "state": "active",
        "public": True,
        "badges_count": 50,
        "image_url": "http://image.png",
        "url": "http://template.url",
        "vanity_slug": "python-expert",
        "variants_allowed": False,
        "variant_type": "",
        "level": "advanced",
        "type_category": "certification",
        "skills": ["Python", "AWS"],
        "reporting_tags": "",
        "state_updated_at": "2023-01-01",
        "created_at": "2022-01-01",
        "updated_at": "2023-06-01",
        "owner": {"id": 1, "name": "Org1", "vanity_url": "http://org1"},
    }

    result = service._map_template(item)

    assert result["badge_template_id"] == "100"
    assert result["name"] == "Python Expert"
    assert result["description"] == "Advanced Python skills"
    assert result["state"] == "active"
    assert result["public"] == "True"
    assert result["badges_count"] == "50"
    assert result["skills"] == "Python;AWS"
    assert result["organization_id"] == "1"
    assert result["organization_name"] == "Org1"


def test_map_template_with_skill_objects(service):
    """Test template mapping with skill objects"""
    item = {
        "id": 101,
        "name": "AWS Expert",
        "skills": [{"name": "EC2"}, {"name": "S3"}],
        "owner": {"id": 2, "name": "AWS"},
        "created_at": "",
        "updated_at": "",
        "state_updated_at": "",
    }

    result = service._map_template(item)

    assert result["skills"] == "EC2;S3"


def test_extract_activities(service):
    """Test activities extraction"""
    item = {
        "id": 100,
        "badge_template_activities": [
            {
                "id": "a1",
                "title": "Complete Course",
                "activity_type": "course",
                "url": "http://course1",
            },
            {
                "id": "a2",
                "title": "Pass Quiz",
                "activity_type": "quiz",
                "url": "http://quiz1",
            },
        ],
    }

    result = service._extract_activities(item)

    assert len(result) == 2
    assert result[0]["badge_template_id"] == "100"
    assert result[0]["badge_template_activity_id"] == "a1"
    assert result[0]["badge_template_activity_title"] == "Complete Course"
    assert result[1]["badge_template_activity_id"] == "a2"


def test_extract_activities_empty(service):
    """Test activities extraction with no activities"""
    item = {"id": 100, "badge_template_activities": []}

    result = service._extract_activities(item)

    assert len(result) == 0
