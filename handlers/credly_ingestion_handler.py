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
        "mode": "historical" | "daily"
    }
    """
    logger.info("Credly Ingestion Lambda started", extra={"event": event})

    load_type = event.get("load_type")
    mode = event.get("mode", "daily")
    page_limit = event.get("page_limit")  # Optional page limit

    if not load_type:
        raise ValueError("Missing 'load_type' in event")

    try:
        observability.start_segment(f"ingest_{load_type}")

        if load_type == "badges":
            credly_badges_service.process(mode, page_limit=page_limit)
        elif load_type == "templates":
            credly_templates_service.process(mode, page_limit=page_limit)
        else:
            raise ValueError(f"Unknown load_type: {load_type}")

        observability.end_segment(f"ingest_{load_type}")

        return {
            "statusCode": 200,
            "body": {"message": f"Successfully processed {load_type} in {mode} mode"},
        }

    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}", exc_info=True)
        observability.increment_metric("ingestion_failed", tags={"type": load_type})
        raise e
