"""
Command Centre: Event Ingestion Pipeline

This module will handle ingestion of detection events from all deployed city
clients for centralized learning and analysis.

STATUS: NOT IMPLEMENTED - SKELETON ONLY

CRITICAL ARCHITECTURE PRINCIPLE:
---------------------------------
NO CLIENT-SIDE LEARNING

This module is intended ONLY for the Command Centre infrastructure.
Client deployments must NEVER perform training or model updates.

FUTURE RESPONSIBILITIES:
------------------------
When implemented, this module will:
1. Receive detection events from city clients via secure API
2. Validate and sanitize incoming event data
3. Store events in the centralized data lake
4. Trigger processing pipelines for model training
5. Track data quality and ingestion metrics

DO NOT IMPLEMENT OR USE IN CLIENT CODE.
"""

from typing import Dict, Any, Optional
from datetime import datetime


def ingest_event(
    event_id: str,
    city_id: str,
    camera_id: str,
    license_plate: str,
    confidence: float,
    timestamp: datetime,
    image_data: Optional[bytes] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Ingest a detection event from a city client for centralized processing.

    THIS FUNCTION IS NOT IMPLEMENTED YET.
    THIS MODULE IS NOT ACTIVE IN CLIENT DEPLOYMENTS.

    When implemented in the Command Centre, this function will:
    - Receive detection events from deployed city clients
    - Store events in the centralized data warehouse
    - Prepare data for future training runs
    - Track event metrics and data quality

    Args:
        event_id: Unique identifier for the detection event
        city_id: Identifier of the city/deployment sending the event
        camera_id: Identifier of the camera that captured the event
        license_plate: Detected license plate text
        confidence: Model confidence score (0.0 to 1.0)
        timestamp: When the event occurred
        image_data: Optional image data for the detection
        metadata: Additional event metadata

    Raises:
        NotImplementedError: Always, as this is a skeleton function.

    WARNING:
        DO NOT call this function from client-side code.
        Client deployments must remain inference-only.
        Implementation will happen ONLY in the Command Centre.
    """
    raise NotImplementedError(
        "Command Centre ingestion is not implemented yet. "
        "This function is a skeleton for future Command Centre infrastructure. "
        "NO CLIENT-SIDE LEARNING: All training happens in the Command Centre only."
    )


def ingest_batch_events(events: list[Dict[str, Any]]) -> None:
    """
    Ingest a batch of detection events for efficiency.

    THIS FUNCTION IS NOT IMPLEMENTED YET.
    THIS MODULE IS NOT ACTIVE IN CLIENT DEPLOYMENTS.

    Args:
        events: List of event dictionaries to ingest

    Raises:
        NotImplementedError: Always, as this is a skeleton function.

    WARNING:
        DO NOT call this function from client-side code.
        Implementation will happen ONLY in the Command Centre.
    """
    raise NotImplementedError(
        "Command Centre batch ingestion is not implemented yet. "
        "This function is a skeleton for future Command Centre infrastructure. "
        "NO CLIENT-SIDE LEARNING: All training happens in the Command Centre only."
    )


def validate_event_schema(event: Dict[str, Any]) -> bool:
    """
    Validate that an event conforms to the expected schema.

    THIS FUNCTION IS NOT IMPLEMENTED YET.

    Args:
        event: Event dictionary to validate

    Returns:
        bool: Whether the event is valid

    Raises:
        NotImplementedError: Always, as this is a skeleton function.

    WARNING:
        Implementation will happen ONLY in the Command Centre.
    """
    raise NotImplementedError(
        "Command Centre event validation is not implemented yet. "
        "This is a skeleton for future Command Centre infrastructure."
    )
