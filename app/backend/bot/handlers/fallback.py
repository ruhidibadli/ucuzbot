from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.types import Message

router = Router()


@router.message(StateFilter(None))
async def fallback_text_search(message: Message):
    """Catch-all: treat any plain text (no active FSM) as a product search."""
    if not message.text or message.text.startswith("/"):
        return

    from app.backend.bot.handlers.search import _execute_search

    await _execute_search(message, message.text.strip())
