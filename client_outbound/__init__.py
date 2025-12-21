"""
Client Outbound Interface

This module defines the ONE-WAY outbound interface from client deployments
to the Command Centre.

CRITICAL ARCHITECTURE PRINCIPLE:
---------------------------------
CLIENT ➜ COMMAND CENTRE (ONE-WAY ONLY)

Clients send detection events and human labels TO the Command Centre.
Clients NEVER receive intelligence, models, or training data BACK.

STATUS: NOT IMPLEMENTED - SKELETON ONLY

This module is intentionally inactive. It defines the interface for future
implementation but contains no active networking or communication logic.

WARNING:
--------
- Client deployments remain INFERENCE ONLY
- Clients must NEVER perform learning or training
- All intelligence evolution happens in the Command Centre
- This interface is for telemetry and feedback collection only

DO NOT wire this module into runtime until Command Centre infrastructure
is operational.
"""

__version__ = "0.0.0"
__status__ = "skeleton"

# Placeholder imports for future implementation
# from .command_centre_client import send_event, send_label

__all__ = []  # Nothing exported yet - module is not operational
