import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from app.backend.bot.handlers import alerts, callbacks, fallback, search, start
from app.backend.core.config import settings
from app.backend.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def run_migrations():
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


async def main():
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)

    await run_migrations()

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(search.router)
    dp.include_router(alerts.router)
    dp.include_router(callbacks.router)
    dp.include_router(fallback.router)  # Must be last — catch-all for plain text

    await bot.set_my_commands([
        BotCommand(command="start", description="Ba\u015fla / Start"),
        BotCommand(command="search", description="M\u0259hsul axtar / Search product"),
        BotCommand(command="alert", description="Qiym\u0259t alerti yarat / Create alert"),
        BotCommand(command="myalerts", description="Alert\u0259l\u0259rim / My alerts"),
        BotCommand(command="help", description="K\u00f6m\u0259k / Help"),
        BotCommand(command="cancel", description="L\u0259\u011fv et / Cancel"),
    ])

    logger.info("bot_starting")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
