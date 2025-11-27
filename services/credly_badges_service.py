import datetime
from typing import Any, Dict

from clients.credly_client import credly_client
from utils.logger import logger
from utils.s3_writer import s3_writer


class CredlyBadgesService:
    def process(self, mode: str, page_limit: int = None):
        """
        Orchestrates fetching and saving badges.
        mode: 'historical' or 'daily'
        page_limit: Optional max number of pages to process
        """
        logger.info(
            f"Starting Badges processing in {mode} mode (page_limit={page_limit})"
        )

        params = {}
        today = datetime.date.today()

        if mode == "daily":
            params["start_date"] = today.strftime("%Y-%m-%d %H:%M:%S")
            params["end_date"] = (today + datetime.timedelta(days=1)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        elif mode == "historical":
            params["start_date"] = "2000-01-01 00:00:00"

        # Clear partition before starting to ensure daily overwrite
        s3_writer.clear_partition("badges_emitidas", today)

        part_number = 1
        pages_processed = 0

        # We will write each batch (page) as a separate parquet file
        # Credly API pagination yields a list of items per page
        for batch in credly_client.get_badges(params):
            if page_limit and pages_processed >= page_limit:
                logger.info(f"Page limit of {page_limit} reached. Stopping.")
                break

            mapped_batch = [self._map_badge(item) for item in batch]

            if mapped_batch:
                s3_writer.write_parquet(
                    "badges_emitidas", mapped_batch, today, part_number
                )
                part_number += 1

            pages_processed += 1

    def _map_badge(self, item: Dict[str, Any]) -> Dict[str, str]:
        """
        Maps API response to flat schema with all fields as strings.
        """

        # Helper to safely get nested fields
        def get_val(d, *keys):
            for k in keys:
                d = d.get(k, {})
            return str(d) if d and not isinstance(d, dict) else ""

        user = item.get("user", {})
        template = item.get("badge_template", {})

        # Organization info from issuer entities
        issuer = item.get("issuer", {})
        entities = issuer.get("entities", [])
        issuer_entity = entities[0] if entities else {}

        return {
            "badge_id": str(item.get("id", "")),
            "issued_to": item.get("issued_to", ""),
            "issued_to_first_name": item.get("issued_to_first_name", ""),
            "issued_to_middle_name": item.get("issued_to_middle_name", ""),
            "issued_to_last_name": item.get("issued_to_last_name", ""),
            "user_id": str(user.get("id", "")),
            "recipient_email": item.get("recipient_email", ""),
            "badge_template_id": str(template.get("id", "")),
            "badge_template_name": template.get("name", ""),
            "image_url": template.get("image_url", ""),
            "locale": item.get("locale", ""),
            "public": str(item.get("public", "")),
            "state": item.get("state", ""),
            "issued_at": item.get("issued_at", ""),
            "expires_at": item.get("expires_at", ""),
            "created_at": item.get("created_at", ""),
            "updated_at": item.get("updated_at", ""),
            "state_updated_at": item.get("state_updated_at", ""),
            "organization_id": str(issuer_entity.get("id", "")),
            "organization_name": issuer_entity.get("name", ""),
        }


credly_badges_service = CredlyBadgesService()
