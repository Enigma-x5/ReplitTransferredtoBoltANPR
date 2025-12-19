# Command Centre

## Overview

This folder represents the **CENTRAL COMMAND CENTRE** for the ANPR system.

All learning, model training, data aggregation, and intelligence evolution will happen **HERE** in future implementations.

## Critical Architecture Principle

**NO CLIENT-SIDE LEARNING**

- Client deployments are **INFERENCE ONLY**
- All training, fine-tuning, and model updates occur in the Command Centre
- Client systems consume pre-trained, validated models only

## Current Status

**This module is intentionally a SKELETON at this stage.**

The Command Centre is not yet operational. These files define the interface and structure for future implementation, but contain no active logic.

## Future Responsibilities

When implemented, the Command Centre will:

1. **Ingest Events**: Receive detection events from all deployed city clients
2. **Collect Labels**: Aggregate human-in-the-loop corrections and feedback
3. **Train Models**: Perform centralized model training and fine-tuning
4. **Validate Models**: Test and validate model performance before deployment
5. **Distribute Models**: Push validated models to client deployments
6. **Monitor Performance**: Track system-wide accuracy and detection metrics
7. **Manage Data**: Handle data governance, privacy, and retention policies

## Design Rationale

Centralizing intelligence in the Command Centre ensures:

- **Quality Control**: All models are validated before deployment
- **Resource Efficiency**: Training happens on appropriate infrastructure
- **Consistency**: All clients use the same validated model versions
- **Privacy**: Sensitive training data never leaves the Command Centre
- **Scalability**: Learning from many cities benefits all deployments

## Implementation Status

- [ ] Event ingestion pipeline
- [ ] Label aggregation system
- [ ] Model training orchestration
- [ ] Model validation framework
- [ ] Model distribution system
- [ ] Performance monitoring dashboard

## WARNING

Do NOT implement training logic in client-side code. If training capabilities are needed, they belong in the Command Centre infrastructure, not in deployed client instances.
