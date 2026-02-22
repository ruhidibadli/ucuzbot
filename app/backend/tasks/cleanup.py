import asyncio

from app.backend.core.logging import get_logger
from app.backend.db.base import async_session_factory, engine
from app.backend.services.price_service import cleanup_old_records
from app.backend.tasks.celery_app import celery_app

logger = get_logger(__name__)


async def _cleanup() -> None:
    await engine.dispose()
    async with async_session_factory() as session:
        deleted = await cleanup_old_records(session, days=90)
        await session.commit()
        logger.info("cleanup_completed", deleted_records=deleted)


@celery_app.task(name="app.backend.tasks.cleanup.cleanup_old_price_records")
def cleanup_old_price_records() -> None:
    asyncio.run(_cleanup())
