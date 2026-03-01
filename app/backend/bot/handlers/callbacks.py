import math
from decimal import Decimal

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatAction
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from app.backend.bot.handlers.alerts import AlertCreation, AlertEditing, UserSettings
from app.backend.bot.handlers.search import RESULTS_PER_PAGE, SearchFlow, format_search_results
from app.backend.bot.keyboards import (
    ONBOARDING_STEPS,
    _category_emoji,
    after_alert_created_keyboard,
    after_delete_keyboard,
    after_search_keyboard,
    alert_detail_keyboard,
    alert_edit_keyboard,
    alert_list_keyboard,
    cancel_inline_keyboard,
    category_selection_keyboard,
    delete_confirmation_keyboard,
    main_menu_inline,
    maybe_tip,
    no_alerts_keyboard,
    onboarding_keyboard,
    pagination_keyboard,
    quiet_hours_keyboard,
    settings_keyboard,
    store_selection_keyboard,
)
from app.backend.core.exceptions import AlertLimitReached, DuplicateAlert
from sqlalchemy import select, update

from app.backend.db.base import async_session_factory
from app.backend.models.alert import Alert
from app.backend.models.bot_activity import log_bot_activity
from app.backend.models.user import User
from app.backend.services.category_detector import CATEGORIES, detect_categories
from app.backend.services.alert_service import (
    create_alert,
    delete_alert,
    get_or_create_user,
    get_user_alerts,
    update_alert,
)
from app.backend.services.price_service import get_price_history
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
        try:
            await callback.message.edit_text(
                "\U0001f50d M\u0259hsul ad\u0131n\u0131 yaz\u0131n:\n"
                "Type the product name:",
                reply_markup=cancel_inline_keyboard(),
            )
        except TelegramBadRequest:
            pass
        await callback.answer()

    elif action == "alert":
        await state.set_state(AlertCreation.waiting_for_query)
        try:
            await callback.message.edit_text(
                "\U0001f50d Hans\u0131 m\u0259hsulu izl\u0259m\u0259k ist\u0259yirsiniz?\n"
                "What product do you want to track?",
                reply_markup=cancel_inline_keyboard(),
            )
        except TelegramBadRequest:
            pass
        await callback.answer()

    elif action == "myalerts":
        await callback.bot.send_chat_action(chat_id=callback.message.chat.id, action=ChatAction.TYPING)
        async with async_session_factory() as session:
            alerts = await get_user_alerts(session, callback.from_user.id)
        if not alerts:
            try:
                await callback.message.edit_text(
                    "\U0001f4ed Aktiv alertiniz yoxdur / No active alerts",
                    reply_markup=no_alerts_keyboard(),
                )
            except TelegramBadRequest:
                pass
        else:
            lines = ["\U0001f4cb Alert\u0259l\u0259riniz / Your alerts:\n"]
            for a in alerts:
                status = "\U0001f7e2" if not a.is_triggered else "\u2705"
                cat_emoji = _category_emoji(getattr(a, "product_category", None))
                price_info = f" (\u0259n a\u015fa\u011f\u0131: {a.lowest_price_found} \u20bc)" if a.lowest_price_found else ""
                lines.append(f"{status} {cat_emoji}#{a.id} {a.search_query}\n   H\u0259d\u0259f: {a.target_price} \u20bc{price_info}")
            try:
                await callback.message.edit_text(
                    "\n".join(lines), reply_markup=alert_list_keyboard(alerts)
                )
            except TelegramBadRequest:
                pass
        await callback.answer()

    elif action == "help":
        from app.backend.bot.handlers.start import HELP_MESSAGE

        try:
            await callback.message.edit_text(HELP_MESSAGE, reply_markup=main_menu_inline())
        except TelegramBadRequest:
            pass
        await callback.answer()

    elif action == "settings":
        try:
            await callback.message.edit_text(
                "\u2699\ufe0f T\u0259nziml\u0259m\u0259l\u0259r / Settings",
                reply_markup=settings_keyboard(),
            )
        except TelegramBadRequest:
            pass
        await callback.answer()

    elif action == "main":
        try:
            await callback.message.edit_text(
                "N\u0259 etm\u0259k ist\u0259yirsiniz?", reply_markup=main_menu_inline()
            )
        except TelegramBadRequest:
            pass
        await callback.answer()

    else:
        await callback.answer()


# ── Settings callbacks ──

@router.callback_query(lambda c: c.data and c.data.startswith("settings:"))
async def handle_settings(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":", 1)[1]

    if action == "quiethours":
        async with async_session_factory() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == callback.from_user.id)
            )
            user = result.scalar_one_or_none()

        if user and user.quiet_hours_start is not None and user.quiet_hours_end is not None:
            status = (
                f"\U0001f515 Hal-haz\u0131rda: {user.quiet_hours_start}:00 \u2014 {user.quiet_hours_end}:00\n"
                f"Bu vaxt aral\u0131\u011f\u0131nda bildiri\u015f g\u00f6nd\u0259rilmir."
            )
        else:
            status = "\U0001f514 Sakit saatlar t\u0259yin edilm\u0259yib / Not set"

        await callback.message.edit_text(
            f"\U0001f515 Sakit saatlar / Quiet hours\n\n{status}",
            reply_markup=quiet_hours_keyboard(),
        )
        await callback.answer()

    elif action == "quietset":
        await state.set_state(UserSettings.waiting_for_quiet_start)
        await callback.message.edit_text(
            "\u23f0 Ba\u015flang\u0131c saat\u0131n\u0131 daxil edin (0-23):\n"
            "Enter start hour (0-23):"
        )
        await callback.answer()

    elif action == "quietoff":
        async with async_session_factory() as session:
            await session.execute(
                update(User)
                .where(User.telegram_id == callback.from_user.id)
                .values(quiet_hours_start=None, quiet_hours_end=None)
            )
            await session.commit()
        await callback.message.edit_text(
            "\u2705 Sakit saatlar s\u00f6nd\u00fcr\u00fcld\u00fc / Quiet hours disabled\n\n"
            "Bildiri\u015fl\u0259r ist\u0259nil\u0259n vaxt g\u00f6nd\u0259ril\u0259c\u0259k.",
            reply_markup=settings_keyboard(),
        )
        await callback.answer()

    else:
        await callback.answer()


# ── Search → Alert callback ──

@router.callback_query(lambda c: c.data and c.data.startswith("search:alert:"))
async def handle_search_alert(callback: CallbackQuery, state: FSMContext):
    query = callback.data.split(":", 2)[2]
    await state.update_data(search_query=query, products=0)

    categories = detect_categories(query)
    await state.set_state(AlertCreation.waiting_for_category)
    await callback.message.answer(
        f"\U0001f4ca Alert: \"{query}\"\n\n"
        f"\U0001f4c2 M\u0259hsul kateqoriyas\u0131n\u0131 se\u00e7in:\n"
        f"Select product category:",
        reply_markup=category_selection_keyboard(categories),
    )
    await callback.answer()


# ── Category selection callback ──

@router.callback_query(lambda c: c.data and c.data.startswith("cat:"))
async def handle_category_selection(callback: CallbackQuery, state: FSMContext):
    slug = callback.data.split(":", 1)[1]
    await state.update_data(product_category=slug)
    await state.set_state(AlertCreation.waiting_for_price)

    cat = CATEGORIES.get(slug)
    cat_label = f"{cat.emoji} {cat.name_az}" if cat else slug

    await callback.message.edit_text(
        f"\u2705 Kateqoriya: {cat_label}\n\n"
        f"\U0001f4b0 H\u0259d\u0259f qiym\u0259t daxil edin (AZN):\n"
        f"Enter target price (AZN):",
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

        # Check if we're in edit mode
        edit_alert_id = data.get("edit_alert_id")
        if edit_alert_id:
            async with async_session_factory() as session:
                try:
                    await update_alert(
                        session, edit_alert_id, callback.from_user.id,
                        store_slugs=list(selected),
                    )
                    await session.commit()
                    store_names = [STORE_CONFIGS.get(s, {}).get("name", s) for s in selected]
                    await callback.message.edit_text(
                        f"\u2705 Alert #{edit_alert_id} yenil\u0259ndi!\n"
                        f"\U0001f3ea Ma\u011fazalar: {', '.join(store_names)}",
                        reply_markup=alert_detail_keyboard(edit_alert_id),
                    )
                except Exception:
                    await callback.answer("\u274c X\u0259ta / Error")
                    return
            await state.clear()
            await callback.answer()
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
    product_category = data.get("product_category")

    async with async_session_factory() as session:
        user, _ = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
        )
        try:
            alert = await create_alert(
                session, user, search_query, target_price, store_slugs,
                product_category=product_category,
            )
            await log_bot_activity(
                session,
                user_id=user.id,
                telegram_id=callback.from_user.id,
                action="alert_create",
                detail=f"{search_query} \u2264 {target_price} AZN [{', '.join(store_slugs)}]",
            )
            await session.commit()
        except AlertLimitReached as e:
            await callback.message.edit_text(
                f"\u274c Alert limitin\u0259 \u00e7atd\u0131n\u0131z! / Alert limit reached!\n"
                f"Maksimum: {e.max_alerts} alert\n\n"
                f"K\u00f6hn\u0259 alertl\u0259ri sil\u0259r\u0259k yeni alert yarada bil\u0259rsiniz.",
                reply_markup=main_menu_inline(),
            )
            await state.clear()
            await callback.answer()
            return
        except DuplicateAlert:
            await callback.message.edit_text(
                f"\u274c \"{search_query}\" \u00fc\u00e7\u00fcn art\u0131q aktiv alert var / Alert already exists for this query",
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
    cat = CATEGORIES.get(product_category) if product_category else None
    cat_line = f"\U0001f4c2 {cat.emoji} {cat.name_az}\n" if cat else ""

    tip = maybe_tip("after_alert_created")
    await callback.message.edit_text(
        f"\u2705 Alert yarad\u0131ld\u0131! / Alert created!\n\n"
        f"\U0001f4f1 {search_query}\n"
        f"{cat_line}"
        f"\U0001f3af H\u0259d\u0259f: {target_price:,.2f} \u20bc\n"
        f"\U0001f3ea {', '.join(store_names)}\n\n"
        f"Qiym\u0259t d\u00fc\u015fd\u00fckd\u0259 siz\u0259 x\u0259b\u0259r ver\u0259c\u0259yik!\n"
        f"We'll notify you when the price drops!{tip}",
        reply_markup=after_alert_created_keyboard(),
    )
    await state.clear()
    await callback.answer()


# ── Edit category callback ──

@router.callback_query(lambda c: c.data and c.data.startswith("editcat:"))
async def handle_edit_category_confirm(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    alert_id = int(parts[1])
    slug = parts[2]

    async with async_session_factory() as session:
        try:
            await update_alert(session, alert_id, callback.from_user.id, product_category=slug)
            await session.commit()
            cat = CATEGORIES.get(slug)
            cat_label = f"{cat.emoji} {cat.name_az}" if cat else slug
            await callback.message.edit_text(
                f"\u2705 Alert #{alert_id} yenil\u0259ndi!\n"
                f"\U0001f4c2 Kateqoriya: {cat_label}",
                reply_markup=alert_detail_keyboard(alert_id),
            )
        except Exception:
            await callback.answer("\u274c X\u0259ta / Error")
            return
    await state.clear()
    await callback.answer()


# ── Alert action callbacks ──

@router.callback_query(lambda c: c.data and c.data.startswith("alert:"))
async def handle_alert_actions(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    action = parts[1]

    if action == "list":
        await callback.bot.send_chat_action(chat_id=callback.message.chat.id, action=ChatAction.TYPING)
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
                cat_emoji = _category_emoji(getattr(a, "product_category", None))
                price_info = f" (\u0259n a\u015fa\u011f\u0131: {a.lowest_price_found} \u20bc)" if a.lowest_price_found else ""
                lines.append(f"{status} {cat_emoji}#{a.id} {a.search_query}\n   H\u0259d\u0259f: {a.target_price} \u20bc{price_info}")
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
            cat = CATEGORIES.get(alert.product_category) if alert.product_category else None
            cat_line = f"\U0001f4c2 {cat.emoji} {cat.name_az}\n" if cat else ""
            text = (
                f"\U0001f4ca Alert #{alert.id}\n\n"
                f"\U0001f4f1 {alert.search_query}\n"
                f"{cat_line}"
                f"\U0001f3af H\u0259d\u0259f: {alert.target_price:,.2f} \u20bc\n"
                f"\U0001f3ea {', '.join(store_names)}\n"
            )
            if alert.lowest_price_found:
                text += f"\U0001f4c9 \u018fn a\u015fa\u011f\u0131 qiym\u0259t: {alert.lowest_price_found:,.2f} \u20bc ({alert.lowest_price_store})\n"
            if alert.last_checked_at:
                text += f"\U0001f550 Son yoxlama: {alert.last_checked_at.strftime('%d.%m.%Y %H:%M')}\n"

            # Price trend
            records = await get_price_history(session, alert.id)
            if records:
                text += "\n\U0001f4c8 Qiym\u0259t tarixi / Price trend:\n"
                # Group by date, show last 5 unique dates
                seen_dates = {}
                for r in records:
                    date_str = r.scraped_at.strftime("%d.%m.%Y")
                    if date_str not in seen_dates:
                        seen_dates[date_str] = r
                    elif r.price < seen_dates[date_str].price:
                        seen_dates[date_str] = r
                for date_str, r in list(seen_dates.items())[:5]:
                    store_name = STORE_CONFIGS.get(r.store_slug, {}).get("name", r.store_slug)
                    text += f"  {date_str}: {r.price:,.2f} \u20bc ({store_name})\n"

        text += maybe_tip("alert_detail")
        await callback.message.edit_text(text, reply_markup=alert_detail_keyboard(alert_id, is_triggered=alert.is_triggered))
        await callback.answer()

    elif action == "edit":
        alert_id = int(parts[2])
        await callback.message.edit_text(
            f"\u270f\ufe0f Alert #{alert_id} redakt\u0259si / Edit alert #{alert_id}\n\n"
            f"N\u0259yi d\u0259yi\u015fm\u0259k ist\u0259yirsiniz?",
            reply_markup=alert_edit_keyboard(alert_id),
        )
        await callback.answer()

    elif action == "editprice":
        alert_id = int(parts[2])
        await state.update_data(edit_alert_id=alert_id)
        await state.set_state(AlertEditing.waiting_for_new_price)
        await callback.message.edit_text(
            f"\U0001f4b0 Alert #{alert_id} \u00fc\u00e7\u00fcn yeni h\u0259d\u0259f qiym\u0259t daxil edin (AZN):\n"
            f"Enter new target price (AZN):",
        )
        await callback.answer()

    elif action == "editstores":
        alert_id = int(parts[2])
        await state.update_data(edit_alert_id=alert_id, selected_stores=[])
        await state.set_state(AlertCreation.waiting_for_stores)
        await callback.message.edit_text(
            f"\U0001f3ea Alert #{alert_id} \u00fc\u00e7\u00fcn yeni ma\u011fazalar\u0131 se\u00e7in:",
            reply_markup=store_selection_keyboard(),
        )
        await callback.answer()

    elif action == "editcat":
        alert_id = int(parts[2])
        # Get alert query and detect categories
        async with async_session_factory() as session:
            alerts = await get_user_alerts(session, callback.from_user.id)
            alert = next((a for a in alerts if a.id == alert_id), None)

        if not alert:
            await callback.answer("Alert tap\u0131lmad\u0131 / Not found")
            return

        categories = detect_categories(alert.search_query)
        buttons = []
        for cat in categories:
            buttons.append([
                InlineKeyboardButton(
                    text=f"{cat.emoji} {cat.name_az}",
                    callback_data=f"editcat:{alert_id}:{cat.slug}",
                )
            ])
        buttons.append([InlineKeyboardButton(
            text="\u2b05\ufe0f Geri",
            callback_data=f"alert:edit:{alert_id}",
        )])
        await callback.message.edit_text(
            f"\U0001f4c2 Alert #{alert_id} \u00fc\u00e7\u00fcn kateqoriya se\u00e7in:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
        await callback.answer()

    elif action == "reactivate":
        alert_id = int(parts[2])
        async with async_session_factory() as session:
            result = await session.execute(
                select(Alert)
                .join(User)
                .where(Alert.id == alert_id, User.telegram_id == callback.from_user.id)
            )
            alert = result.scalar_one_or_none()
            if not alert:
                await callback.answer("Alert tap\u0131lmad\u0131 / Not found")
                return
            alert.is_triggered = False
            alert.triggered_at = None
            await log_bot_activity(
                session,
                user_id=None,
                telegram_id=callback.from_user.id,
                action="alert_reactivate",
                detail=f"Alert #{alert_id}",
            )
            await session.commit()
        await callback.message.edit_text(
            f"\u2705 Alert #{alert_id} yenid\u0259n aktivl\u0259\u015fdirildi / reactivated",
            reply_markup=alert_detail_keyboard(alert_id, is_triggered=False),
        )
        await callback.answer()

    elif action == "check":
        alert_id = int(parts[2])
        check_single_alert.delay(alert_id)
        await callback.answer("\U0001f504 Yoxlan\u0131l\u0131r... / Checking now!", show_alert=True)

    elif action == "delete":
        alert_id = int(parts[2])
        await callback.message.edit_text(
            f"\u26a0\ufe0f Alert #{alert_id} silinsin?\n"
            f"Bu \u0259m\u0259liyyat geri qaytarıla bilm\u0259z.\n\n"
            f"Delete alert #{alert_id}?\n"
            f"This action cannot be undone.",
            reply_markup=delete_confirmation_keyboard(alert_id),
        )
        await callback.answer()

    elif action == "confirmdelete":
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
        await callback.answer("N\u0259tic\u0259l\u0259r m\u00fcdd\u0259ti bitdi, yenid\u0259n axtar\u0131n / Results expired, search again")
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


# ── Onboarding callbacks ──

@router.callback_query(lambda c: c.data and c.data.startswith("onboarding:"))
async def handle_onboarding(callback: CallbackQuery):
    value = callback.data.split(":", 1)[1]

    if value == "done":
        async with async_session_factory() as session:
            await session.execute(
                update(User)
                .where(User.telegram_id == callback.from_user.id)
                .values(has_completed_onboarding=True)
            )
            await session.commit()
        await callback.message.edit_text(
            "\U0001f389 Haz\u0131rs\u0131n\u0131z! / You're all set!\n\n"
            "A\u015fa\u011f\u0131dak\u0131 menyudan ba\u015flay\u0131n:",
            reply_markup=main_menu_inline(),
        )
        await callback.answer()
        return

    step = int(value)
    step_data = ONBOARDING_STEPS.get(step)
    if not step_data:
        await callback.answer()
        return

    await callback.message.edit_text(
        f"({step}/3) {step_data['title']}\n\n{step_data['text']}",
        reply_markup=onboarding_keyboard(step),
    )
    await callback.answer()
