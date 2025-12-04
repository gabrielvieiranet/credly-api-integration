import json
import logging
import sys

from src.config.settings import settings


class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "level": record.levelname,
            "message": record.getMessage(),
            "timestamp": self.formatTime(record, self.datefmt),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "correlation_id"):
            log_record["correlation_id"] = record.correlation_id

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL)

    # Prevent adding multiple handlers if logger is already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = JsonFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logger("app")
