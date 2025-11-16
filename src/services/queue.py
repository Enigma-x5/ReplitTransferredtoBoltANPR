import json
from typing import Optional

import redis.asyncio as aioredis
from src.config import settings
from src.logging_config import get_logger

logger = get_logger(__name__)


class QueueService:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self):
        self.redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        logger.info("Connected to Redis queue")

    async def disconnect(self):
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis queue")

    async def enqueue(self, queue_name: str, data: dict) -> str:
        if not self.redis:
            raise RuntimeError("Redis not connected")

        job_data = json.dumps(data)
        await self.redis.lpush(queue_name, job_data)
        logger.info("Job enqueued", queue=queue_name, job_id=data.get("job_id"))
        return data.get("job_id", "unknown")

    async def dequeue(self, queue_name: str, timeout: int = 0) -> Optional[dict]:
        if not self.redis:
            raise RuntimeError("Redis not connected")

        result = await self.redis.brpop(queue_name, timeout=timeout)
        if result:
            _, job_data = result
            return json.loads(job_data)
        return None

    async def get_queue_length(self, queue_name: str) -> int:
        if not self.redis:
            raise RuntimeError("Redis not connected")
        return await self.redis.llen(queue_name)


queue_service = QueueService()
