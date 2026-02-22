import asyncio
import subprocess
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.backend.api.routes import alerts, auth, health, products, push, search
from app.backend.core.config import settings
from app.backend.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="UcuzBot API",
    description="Azerbaijan Price Monitoring System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
app.include_router(products.router, prefix="/api/v1", tags=["products"])
app.include_router(push.router, prefix="/api/v1", tags=["push"])


@app.on_event("startup")
async def startup_event():
    logger.info("running_migrations")
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "alembic", "-c", "app/backend/db/alembic.ini", "upgrade", "head",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        logger.error("migration_failed", stderr=stderr.decode())
    else:
        logger.info("migrations_complete")

    # Seed stores
    from app.backend.db.base import async_session_factory
    from app.backend.models.store import Store
    from app.shared.constants import STORE_CONFIGS
    from sqlalchemy import select

    async with async_session_factory() as session:
        for slug, config in STORE_CONFIGS.items():
            result = await session.execute(select(Store).where(Store.slug == slug))
            if not result.scalar_one_or_none():
                session.add(Store(
                    slug=slug,
                    name=config["name"],
                    base_url=config["base_url"],
                    search_url_template=config.get("search_url_template"),
                    scraper_class=config["scraper_class"],
                ))
        await session.commit()
    logger.info("stores_seeded")


if __name__ == "__main__":
    uvicorn.run(
        "app.backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.APP_ENV != "production",
    )
