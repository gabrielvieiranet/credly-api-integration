import datetime
import hashlib
from typing import Any, Dict

from clients.credly_client import credly_client
from clients.dynamodb_client import dynamodb_client
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

        # Fetch all templates first to calculate hash
        all_templates = []
        params["page_size"] = 100  # Maximize page size for efficiency

        page_url = None
        pages_processed = 0
        part_number = 1

        while True:
            items, next_page_url = credly_client.get_templates(
                params, page_url=page_url
            )

            if items:
                all_templates.extend(items)

            pages_processed += 1

            if page_limit and pages_processed >= page_limit:
                logger.info(f"Page limit of {page_limit} reached. Stopping fetch.")
                break

            if not next_page_url:
                break

            page_url = next_page_url

        # Calculate hash of the current dataset
        # We use ID and updated_at to detect changes
        hash_payload = []
        for t in all_templates:
            hash_payload.append(f"{t.get('id')}-{t.get('updated_at')}")

        hash_payload.sort()  # Ensure consistent order
        current_hash = hashlib.sha256("".join(hash_payload).encode()).hexdigest()

        # Check against stored hash
        metadata = dynamodb_client.get_metadata("badges_templates")
        stored_hash = metadata.get("payload_hash")

        if stored_hash == current_hash:
            logger.info("No changes detected in templates. Skipping ingestion.")
            return {"records_processed": 0, "next_page": None}

        logger.info(
            f"Changes detected (Old: {stored_hash}, New: {current_hash}). Starting full load."
        )

        # Clear partitions
        s3_writer.clear_partition("badges_templates", today)
        s3_writer.clear_partition("badges_templates_activities", today)

        # Process and write data
        # Since we already have all_templates in memory, we can process them directly
        # If memory is a concern for very large datasets, we might need to re-fetch or stream,
        # but for templates (usually thousands, not millions), memory should be fine.

        # Chunk processing to avoid huge parquet files
        chunk_size = 1000
        for i in range(0, len(all_templates), chunk_size):
            chunk = all_templates[i : i + chunk_size]

            mapped_templates = []
            mapped_activities = []

            for item in chunk:
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

        # Update metadata
        dynamodb_client.update_metadata(
            "badges_templates",
            {
                "payload_hash": current_hash,
                "last_updated_at": datetime.datetime.now().isoformat(),
                "record_count": len(all_templates),
            },
        )

        return {"records_processed": len(all_templates), "next_page": None}

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
