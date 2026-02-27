import math
from decimal import Decimal

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.backend.bot.handlers.alerts import AlertCreation
from app.backend.bot.handlers.search import RESULTS_PER_PAGE, SearchFlow, format_search_results
from app.backend.bot.keyboards import (
    after_alert_created_keyboard,
    after_delete_keyboard,
    after_search_keyboard,
    alert_detail_keyboard,
    alert_list_keyboard,
    cancel_inline_keyboard,
    main_menu_inline,
    no_alerts_keyboard,
    pagination_keyboard,
    store_selection_keyboard,
)
from app.backend.core.exceptions import DuplicateAlert
from app.backend.db.base import async_session_factory
from app.backend.models.bot_activity import log_bot_activity
from app.backend.services.alert_service import (
    create_alert,
    delete_alert,
    get_or_create_user,
    get_user_alerts,
)
from app.backend.tasks.price_check import check_single_alert
from app.shared.constants import STORE_CONFIGS

router = Router()


# ── Action callbacks ──

@router.callback_query(lambda c: c.data == "action:cancel")
async def handle_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "\u2705 \u018fm\u0259liyyat l\u0259\u011fv edildi / Operation cancelled",
        reply_markup=main_menu_inline(),
    )
    await callback.answer()


# ── Menu callbacks ──

@router.callback_query(lambda c: c.data and c.data.startswith("menu:"))
async def handle_menu(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":", 1)[1]

    if action == "search":
        await state.clear()
        await state.set_state(SearchFlow.waiting_for_query)
        await callback.message.answer(
            "\U0001f50d M\u0259hsul ad\u0131n\u0131 yaz\u0131n:\n"
            "Type the product name:",
            reply_markup=cancel_inline_keyboard(),
        )
        await callback.answer()

    elif action == "alert":
        await state.set_state(AlertCreation.waiting_for_query)
        await callback.message.answer(
            "\U0001f50d Hans\u0131 m\u0259hsulu izl\u0259m\u0259k ist\u0259yirsiniz?\n"
            "What product do you want to track?",
            reply_markup=cancel_inline_keyboard(),
        )
        await callback.answer()

    elif action == "myalerts":
        async with async_session_factory() as session:
            alerts = await get_user_alerts(session, callback.from_user.id)
        if not alerts:
            await callback.message.answer(
                "\U0001f4ed Aktiv alertiniz yoxdur / No active alerts",
                reply_markup=no_alerts_keyboard(),
            )
        else:
            lines = ["\U0001f4cb Alert\u0259l\u0259riniz / Your alerts:\n"]
            for a in alerts:
                status = "\U0001f7e2" if not a.is_triggered else "\u2705"
                price_info = f" (\u0259n a\u015fa\u011f\u0131: {a.lowest_price_found} \u20bc)" if a.lowest_price_found else ""
                lines.append(f"{status} #{a.id} {a.search_query}\n   H\u0259d\u0259f: {a.target_price} \u20bc{price_info}")
            await callback.message.answer(
                "\n".join(lines), reply_markup=alert_list_keyboard(alerts)
            )
        await callback.answer()

    elif action == "help":
        from app.backend.bot.handlers.start import HELP_MESSAGE

        await callback.message.answer(HELP_MESSAGE, reply_markup=main_menu_inline())
        await callback.answer()

    elif action == "main":
        await callback.message.answer(
            "N\u0259 etm\u0259k ist\u0259yirsiniz?", reply_markup=main_menu_inline()
        )
        await callback.answer()

    else:
        await callback.answer()


# ── Search → Alert callback ──

@router.callback_query(lambda c: c.data and c.data.startswith("search:alert:"))
async def handle_search_alert(callback: CallbackQuery, state: FSMContext):
    query = callback.data.split(":", 2)[2]
    await state.set_state(AlertCreation.waiting_for_query)
    await state.update_data(search_query=query, products=0)
    await state.set_state(AlertCreation.waiting_for_price)
    await callback.message.answer(
        f"\U0001f4ca Alert: \"{query}\"\n\n"
        f"\U0001f4b0 H\u0259d\u0259f qiym\u0259t daxil edin (AZN):\n"
        f"Enter target price (AZN):",
        reply_markup=cancel_inline_keyboard(),
    )
    await callback.answer()


# ── Store selection callbacks ──

@router.callback_query(lambda c: c.data and c.data.startswith("store:"))
async def handle_store_selection(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":", 1)[1]
    data = await state.get_data()
    selected: set = data.get("selected_stores", set())
    if isinstance(selected, list):
        selected = set(selected)

    if action == "all":
        if len(selected) == len(STORE_CONFIGS):
            selected = set()
        else:
            selected = set(STORE_CONFIGS.keys())
    elif action == "confirm":
        if not selected:
            await callback.answer("\u274c \u018fn az\u0131 1 ma\u011faza se\u00e7in / Select at least 1 store")
            return
        await _finalize_alert(callback, state, selected)
        return
    else:
        if action in selected:
            selected.discard(action)
        else:
            selected.add(action)

    await state.update_data(selected_stores=list(selected))
    await callback.message.edit_reply_markup(reply_markup=store_selection_keyboard(selected))
    await callback.answer()


async def _finalize_alert(callback: CallbackQuery, state: FSMContext, selected_stores: set):
    data = await state.get_data()
    search_query = data["search_query"]
    target_price = Decimal(data["target_price"])
    store_slugs = list(selected_stores)

    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
        )
        try:
            alert = await create_alert(session, user, search_query, target_price, store_slugs)
            await log_bot_activity(
                session,
                user_id=user.id,
                telegram_id=callback.from_user.id,
                action="alert_create",
                detail=f"{search_query} \u2264 {target_price} AZN [{', '.join(store_slugs)}]",
            )
            await session.commit()
        except DuplicateAlert:
            await callback.message.edit_text(
                f"❌ \"{search_query}\" üçün artıq aktiv alert var / Alert already exists for this query",
                reply_markup=main_menu_inline(),
            )
            await state.clear()
            await callback.answer()
            return

    try:
        check_single_alert.delay(alert.id)
    except Exception:
        pass  # Non-critical: alert is saved, price check will run on next schedule

    store_names = [STORE_CONFIGS[s]["name"] for s in store_slugs if s in STORE_CONFIGS]
    await callback.message.edit_text(
        f"\u2705 Alert yarad\u0131ld\u0131! / Alert created!\n\n"
        f"\U0001f4f1 {search_query}\n"
        f"\U0001f3af H\u0259d\u0259f: {target_price:,.2f} \u20bc\n"
        f"\U0001f3ea {', '.join(store_names)}\n\n"
        f"Qiym\u0259t d\u00fc\u015fd\u00fckd\u0259 siz\u0259 x\u0259b\u0259r ver\u0259c\u0259yik!\n"
        f"We'll notify you when the price drops!",
        reply_markup=after_alert_created_keyboard(),
    )
    await state.clear()
    await callback.answer()


# ── Alert action callbacks ──

@router.callback_query(lambda c: c.data and c.data.startswith("alert:"))
async def handle_alert_actions(callback: CallbackQuery):
    parts = callback.data.split(":")
    action = parts[1]

    if action == "list":
        async with async_session_factory() as session:
            alerts = await get_user_alerts(session, callback.from_user.id)
        if not alerts:
            await callback.message.edit_text(
                "\U0001f4ed Aktiv alertiniz yoxdur / No active alerts",
                reply_markup=no_alerts_keyboard(),
            )
        else:
            lines = ["\U0001f4cb Alert\u0259l\u0259riniz / Your alerts:\n"]
            for a in alerts:
                status = "\U0001f7e2" if not a.is_triggered else "\u2705"
                price_info = f" (\u0259n a\u015fa\u011f\u0131: {a.lowest_price_found} \u20bc)" if a.lowest_price_found else ""
                lines.append(f"{status} #{a.id} {a.search_query}\n   H\u0259d\u0259f: {a.target_price} \u20bc{price_info}")
            await callback.message.edit_text(
                "\n".join(lines), reply_markup=alert_list_keyboard(alerts)
            )
        await callback.answer()

    elif action == "view":
        alert_id = int(parts[2])
        async with async_session_factory() as session:
            alerts = await get_user_alerts(session, callback.from_user.id)
            alert = next((a for a in alerts if a.id == alert_id), None)

        if not alert:
            await callback.answer("Alert tap\u0131lmad\u0131 / Not found")
            return

        store_names = [STORE_CONFIGS.get(s, {}).get("name", s) for s in alert.store_slugs]
        text = (
            f"\U0001f4ca Alert #{alert.id}\n\n"
            f"\U0001f4f1 {alert.search_query}\n"
            f"\U0001f3af H\u0259d\u0259f: {alert.target_price:,.2f} \u20bc\n"
            f"\U0001f3ea {', '.join(store_names)}\n"
        )
        if alert.lowest_price_found:
            text += f"\U0001f4c9 \u018fn a\u015fa\u011f\u0131 qiym\u0259t: {alert.lowest_price_found:,.2f} \u20bc ({alert.lowest_price_store})\n"
        if alert.last_checked_at:
            text += f"\U0001f550 Son yoxlama: {alert.last_checked_at.strftime('%d.%m.%Y %H:%M')}\n"

        await callback.message.edit_text(text, reply_markup=alert_detail_keyboard(alert_id))
        await callback.answer()

    elif action == "check":
        alert_id = int(parts[2])
        check_single_alert.delay(alert_id)
        await callback.answer("\U0001f504 Yoxlan\u0131l\u0131r... / Checking now!", show_alert=True)

    elif action == "delete":
        alert_id = int(parts[2])
        async with async_session_factory() as session:
            try:
                await delete_alert(session, alert_id, callback.from_user.id)
                await log_bot_activity(
                    session,
                    user_id=None,
                    telegram_id=callback.from_user.id,
                    action="alert_delete",
                    detail=f"Alert #{alert_id}",
                )
                await session.commit()
                await callback.message.edit_text(
                    f"\u2705 Alert #{alert_id} silindi / deleted",
                    reply_markup=after_delete_keyboard(),
                )
            except Exception:
                await callback.answer("\u274c X\u0259ta / Error")
                return
        await callback.answer()


# ── Pagination callbacks ──

@router.callback_query(lambda c: c.data and c.data.startswith("search:") and c.data.split(":")[1].isdigit())
async def handle_search_pagination(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[1])
    data = await state.get_data()
    results = data.get("search_results")
    query = data.get("search_query", "")

    if not results:
        await callback.answer("Nəticələr müddəti bitdi, yenidən axtarın / Results expired, search again")
        return

    # Reconstruct lightweight product objects for format_search_results
    from types import SimpleNamespace

    products = [
        SimpleNamespace(
            product_name=r["product_name"],
            price=Decimal(r["price"]),
            product_url=r["product_url"],
            store_slug=r["store_slug"],
            store_name=r["store_name"],
        )
        for r in results
    ]

    total_pages = math.ceil(len(products) / RESULTS_PER_PAGE)
    page = max(1, min(page, total_pages))

    text = format_search_results(products, query, page)
    await callback.message.edit_text(text, reply_markup=pagination_keyboard(page, total_pages, "search"))
    await callback.answer()


@router.callback_query(lambda c: c.data == "noop")
async def handle_noop(callback: CallbackQuery):
    await callback.answer()
