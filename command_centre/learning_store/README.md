# Command Centre Learning Store Schema

## Overview

This folder defines the **Command Centre learning database schema** for centralized machine learning operations.

**CRITICAL ARCHITECTURE:**
- City databases remain isolated and untouched
- This schema is used ONLY for central learning
- No operational or client data is stored here
- Only curated learning samples and HITL labels are stored

## Purpose

The Command Centre learning store exists to:

1. **Aggregate curated samples** from multiple cities for centralized learning
2. **Store HITL labels** (human-in-the-loop corrections) for training
3. **Track dataset versions** for training reproducibility
4. **Maintain separation** between operational data (city DBs) and learning data (Command Centre)

## Schema Files

### `learning_samples.sql`
Defines the `learning_samples` table for storing curated detection samples from cities.

### `hitl_labels.sql`
Defines the `hitl_labels` table for storing human-in-the-loop corrections and labels.

### `dataset_versions.sql`
Defines the `dataset_versions` table for tracking dataset versions used in training runs.

## Database Agnostic

These schemas are written in standard SQL and should work on most relational databases:
- PostgreSQL (recommended)
- MySQL
- SQLite
- Others with minor adjustments

## Data Flow

```
City Clients (Operational DBs)
    ↓
    ↓ Send curated samples + HITL labels
    ↓
Command Centre (Learning Store)
    ↓
    ↓ Aggregate & version
    ↓
Training Pipeline (Future)
```

## Important Notes

1. **Isolation**: City operational data stays in city databases
2. **Curation**: Only selected samples (not all detections) are sent to learning store
3. **HITL**: Human corrections are stored here for supervised learning
4. **Versioning**: Dataset versions enable reproducible training
5. **Privacy**: No PII or sensitive operational data should be stored

## Not Included

This schema does NOT include:
- Model artifacts or weights
- Training metrics or evaluation results
- Configuration or hyperparameters
- Real-time streaming or queue tables

These may be added in future iterations if needed.

## Usage

These SQL files are **schema definitions only**. They:
- Define table structure
- Document field meanings
- Do NOT create actual databases
- Do NOT insert data
- Do NOT connect to any database system

To use these schemas:
1. Choose a database system (e.g., PostgreSQL, Supabase)
2. Execute the SQL files to create tables
3. Configure Command Centre receiver to write to these tables
4. Implement training pipeline to read from these tables

## Status

**SCHEMA ONLY - NOT IMPLEMENTED**

This is a design document. The actual database, connections, and data ingestion logic are not yet implemented.
