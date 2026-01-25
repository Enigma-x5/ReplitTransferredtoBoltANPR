#!/usr/bin/env python3
"""
PHASE 10.1 Cleanup Script: Delete Events with null crop_path

This script removes Events rows where crop_path IS NULL to clean up
database corruption from remote inference pipeline bugs.

Usage:
    python scripts/cleanup_null_crops.py [--dry-run]
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, delete, func
from src.database import AsyncSessionLocal
from src.models.event import Event
from src.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def cleanup_null_crops(dry_run: bool = False):
    """Delete all Events with crop_path IS NULL."""

    async with AsyncSessionLocal() as db:
        # Count events with null crop_path
        count_query = select(func.count(Event.id)).where(Event.crop_path.is_(None))
        result = await db.execute(count_query)
        null_count = result.scalar()

        logger.info(
            "CLEANUP_NULL_CROPS_START",
            null_crop_events=null_count,
            dry_run=dry_run
        )

        if null_count == 0:
            logger.info("No events with null crop_path found. Database is clean.")
            return 0

        if dry_run:
            logger.info(
                "DRY_RUN",
                message=f"Would delete {null_count} events with null crop_path"
            )

            # Show sample of events to be deleted
            sample_query = (
                select(Event.id, Event.plate, Event.created_at)
                .where(Event.crop_path.is_(None))
                .limit(10)
            )
            sample_result = await db.execute(sample_query)
            samples = sample_result.all()

            logger.info("Sample events to delete:")
            for event_id, plate, created_at in samples:
                logger.info(
                    "SAMPLE_EVENT",
                    event_id=str(event_id),
                    plate=plate,
                    created_at=created_at.isoformat()
                )

            return null_count

        # Delete events with null crop_path
        delete_query = delete(Event).where(Event.crop_path.is_(None))
        await db.execute(delete_query)
        await db.commit()

        logger.info(
            "CLEANUP_NULL_CROPS_COMPLETE",
            deleted_count=null_count
        )

        return null_count


async def main():
    parser = argparse.ArgumentParser(
        description="Delete Events with null crop_path from database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    args = parser.parse_args()

    try:
        deleted_count = await cleanup_null_crops(dry_run=args.dry_run)

        if args.dry_run:
            print(f"\n[DRY RUN] Would delete {deleted_count} events with null crop_path")
        else:
            print(f"\nSuccessfully deleted {deleted_count} events with null crop_path")

        return 0
    except Exception as e:
        logger.error("CLEANUP_FAILED", error=str(e), error_type=type(e).__name__)
        print(f"\nERROR: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
