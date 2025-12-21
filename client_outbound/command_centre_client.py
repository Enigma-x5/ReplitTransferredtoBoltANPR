"""
Command Centre Client Interface

ONE-WAY outbound interface for client deployments to send data TO the
Command Centre.

CRITICAL ARCHITECTURE:
----------------------
CLIENT ➜ COMMAND CENTRE (ONE-WAY ONLY)

This interface allows clients to:
- Send detection events for aggregation
- Send human-in-the-loop corrections for training
- Report system health and metrics

This interface NEVER allows clients to:
- Receive model updates (models are deployed through separate channels)
- Receive training data
- Receive inference results from the Command Centre
- Perform any learning or training locally

STATUS: NOT IMPLEMENTED - SKELETON ONLY

This module defines the interface but contains no active networking,
API calls, or communication logic.

WARNING:
--------
CLIENT DEPLOYMENTS MUST REMAIN INFERENCE ONLY

- Clients NEVER receive intelligence back from Command Centre
- Clients NEVER perform learning or training locally
- All model training happens exclusively in the Command Centre
- Model deployment happens through separate, controlled channels

DO NOT implement bi-directional communication.
DO NOT add training logic to client code.
DO NOT bypass the inference-only policy.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class OutboundMessageType(Enum):
    """Types of messages that can be sent to Command Centre."""
    DETECTION_EVENT = "detection_event"
    HITL_LABEL = "hitl_label"
    SYSTEM_HEALTH = "system_health"
    ERROR_REPORT = "error_report"


def send_event(
    event_id: str,
    city_id: str,
    camera_id: str,
    license_plate: str,
    confidence: float,
    timestamp: datetime,
    image_path: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Send a detection event to the Command Centre for aggregation and analysis.

    THIS FUNCTION IS NOT IMPLEMENTED YET.
    THIS MODULE IS NOT ACTIVE IN CLIENT DEPLOYMENTS.

    ONE-WAY COMMUNICATION ONLY:
    - Client sends detection event TO Command Centre
    - Client NEVER receives intelligence back
    - Client NEVER performs training

    When implemented, this function will:
    - Serialize the detection event
    - Send it to Command Centre via secure API
    - Handle network failures gracefully (queue for retry)
    - NOT wait for or process any intelligence response

    Args:
        event_id: Unique identifier for the detection event
        city_id: Identifier of this city/deployment
        camera_id: Identifier of the camera that captured the event
        license_plate: Detected license plate text
        confidence: Model confidence score (0.0 to 1.0)
        timestamp: When the event occurred
        image_path: Optional path to the detection image
        metadata: Additional event metadata

    Raises:
        NotImplementedError: Always, as this is a skeleton function.

    WARNING:
        DO NOT implement bi-directional communication.
        Client must remain inference-only.
        Implementation will happen ONLY when Command Centre is operational.
    """
    raise NotImplementedError(
        "Command Centre client interface is not implemented yet. "
        "This function is a skeleton for future one-way outbound communication. "
        "CLIENT ➜ COMMAND CENTRE ONLY: Clients never receive intelligence back."
    )


def send_label(
    event_id: str,
    city_id: str,
    user_id: str,
    corrected_plate: str,
    original_plate: str,
    label_type: str,
    timestamp: datetime,
    confidence_override: Optional[float] = None,
    notes: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Send a human-in-the-loop label/correction to the Command Centre.

    THIS FUNCTION IS NOT IMPLEMENTED YET.
    THIS MODULE IS NOT ACTIVE IN CLIENT DEPLOYMENTS.

    ONE-WAY COMMUNICATION ONLY:
    - Client sends human correction TO Command Centre
    - Command Centre aggregates corrections for training
    - Client NEVER receives model updates through this interface
    - Client NEVER performs training locally

    When implemented, this function will:
    - Serialize the human label/correction
    - Send it to Command Centre via secure API
    - Handle network failures gracefully (queue for retry)
    - NOT wait for or process any training results

    Args:
        event_id: ID of the detection event being corrected
        city_id: Identifier of this city/deployment
        user_id: Identifier of the user who provided the label
        corrected_plate: The corrected license plate text
        original_plate: The original detected license plate text
        label_type: Type of label (correction, confirmation, rejection)
        timestamp: When the label was provided
        confidence_override: Optional user confidence rating
        notes: Optional notes from the user
        metadata: Additional label metadata

    Raises:
        NotImplementedError: Always, as this is a skeleton function.

    WARNING:
        DO NOT implement bi-directional communication.
        Client must remain inference-only.
        All training happens in the Command Centre.
        Implementation will happen ONLY when Command Centre is operational.
    """
    raise NotImplementedError(
        "Command Centre client interface is not implemented yet. "
        "This function is a skeleton for future one-way outbound communication. "
        "CLIENT ➜ COMMAND CENTRE ONLY: Clients never receive intelligence back."
    )


def send_health_metrics(
    city_id: str,
    metrics: Dict[str, Any],
    timestamp: datetime
) -> None:
    """
    Send system health metrics to the Command Centre for monitoring.

    THIS FUNCTION IS NOT IMPLEMENTED YET.

    ONE-WAY COMMUNICATION ONLY:
    - Client sends health metrics TO Command Centre
    - Client NEVER receives configuration changes back

    Args:
        city_id: Identifier of this city/deployment
        metrics: System health and performance metrics
        timestamp: When metrics were collected

    Raises:
        NotImplementedError: Always, as this is a skeleton function.

    WARNING:
        Implementation will happen ONLY when Command Centre is operational.
    """
    raise NotImplementedError(
        "Command Centre client interface is not implemented yet. "
        "This is a skeleton for future one-way outbound communication."
    )


def get_client_info() -> Dict[str, Any]:
    """
    Get information about this client interface configuration.

    Returns:
        dict: Client interface status and configuration.
    """
    return {
        "status": "not_implemented",
        "version": "0.0.0",
        "communication_mode": "one_way_outbound_only",
        "direction": "client_to_command_centre",
        "client_policy": "inference_only",
        "warning": "Client never receives intelligence back. All training happens in Command Centre."
    }
