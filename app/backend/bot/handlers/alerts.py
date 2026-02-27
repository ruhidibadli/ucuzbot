from decimal import Decimal, InvalidOperation

from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.backend.bot.keyboards import (
    after_delete_keyboard,
    alert_list_keyboard,
    cancel_inline_keyboard,
    main_menu_inline,
    no_alerts_keyboard,
    store_selection_keyboard,
)
from app.backend.db.base import async_session_factory
from app.backend.models.bot_activity import log_bot_activity
from app.backend.services.alert_service import (
    create_alert,
    delete_alert,
    get_or_create_user,
    get_user_alerts,
)
from app.backend.services.search_service import search_all_stores

router = Router()


class AlertCreation(StatesGroup):
    waiting_for_query = State()
    waiting_for_price = State()
    waiting_for_stores = State()


@router.message(Command("cancel"), StateFilter("*"))
async def cmd_cancel(message: Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        await message.answer("\u2139\ufe0f L\u0259\u011fv edil\u0259c\u0259k \u0259m\u0259liyyat yoxdur / Nothing to cancel")
        return
    await state.clear()
    await message.answer(
        "\u2705 \u018fm\u0259liyyat l\u0259\u011fv edildi / Operation cancelled",
        reply_markup=main_menu_inline(),
    )


@router.message(Command("alert"))
async def cmd_alert(message: Message, state: FSMContext):
    await state.set_state(AlertCreation.waiting_for_query)
    await message.answer(
        "\U0001f50d Hans\u0131 m\u0259hsulu izl\u0259m\u0259k ist\u0259yirsiniz?\n"
        "What product do you want to track?",
        reply_markup=cancel_inline_keyboard(),
    )


@router.message(AlertCreation.waiting_for_query)
async def alert_receive_query(message: Message, state: FSMContext):
    query = message.text.strip()
    if len(query) < 2:
        await message.answer("❌ Ən azı 2 simvol daxil edin / Enter at least 2 characters")
        return

    wait_msg = await message.answer("⏳ Axtarılır... / Searching...")
    products, _ = await search_all_stores(query, max_results_per_store=3)

    if products:
        lines = [f"📊 Cari qiymətlər / Current prices for \"{query}\":\n"]
        for p in products[:5]:
            lines.append(f"• {p.product_name}: {p.price:,.2f} ₼ ({p.store_name})")
        await wait_msg.edit_text("\n".join(lines))

    await state.update_data(search_query=query, products=len(products))
    await state.set_state(AlertCreation.waiting_for_price)
    await message.answer(
        "\U0001f4b0 H\u0259d\u0259f qiym\u0259t daxil edin (AZN):\n"
        "Enter target price (AZN):",
        reply_markup=cancel_inline_keyboard(),
    )


@router.message(AlertCreation.waiting_for_price)
async def alert_receive_price(message: Message, state: FSMContext):
    try:
        price = Decimal(message.text.strip().replace(",", ".")).quantize(Decimal("0.01"))
        if price <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Düzgün qiymət daxil edin / Enter a valid price\nMəsələn: 1500")
        return

    await state.update_data(target_price=str(price), selected_stores=set())
    await state.set_state(AlertCreation.waiting_for_stores)
    await message.answer(
        "🏪 İzləmək istədiyiniz mağazaları seçin:\nSelect stores to monitor:",
        reply_markup=store_selection_keyboard(),
    )


@router.message(Command("myalerts"))
async def cmd_myalerts(message: Message):
    async with async_session_factory() as session:
        alerts = await get_user_alerts(session, message.from_user.id)

    if not alerts:
        await message.answer(
            "\U0001f4ed Aktiv alertiniz yoxdur / No active alerts",
            reply_markup=no_alerts_keyboard(),
        )
        return

    lines = ["📋 Alertləriniz / Your alerts:\n"]
    for a in alerts:
        status = "🟢" if not a.is_triggered else "✅"
        price_info = f" (ən aşağı: {a.lowest_price_found} ₼)" if a.lowest_price_found else ""
        lines.append(f"{status} #{a.id} {a.search_query}\n   Hədəf: {a.target_price} ₼{price_info}")

    await message.answer("\n".join(lines), reply_markup=alert_list_keyboard(alerts))


@router.message(Command("delete"))
async def cmd_delete(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ İstifadə / Usage: /delete <alert_id>")
        return

    try:
        alert_id = int(parts[1])
    except ValueError:
        await message.answer("❌ Düzgün ID daxil edin / Enter a valid ID")
        return

    async with async_session_factory() as session:
        try:
            await delete_alert(session, alert_id, message.from_user.id)
            await log_bot_activity(
                session,
                user_id=None,
                telegram_id=message.from_user.id,
                action="alert_delete",
                detail=f"Alert #{alert_id}",
            )
            await session.commit()
            await message.answer(
                f"\u2705 Alert #{alert_id} silindi / deleted",
                reply_markup=after_delete_keyboard(),
            )
        except Exception:
            await message.answer(f"❌ Alert #{alert_id} tapılmadı / not found")
