import math

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from sqlalchemy import select

from app.backend.bot.keyboards import (
    after_search_keyboard,
    cancel_inline_keyboard,
    no_results_keyboard,
    pagination_keyboard,
)
from app.backend.db.base import async_session_factory
from app.backend.models.bot_activity import log_bot_activity
from app.backend.models.user import User
from app.backend.services.search_service import search_all_stores

router = Router()

RESULTS_PER_PAGE = 5


class SearchFlow(StatesGroup):
    waiting_for_query = State()


def format_search_results(products, query: str, page: int = 1) -> str:
    total = len(products)
    total_pages = math.ceil(total / RESULTS_PER_PAGE)
    start = (page - 1) * RESULTS_PER_PAGE
    end = start + RESULTS_PER_PAGE
    page_items = products[start:end]

    lines = [f"\U0001f50d N\u0259tic\u0259l\u0259r / Results: \"{query}\" ({total} tap\u0131ld\u0131)\n"]

    for i, p in enumerate(page_items, start=start + 1):
        lines.append(
            f"{i}. {p.product_name}\n"
            f"   \U0001f4b0 {p.price:,.2f} \u20bc \u2014 \U0001f3ea {p.store_name}\n"
            f"   \U0001f517 {p.product_url}\n"
        )

    if total_pages > 1:
        lines.append(f"\n\U0001f4c4 S\u0259hif\u0259 {page}/{total_pages}")

    return "\n".join(lines)


async def _execute_search(message: Message, query: str):
    """Reusable search execution — used by cmd_search, SearchFlow, and fallback."""
    if len(query) < 2:
        await message.answer("\u274c \u018fn az\u0131 2 simvol daxil edin / Enter at least 2 characters")
        return

    wait_msg = await message.answer("\u23f3 Axtar\u0131l\u0131r... / Searching...")

    products, errors = await search_all_stores(query)

    # Log search activity
    try:
        async with async_session_factory() as session:
            telegram_id = message.from_user.id
            result = await session.execute(
                select(User.id).where(User.telegram_id == telegram_id)
            )
            uid = result.scalar_one_or_none()
            await log_bot_activity(
                session,
                user_id=uid,
                telegram_id=telegram_id,
                action="search",
                detail=f"{query} \u2192 {len(products)} results",
            )
            await session.commit()
    except Exception:
        pass

    if not products:
        error_text = ""
        if errors:
            error_text = "\n\n\u26a0\ufe0f B\u0259zi ma\u011fazalarda x\u0259ta: " + ", ".join(errors)
        await wait_msg.edit_text(
            f"\U0001f614 N\u0259tic\u0259 tap\u0131lmad\u0131: \"{query}\"{error_text}",
            reply_markup=no_results_keyboard(query),
        )
        return

    text = format_search_results(products, query)
    total_pages = math.ceil(len(products) / RESULTS_PER_PAGE)

    if total_pages > 1:
        await wait_msg.edit_text(text, reply_markup=pagination_keyboard(1, total_pages, "search"))
        await message.answer(
            "\U0001f4a1 Bu m\u0259hsul \u00fc\u00e7\u00fcn alert yaratmaq ist\u0259yirsiniz?",
            reply_markup=after_search_keyboard(query),
        )
    else:
        await wait_msg.edit_text(text, reply_markup=after_search_keyboard(query))


@router.message(Command("search"))
async def cmd_search(message: Message, state: FSMContext):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await state.set_state(SearchFlow.waiting_for_query)
        await message.answer(
            "\U0001f50d M\u0259hsul ad\u0131n\u0131 yaz\u0131n:\n"
            "Type the product name:",
            reply_markup=cancel_inline_keyboard(),
        )
        return

    query = parts[1].strip()
    await _execute_search(message, query)


@router.message(SearchFlow.waiting_for_query)
async def search_receive_query(message: Message, state: FSMContext):
    query = message.text.strip()
    await state.clear()
    await _execute_search(message, query)
