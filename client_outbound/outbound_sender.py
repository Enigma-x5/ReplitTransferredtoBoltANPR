"""
Client-Side Outbound Data Sender Stub

STUB ONLY - NO REAL NETWORKING

This module simulates the automatic, daily push of events and labels from the
client to the Command Centre. It is a STUB implementation with no real networking.

CRITICAL ARCHITECTURE:
----------------------
- Client automatically pushes data (no human approval required)
- Push happens once per day (simulated)
- Data is sent only once (no duplicates)
- NO intelligence or learning occurs here
- NO data is pulled or received from Command Centre
- NO model updates happen on the client
- This is pure outbound data transmission only

STUB BEHAVIOR:
--------------
- Uses in-memory tracking only (does NOT persist across restarts)
- Logs to console instead of real HTTP calls
- Simulates marking items as "sent"
- Real networking will be added later
- Real persistence will be added later

DO NOT:
-------
- Add real HTTP calls to Command Centre
- Add database writes or Supabase operations
- Add schedulers, cron jobs, or timers
- Add learning or training logic
- Pull or receive intelligence from Command Centre
- Modify existing event creation logic
- Add retries or backoff strategies
- Add metrics or analytics

This is a STUB representing the CONCEPT of automatic outbound data pushing.
"""

from typing import List, Dict, Any
import json
from datetime import datetime

# In-memory tracking of sent items (does NOT persist across restarts)
# In a real implementation, this would be persisted to local storage
_sent_event_ids = set()
_sent_label_ids = set()


def collect_unsent_events() -> List[Dict[str, Any]]:
    """
    Collect events that have not been sent to the Command Centre yet.

    STUB IMPLEMENTATION:
    - Returns a dummy list of events for demonstration
    - In a real implementation, this would query local event storage
    - Would filter out events already marked as sent

    Returns:
        List of unsent event dictionaries

    REMINDER: This is a STUB. No real data collection occurs.
    """
    # STUB: In a real implementation, this would:
    # 1. Query local event storage (e.g., SQLite, file system)
    # 2. Filter events where sent_to_command_centre = False
    # 3. Return the list of unsent events

    # For now, return empty list (no events to send)
    unsent_events = []

    # Example of what an event might look like (commented out):
    # unsent_events = [
    #     {
    #         "id": "event_123",
    #         "timestamp": "2025-12-21T12:00:00Z",
    #         "camera_id": "cam_01",
    #         "detection_result": "ABC123",
    #         "confidence": 0.95,
    #         "image_path": "/path/to/image.jpg"
    #     }
    # ]

    return unsent_events


def collect_unsent_labels() -> List[Dict[str, Any]]:
    """
    Collect HITL labels that have not been sent to the Command Centre yet.

    STUB IMPLEMENTATION:
    - Returns a dummy list of labels for demonstration
    - In a real implementation, this would query local label storage
    - Would filter out labels already marked as sent

    Returns:
        List of unsent label dictionaries (with HITL semantics)

    REMINDER: This is a STUB. No real data collection occurs.
    REMINDER: Labels are sent to Command Centre for FUTURE training.
    REMINDER: Client does NOT learn from these labels locally.
    """
    # STUB: In a real implementation, this would:
    # 1. Query local label storage (e.g., SQLite, file system)
    # 2. Filter labels where sent_to_command_centre = False
    # 3. Return the list of unsent labels

    # For now, return empty list (no labels to send)
    unsent_labels = []

    # Example of what a label might look like (commented out):
    # unsent_labels = [
    #     {
    #         "id": "label_456",
    #         "event_id": "event_123",
    #         "timestamp": "2025-12-21T12:05:00Z",
    #         "operator_id": "operator_01",
    #         "label_state": "changed",  # "correct" | "changed" | "unsure"
    #         "original_detection": "AB0123",
    #         "corrected_value": "ABC123",
    #         "notes": "First character was misread"
    #     }
    # ]

    return unsent_labels


def mark_as_sent(item_id: str, item_type: str) -> None:
    """
    Mark an event or label as sent to prevent duplicate transmissions.

    STUB IMPLEMENTATION:
    - Uses in-memory tracking only (does NOT persist across restarts)
    - In a real implementation, this would update local storage

    Args:
        item_id: Unique identifier of the event or label
        item_type: Either "event" or "label"

    REMINDER: This is a STUB. No real persistence occurs.
    """
    # STUB: In a real implementation, this would:
    # 1. Update local storage (e.g., SQLite)
    # 2. Set sent_to_command_centre = True
    # 3. Record the sent_timestamp

    # For now, track in memory only
    if item_type == "event":
        _sent_event_ids.add(item_id)
    elif item_type == "label":
        _sent_label_ids.add(item_id)

    # No actual persistence happens here


def simulate_send_to_command_centre(data: List[Dict[str, Any]], data_type: str) -> bool:
    """
    Simulate sending data to the Command Centre.

    STUB IMPLEMENTATION:
    - Logs data to console instead of making real HTTP calls
    - Always returns success (True)
    - Real networking will be added later

    Args:
        data: List of events or labels to send
        data_type: Either "events" or "labels"

    Returns:
        True (always succeeds in stub mode)

    REMINDER: This is a STUB. No real networking occurs.
    REMINDER: No intelligence or learning happens here.
    """
    if not data:
        print(f"[OUTBOUND STUB] No {data_type} to send")
        return True

    print(f"[OUTBOUND STUB] Simulating send of {len(data)} {data_type} to Command Centre")
    print(f"[OUTBOUND STUB] Data: {json.dumps(data, indent=2)}")

    # STUB: In a real implementation, this would:
    # 1. Make HTTP POST to Command Centre API endpoint
    # 2. Include authentication credentials
    # 3. Handle response codes
    # 4. Return True on success, False on failure

    # For now, just log and return success
    return True


def run_daily_push_stub() -> Dict[str, Any]:
    """
    Simulate a daily automatic push of data to the Command Centre.

    This function represents the concept of automatic, scheduled data transmission
    from the client to the Command Centre. In a real deployment, this would be
    triggered once per day by a scheduler.

    STUB IMPLEMENTATION:
    - Collects unsent events and labels
    - Simulates sending them to Command Centre (logs to console)
    - Marks items as sent (in-memory only)
    - Returns summary of what was sent

    CRITICAL BEHAVIOR:
    - Push is AUTOMATIC (no human approval required)
    - Data is sent ONLY ONCE (no duplicates)
    - NO intelligence or learning occurs here
    - NO data is pulled or received from Command Centre
    - This is OUTBOUND ONLY

    Returns:
        Dictionary with summary of sent data

    REMINDER: This is a STUB representing the CONCEPT of automatic pushing.
    REMINDER: Real networking will be added later.
    REMINDER: Real scheduling will be added later.
    REMINDER: Real persistence will be added later.
    """
    print("\n" + "="*70)
    print("[OUTBOUND STUB] Starting daily push to Command Centre")
    print("="*70)

    # Step 1: Collect unsent data
    print("\n[OUTBOUND STUB] Step 1: Collecting unsent data...")
    unsent_events = collect_unsent_events()
    unsent_labels = collect_unsent_labels()

    print(f"[OUTBOUND STUB] Found {len(unsent_events)} unsent events")
    print(f"[OUTBOUND STUB] Found {len(unsent_labels)} unsent labels")

    # Step 2: Send events
    print("\n[OUTBOUND STUB] Step 2: Sending events to Command Centre...")
    events_sent = False
    if unsent_events:
        events_sent = simulate_send_to_command_centre(unsent_events, "events")
        if events_sent:
            # Mark all events as sent
            for event in unsent_events:
                mark_as_sent(event["id"], "event")
            print(f"[OUTBOUND STUB] Successfully sent {len(unsent_events)} events")
        else:
            print("[OUTBOUND STUB] Failed to send events (would retry later)")

    # Step 3: Send labels
    print("\n[OUTBOUND STUB] Step 3: Sending labels to Command Centre...")
    labels_sent = False
    if unsent_labels:
        labels_sent = simulate_send_to_command_centre(unsent_labels, "labels")
        if labels_sent:
            # Mark all labels as sent
            for label in unsent_labels:
                mark_as_sent(label["id"], "label")
            print(f"[OUTBOUND STUB] Successfully sent {len(unsent_labels)} labels")
        else:
            print("[OUTBOUND STUB] Failed to send labels (would retry later)")

    # Step 4: Summary
    summary = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "events_sent": len(unsent_events) if events_sent else 0,
        "labels_sent": len(unsent_labels) if labels_sent else 0,
        "total_items_sent": (
            (len(unsent_events) if events_sent else 0) +
            (len(unsent_labels) if labels_sent else 0)
        ),
        "status": "success" if (not unsent_events and not unsent_labels) or (events_sent and labels_sent) else "partial"
    }

    print("\n[OUTBOUND STUB] Daily push completed")
    print(f"[OUTBOUND STUB] Summary: {json.dumps(summary, indent=2)}")
    print("="*70 + "\n")

    return summary


def get_sent_status() -> Dict[str, Any]:
    """
    Get statistics about sent items (for debugging/monitoring).

    STUB IMPLEMENTATION:
    - Returns in-memory counts only
    - In a real implementation, would query local storage

    Returns:
        Dictionary with sent item statistics

    REMINDER: This is a STUB. Data does NOT persist across restarts.
    """
    return {
        "sent_events_count": len(_sent_event_ids),
        "sent_labels_count": len(_sent_label_ids),
        "note": "IN-MEMORY ONLY - Does not persist across restarts"
    }


"""
ARCHITECTURAL NOTES:
--------------------

1. AUTOMATIC PUSHING:
   - Client pushes data to Command Centre automatically
   - No human approval or triggering required
   - Happens once per day (simulated)

2. NO INTELLIGENCE:
   - This module does NOT perform learning or training
   - This module does NOT receive intelligence from Command Centre
   - This is pure data transmission only
   - Outbound only, no inbound communication

3. SEND ONCE:
   - Items are marked as sent to prevent duplicates
   - Once sent, an item is never re-sent
   - Idempotency is critical for data integrity

4. STUB LIMITATIONS:
   - No real HTTP networking
   - No real persistence across restarts
   - No real scheduling (must be called manually)
   - No retries or error handling
   - No authentication or security

5. FUTURE WORK:
   - Add real HTTP client to Command Centre API
   - Add persistent storage for sent_status
   - Add scheduler for daily automatic execution
   - Add retry logic with exponential backoff
   - Add authentication and encryption
   - Add batch size limits and pagination

6. COMMAND CENTRE INTEGRATION:
   - Command Centre will receive events and labels
   - Command Centre performs all training and learning
   - Client never receives models or intelligence back
   - This maintains the inference-only client architecture

DO NOT ADD CLIENT-SIDE LEARNING TO THIS MODULE.
"""
