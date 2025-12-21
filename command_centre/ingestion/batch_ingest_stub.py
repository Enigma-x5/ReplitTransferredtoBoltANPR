"""
Command Centre Batch Ingestion Stub (Phase 8B)

CRITICAL NOTES:
- This is a WRITE-ONLY ingestion stub
- NO data is actually stored
- NO learning occurs
- NO reads occur
- NO connection to databases or storage
- This represents the future interface for daily city batch uploads
- All operations are simulated via logging only

PURPOSE:
Defines the contract for how cities will submit daily batches of HITL-approved
data to the Command Centre for future model training.

WORKFLOW:
1. City uploads daily batch of events with HITL labels
2. Command Centre filters for quality-assured labels only
3. Accepted items would be stored in learning database (stub only)
4. Images would be uploaded to object storage (stub only)
5. Batch metadata would be recorded (stub only)

This stub exists to establish the API contract without implementing
actual infrastructure.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def ingest_daily_batch(batch_payload: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    WRITE-ONLY stub for ingesting daily city batches into Command Centre.

    This function represents Phase 8B: cities uploading HITL-approved data
    for future model training. No actual storage or learning occurs.

    Args:
        batch_payload: List of items, each containing:
            - event_id: Unique identifier for the event
            - license_plate: Detected/corrected license plate text
            - image_path: Reference to image in city's storage
            - label_status: HITL status ("correct", "changed", "unsure", "pending")
            - corrected_plate: Corrected plate if label_status == "changed"
            - camera_id: Source camera identifier
            - timestamp: Event timestamp
            - metadata: Additional event metadata

    Returns:
        Dict containing:
            - accepted_count: Number of items accepted for ingestion
            - rejected_count: Number of items rejected
            - batch_id: Simulated batch identifier
            - status: "simulated" (always, since this is a stub)

    Filter Rules:
        ACCEPT:
            - label_status == "correct"
            - label_status == "changed"

        REJECT:
            - label_status == "unsure"
            - label_status == "pending"
            - Missing HITL status
            - Invalid/missing required fields
    """

    logger.info(f"[STUB] Starting batch ingestion for {len(batch_payload)} items")

    accepted_items = []
    rejected_items = []

    for item in batch_payload:
        label_status = item.get("label_status")

        if not label_status:
            rejected_items.append({
                "item": item,
                "reason": "Missing HITL label_status"
            })
            logger.debug(f"[STUB] Rejected item {item.get('event_id')}: Missing HITL status")
            continue

        if label_status in ["unsure", "pending"]:
            rejected_items.append({
                "item": item,
                "reason": f"Rejected HITL status: {label_status}"
            })
            logger.debug(f"[STUB] Rejected item {item.get('event_id')}: Status={label_status}")
            continue

        if label_status not in ["correct", "changed"]:
            rejected_items.append({
                "item": item,
                "reason": f"Invalid HITL status: {label_status}"
            })
            logger.debug(f"[STUB] Rejected item {item.get('event_id')}: Invalid status={label_status}")
            continue

        if not all(k in item for k in ["event_id", "license_plate", "image_path"]):
            rejected_items.append({
                "item": item,
                "reason": "Missing required fields (event_id, license_plate, or image_path)"
            })
            logger.debug(f"[STUB] Rejected item {item.get('event_id')}: Missing required fields")
            continue

        accepted_items.append(item)
        logger.debug(f"[STUB] Accepted item {item.get('event_id')} with status={label_status}")

    logger.info(f"[STUB] Filtering complete: {len(accepted_items)} accepted, {len(rejected_items)} rejected")

    simulated_batch_id = f"stub_batch_{len(accepted_items)}_items"

    for item in accepted_items:
        event_id = item.get("event_id")
        image_path = item.get("image_path")

        logger.info(f"[STUB] Would upload image: {image_path}")

        logger.info(f"[STUB] Would write metadata for event {event_id} to learning database")

        logger.debug(f"[STUB] Item {event_id}: plate={item.get('license_plate')}, "
                    f"status={item.get('label_status')}, camera={item.get('camera_id')}")

    logger.info(f"[STUB] Would mark batch {simulated_batch_id} as ingested in Command Centre")

    result = {
        "accepted_count": len(accepted_items),
        "rejected_count": len(rejected_items),
        "batch_id": simulated_batch_id,
        "status": "simulated",
        "message": "This is a write-only stub. No actual storage occurred."
    }

    logger.info(f"[STUB] Batch ingestion complete: {result}")

    return result
