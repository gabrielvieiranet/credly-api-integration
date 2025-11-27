import datetime
from typing import Any, Dict

from clients.credly_client import credly_client
from utils.logger import logger
from utils.s3_writer import s3_writer


class CredlyBadgesService:
    def process(self, mode: str, page: str = None, is_first_page: bool = True) -> dict:
        """
        Processes a single page of badges.

        Args:
            mode: 'historical' or 'daily'
            page: Optional page URL for continuation
            is_first_page: Whether this is the first page (to clear partition)

        Returns:
            dict with:
                - records_processed: int
                - next_page: str | None
        """
        logger.info(
            f"Starting Badges processing in {mode} mode (page={page}, is_first_page={is_first_page})"
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

        # Clear partition only on first page
        if is_first_page:
            s3_writer.clear_partition("badges_emitidas", today)

        # Fetch single page
        items, next_page_url = credly_client.get_badges(params, page_url=page)

        # Process and write
        if items:
            mapped_batch = [self._map_badge(item) for item in items]
            # Use timestamp-based part number to avoid collisions
            part_number = int(datetime.datetime.now().timestamp() * 1000)
            s3_writer.write_parquet("badges_emitidas", mapped_batch, today, part_number)

        return {"records_processed": len(items), "next_page": next_page_url}

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
