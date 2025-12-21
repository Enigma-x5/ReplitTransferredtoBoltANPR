"""
Label Schema - Human-in-the-Loop Label Data Contract

SCHEMA ONLY - NO LOGIC ALLOWED

This module defines the structure of human corrections/labels received BY the
Command Centre FROM client deployments.

CRITICAL ARCHITECTURE:
----------------------
CLIENT ➜ COMMAND CENTRE (ONE-WAY INBOUND)

- Command Centre receives human labels/corrections from clients
- Labels are aggregated for future model training
- No learning occurs here yet (this is schema only)
- This defines expected inbound label payloads from clients
- Model distribution will be PUSH-ONLY in the future (separate channel)
- Clients never receive model updates through this interface

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

from typing import Optional, Dict, Any, Literal


# Type alias for label status values
LabelStatus = Literal["correct", "changed", "unsure"]


class HumanLabelSchema:
    """
    Human-in-the-loop label payload received from client deployments.

    SCHEMA ONLY - NO VALIDATION OR LOGIC

    Represents a human correction or confirmation of a detection event.
    These labels are received from clients and aggregated by the Command
    Centre for future model training. No training occurs on the client.

    Attributes:
        event_id: ID of the detection event being labeled
        corrected_plate: The corrected license plate text (None if no plate)
        label_status: Type of human action taken
        labeled_at: When the human provided this label (ISO 8601 format)
        metadata: Optional metadata about the labeling action
    """

    # Type annotations only - NO implementation
    event_id: str  # References a previously sent detection event
    corrected_plate: Optional[str]  # None if no plate present
    label_status: LabelStatus  # "correct" | "changed" | "unsure"
    labeled_at: str  # ISO 8601 format: "2024-01-15T14:35:00Z"
    metadata: Optional[Dict[str, Any]]  # Optional additional context


class HumanLabelMetadata:
    """
    Optional metadata for human labels.

    SCHEMA ONLY - NO VALIDATION OR LOGIC

    Additional context about the labeling action that may be useful for
    quality analysis and training.

    Attributes:
        user_id: ID of the user who provided the label
        labeling_duration_seconds: Time taken to provide the label
        notes: Optional notes from the human operator
        original_plate_text: Original detected text for reference
        original_confidence: Original confidence score for reference
    """

    # Type annotations only - NO implementation
    user_id: Optional[str]
    labeling_duration_seconds: Optional[float]
    notes: Optional[str]
    original_plate_text: Optional[str]
    original_confidence: Optional[float]


"""
REMINDER: This is a schema-only file.

- No validation logic
- No runtime behavior
- No learning or training implementation
- Defines expected inbound label payloads from clients
- Model distribution will be PUSH-ONLY in future (separate channel)
- Clients do not learn from labels
- No model updates sent to clients through this interface
- All training happens in Command Centre only
- This file only documents the data contract
"""
