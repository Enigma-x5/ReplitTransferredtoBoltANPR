"""
Event Schema - Detection Event Data Contract

SCHEMA ONLY - NO LOGIC ALLOWED

This module defines the structure of detection events received BY the Command
Centre FROM client deployments.

CRITICAL ARCHITECTURE:
----------------------
CLIENT ➜ COMMAND CENTRE (ONE-WAY INBOUND)

- Command Centre receives detection events from clients
- Events are aggregated for analysis and training
- No learning occurs here yet (this is schema only)
- This defines expected inbound payloads from clients
- Model distribution will be PUSH-ONLY in the future (separate channel)

This is a pure data contract with no validation, logic, or runtime behavior.

DO NOT:
- Add validation logic
- Add runtime behavior
- Import pydantic, dataclasses, or validation libraries
- Implement model training here
- Add model distribution logic
- Add bi-directional communication

NOTE: Do NOT import pydantic or other validation libraries.
This is a pure schema definition only.
"""

from typing import Optional, Dict, Any


class DetectionEventSchema:
    """
    Detection event payload received from client deployments.

    SCHEMA ONLY - NO VALIDATION OR LOGIC

    Represents a single license plate detection event captured by a client
    deployment camera and sent to the Command Centre for aggregation.

    Attributes:
        event_id: Unique identifier for this detection event
        camera_id: Identifier of the camera that captured this event
        city_id: Identifier of the city/deployment sending this event
        timestamp: When the detection occurred (ISO 8601 format)
        plate_text: Detected license plate text (None if detection failed)
        confidence: Model confidence score (0.0 to 1.0)
        metadata: Optional metadata about the detection
    """

    # Type annotations only - NO implementation
    event_id: str
    camera_id: str
    city_id: str
    timestamp: str  # ISO 8601 format: "2024-01-15T14:30:00Z"
    plate_text: Optional[str]  # None if detection failed
    confidence: float  # 0.0 to 1.0
    metadata: Optional[Dict[str, Any]]  # Optional additional context


class DetectionEventMetadata:
    """
    Optional metadata for detection events.

    SCHEMA ONLY - NO VALIDATION OR LOGIC

    Additional context about the detection that may be useful for
    analysis and training.

    Attributes:
        image_width: Image width in pixels if available
        image_height: Image height in pixels if available
        bbox: Bounding box coordinates if available
        model_version: Model version used for this detection
    """

    # Type annotations only - NO implementation
    image_width: Optional[int]
    image_height: Optional[int]
    bbox: Optional[Dict[str, float]]  # {x, y, width, height}
    model_version: Optional[str]


"""
REMINDER: This is a schema-only file.

- No validation logic
- No runtime behavior
- No learning or training implementation
- Defines expected inbound payloads from clients
- Model distribution will be PUSH-ONLY in future (separate channel)
- This file only documents the data contract
"""
