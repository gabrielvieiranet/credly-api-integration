import datetime
from typing import Any, Dict, List

from clients.credly_client import credly_client
from utils.logger import logger
from utils.s3_writer import s3_writer


class CredlyTemplatesService:
    def process(self, mode: str, page_limit: int = None):
        """
        Orchestrates fetching and saving templates.
        """
        logger.info(
            f"Starting Templates processing in {mode} mode (page_limit={page_limit})"
        )

        params = {}
        today = datetime.date.today()

        # Clear partitions
        s3_writer.clear_partition("badges_templates", today)
        s3_writer.clear_partition("badges_templates_activities", today)

        part_number = 1
        pages_processed = 0

        for batch in credly_client.get_templates(params):
            if page_limit and pages_processed >= page_limit:
                logger.info(f"Page limit of {page_limit} reached. Stopping.")
                break

            mapped_templates = []
            mapped_activities = []

            for item in batch:
                mapped_templates.append(self._map_template(item))
                mapped_activities.extend(self._extract_activities(item))

            if mapped_templates:
                s3_writer.write_parquet(
                    "badges_templates", mapped_templates, today, part_number
                )

            if mapped_activities:
                s3_writer.write_parquet(
                    "badges_templates_activities", mapped_activities, today, part_number
                )

            part_number += 1
            pages_processed += 1

    def _map_template(self, item: Dict[str, Any]) -> Dict[str, str]:
        owner = item.get("owner", {})
        skills = item.get("skills", [])
        # Skills can be a list of strings or objects depending on API version/response
        skills_list = []
        for s in skills:
            if isinstance(s, dict):
                skills_list.append(s.get("name", ""))
            elif isinstance(s, str):
                skills_list.append(s)
            else:
                skills_list.append(str(s))

        skills_str = ";".join(skills_list) if skills_list else ""

        return {
            "badge_template_id": str(item.get("id", "")),
            "primary_badge_template_id": str(item.get("primary_badge_template_id", "")),
            "variant_name": item.get("variant_name", ""),
            "name": item.get("name", ""),
            "description": item.get("description", ""),
            "state": item.get("state", ""),
            "public": str(item.get("public", "")),
            "badges_count": str(item.get("badges_count", "")),
            "image_url": item.get("image_url", ""),
            "url": item.get("url", ""),
            "vanity_slug": item.get("vanity_slug", ""),
            "variants_allowed": str(item.get("variants_allowed", "")),
            "variant_type": item.get("variant_type", ""),
            "level": item.get("level", ""),
            "type_category": item.get("type_category", ""),
            "skills": skills_str,
            "reporting_tags": str(item.get("reporting_tags", "")),
            "state_updated_at": item.get("state_updated_at", ""),
            "created_at": item.get("created_at", ""),
            "updated_at": item.get("updated_at", ""),
            "organization_id": str(owner.get("id", "")),
            "organization_name": owner.get("name", ""),
            "organization_vanity_url": owner.get("vanity_url", ""),
        }

    def _extract_activities(self, item: dict[str, Any]) -> list[dict[str, str]]:
        activities = item.get("badge_template_activities", [])
        results = []
        template_id = str(item.get("id", ""))

        for act in activities:
            results.append(
                {
                    "badge_template_id": template_id,
                    "badge_template_activity_id": str(act.get("id", "")),
                    "badge_template_activity_title": act.get("title", ""),
                    "badge_template_activity_type": act.get("activity_type", ""),
                    "badge_template_activity_url": act.get("url", ""),
                }
            )
        return results


credly_templates_service = CredlyTemplatesService()
