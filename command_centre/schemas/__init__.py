"""
Command Centre Schemas

SCHEMA-ONLY MODULE - NO LOGIC OR VALIDATION

This module contains pure data contract definitions for payloads received
from client deployments.

These schemas define the expected structure of:
- Detection events from client cameras
- Human-in-the-loop labels/corrections from client operators

REMINDER:
- These are schema definitions only
- No validation logic
- No runtime behavior
- No training or learning implementation
- Model distribution will be PUSH-ONLY in future (separate channel)
"""

# Schema classes are not imported yet as they are pure type definitions
# with no runtime behavior

__all__ = []  # Nothing exported - schemas are documentation only at this stage
