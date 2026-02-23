import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.backend.core.config import settings
from app.backend.core.logging import get_logger
from app.backend.services.price_service import cleanup_old_records
from app.backend.tasks.celery_app import celery_app

logger = get_logger(__name__)


async def _cleanup() -> None:
    task_engine = create_async_engine(
        settings.database_url, echo=False, pool_pre_ping=True, pool_size=2, max_overflow=0
    )
    factory = async_sessionmaker(task_engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with factory() as session:
            deleted = await cleanup_old_records(session, days=90)
            await session.commit()
            logger.info("cleanup_completed", deleted_records=deleted)
    finally:
        await task_engine.dispose()


@celery_app.task(name="app.backend.tasks.cleanup.cleanup_old_price_records")
def cleanup_old_price_records() -> None:
    asyncio.run(_cleanup())
