from typing import Any, Dict

from services.credly_badges_service import credly_badges_service
from services.credly_templates_service import credly_templates_service
from utils.logger import logger
from utils.observability import observability


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Entrypoint for Credly Ingestion.
    Event payload:
    {
        "load_type": "badges" | "templates",
        "mode": "historical" | "daily",
        "page": optional page URL for continuation (badges only)
    }
    """
    logger.info("Credly Ingestion Lambda started", extra={"event": event})

    load_type = event.get("load_type")
    mode = event.get("mode", "daily")
    page = event.get("page")  # Optional page URL for continuation

    if not load_type:
        raise ValueError("Missing 'load_type' in event")

    try:
        observability.start_segment(f"ingest_{load_type}")

        result = {}
        if load_type == "badges":
            # Determine if first page based on presence of page parameter
            is_first_page = page is None
            result = credly_badges_service.process(
                mode, page=page, is_first_page=is_first_page
            )
        elif load_type == "templates":
            # Templates still process all pages internally for hash validation
            # TODO: Refactor templates to support pagination
            credly_templates_service.process(mode)
            result = {"records_processed": 0, "next_page": None}
        else:
            raise ValueError(f"Unknown load_type: {load_type}")

        observability.end_segment(f"ingest_{load_type}")

        return {
            "statusCode": 200,
            "body": {
                "message": f"Successfully processed {load_type} in {mode} mode",
                "records_processed": result.get("records_processed", 0),
                "next_page": result.get("next_page"),
            },
        }

    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}", exc_info=True)
        observability.increment_metric("ingestion_failed", tags={"type": load_type})
        raise e
