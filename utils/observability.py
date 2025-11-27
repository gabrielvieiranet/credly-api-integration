from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from utils.logger import logger


class ObservabilityProvider(ABC):
    """
    Abstract base class for observability (metrics and tracing).
    This allows us to plug in Datadog or other providers later.
    """

    @abstractmethod
    def increment_metric(
        self, metric_name: str, tags: Optional[Dict[str, str]] = None, value: int = 1
    ):
        pass

    @abstractmethod
    def record_gauge(
        self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
    ):
        pass

    @abstractmethod
    def start_segment(self, name: str):
        """Start a tracing segment."""
        pass

    @abstractmethod
    def end_segment(self, segment):
        """End a tracing segment."""
        pass


class NoOpObservabilityProvider(ObservabilityProvider):
    """
    Default implementation that logs metrics instead of sending them.
    Useful for local development or when Datadog is not yet configured.
    """

    def increment_metric(
        self, metric_name: str, tags: Optional[Dict[str, str]] = None, value: int = 1
    ):
        logger.debug(f"Metric Increment: {metric_name} +{value} Tags: {tags}")

    def record_gauge(
        self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
    ):
        logger.debug(f"Metric Gauge: {metric_name} = {value} Tags: {tags}")

    def start_segment(self, name: str):
        logger.debug(f"Start Trace Segment: {name}")
        return name

    def end_segment(self, segment):
        logger.debug(f"End Trace Segment: {segment}")


# Global instance
observability = NoOpObservabilityProvider()
