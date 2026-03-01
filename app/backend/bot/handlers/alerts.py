from decimal import Decimal, InvalidOperation

from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from sqlalchemy import update

from app.backend.bot.keyboards import (
    _category_emoji,
    after_delete_keyboard,
    alert_detail_keyboard,
    alert_list_keyboard,
    cancel_inline_keyboard,
    category_selection_keyboard,
    main_menu_inline,
    no_alerts_keyboard,
    settings_keyboard,
    store_selection_keyboard,
)
from app.backend.models.user import User
from app.backend.db.base import async_session_factory
from app.backend.models.bot_activity import log_bot_activity
from app.backend.services.alert_service import (
    create_alert,
    delete_alert,
    get_or_create_user,
    get_user_alerts,
    update_alert,
)
from app.backend.services.category_detector import CATEGORIES, detect_categories
from app.backend.services.search_service import search_all_stores

router = Router()


class AlertCreation(StatesGroup):
    waiting_for_query = State()
    waiting_for_category = State()
    waiting_for_price = State()
    waiting_for_stores = State()


class AlertEditing(StatesGroup):
    waiting_for_new_price = State()


class UserSettings(StatesGroup):
    waiting_for_quiet_start = State()
    waiting_for_quiet_end = State()


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


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    await message.answer(
        "\u2699\ufe0f T\u0259nziml\u0259m\u0259l\u0259r / Settings",
        reply_markup=settings_keyboard(),
    )


@router.message(UserSettings.waiting_for_quiet_start)
async def settings_receive_quiet_start(message: Message, state: FSMContext):
    text = message.text.strip()
    try:
        hour = int(text)
        if not 0 <= hour <= 23:
            raise ValueError
    except (ValueError, TypeError):
        await message.answer(
            "\u274c 0\u201323 aras\u0131nda saat daxil edin / Enter an hour between 0-23"
        )
        return
    await state.update_data(quiet_start=hour)
    await state.set_state(UserSettings.waiting_for_quiet_end)
    await message.answer(
        f"\u2705 Ba\u015flang\u0131c: {hour}:00\n\n"
        f"\u23f0 Bitmə saatını daxil edin (0-23):\n"
        f"Enter end hour (0-23):"
    )


@router.message(UserSettings.waiting_for_quiet_end)
async def settings_receive_quiet_end(message: Message, state: FSMContext):
    text = message.text.strip()
    try:
        hour = int(text)
        if not 0 <= hour <= 23:
            raise ValueError
    except (ValueError, TypeError):
        await message.answer(
            "\u274c 0\u201323 aras\u0131nda saat daxil edin / Enter an hour between 0-23"
        )
        return
    data = await state.get_data()
    start_hour = data["quiet_start"]
    await state.clear()

    async with async_session_factory() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == message.from_user.id)
            .values(quiet_hours_start=start_hour, quiet_hours_end=hour)
        )
        await session.commit()

    await message.answer(
        f"\u2705 Sakit saatlar t\u0259yin edildi / Quiet hours set!\n\n"
        f"\U0001f515 {start_hour}:00 \u2014 {hour}:00\n"
        f"Bu vaxt aral\u0131\u011f\u0131nda bildiris g\u00f6nd\u0259rilm\u0259y\u0259c\u0259k.",
        reply_markup=settings_keyboard(),
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

    await message.answer_chat_action("typing")
    wait_msg = await message.answer("⏳ Axtarılır... / Searching...")
    products, _ = await search_all_stores(query, max_results_per_store=3)

    if products:
        lines = [f"📊 Cari qiymətlər / Current prices for \"{query}\":\n"]
        for p in products[:5]:
            lines.append(f"• {p.product_name}: {p.price:,.2f} ₼ ({p.store_name})")
        await wait_msg.edit_text("\n".join(lines))

    await state.update_data(search_query=query, products=len(products))

    categories = detect_categories(query)
    await state.set_state(AlertCreation.waiting_for_category)
    await message.answer(
        "📂 Məhsul kateqoriyasını seçin:\n"
        "Select product category:",
        reply_markup=category_selection_keyboard(categories),
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


@router.message(AlertEditing.waiting_for_new_price)
async def alert_edit_receive_price(message: Message, state: FSMContext):
    try:
        price = Decimal(message.text.strip().replace(",", ".")).quantize(Decimal("0.01"))
        if price <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("\u274c D\u00fczg\u00fcn qiym\u0259t daxil edin / Enter a valid price\nM\u0259s\u0259l\u0259n: 1500")
        return

    data = await state.get_data()
    alert_id = data.get("edit_alert_id")
    await state.clear()

    async with async_session_factory() as session:
        try:
            alert = await update_alert(session, alert_id, message.from_user.id, target_price=price)
            await session.commit()
            await message.answer(
                f"\u2705 Alert #{alert_id} yenil\u0259ndi!\n"
                f"\U0001f3af Yeni h\u0259d\u0259f qiym\u0259t: {price:,.2f} \u20bc",
                reply_markup=alert_detail_keyboard(alert_id),
            )
        except Exception:
            await message.answer(f"\u274c Alert #{alert_id} tap\u0131lmad\u0131 / not found")


@router.message(Command("myalerts"))
async def cmd_myalerts(message: Message):
    await message.answer_chat_action("typing")
    async with async_session_factory() as session:
        alerts = await get_user_alerts(session, message.from_user.id)

    if not alerts:
        await message.answer(
            "\U0001f4ed Aktiv alertiniz yoxdur / No active alerts",
            reply_markup=no_alerts_keyboard(),
        )
        return

    lines = ["\U0001f4cb Alert\u0259l\u0259riniz / Your alerts:\n"]
    for a in alerts:
        status = "\U0001f7e2" if not a.is_triggered else "\u2705"
        cat_emoji = _category_emoji(getattr(a, "product_category", None))
        price_info = f" (\u0259n a\u015fa\u011f\u0131: {a.lowest_price_found} \u20bc)" if a.lowest_price_found else ""
        lines.append(f"{status} {cat_emoji}#{a.id} {a.search_query}\n   H\u0259d\u0259f: {a.target_price} \u20bc{price_info}")

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
