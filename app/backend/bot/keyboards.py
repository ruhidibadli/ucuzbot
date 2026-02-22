from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.shared.constants import STORE_CONFIGS

# ── Reply keyboard button labels (used for matching in handlers) ──
BTN_SEARCH = "\U0001f50d Axtar / Search"
BTN_NEW_ALERT = "\U0001f4ca Yeni Alert"
BTN_MY_ALERTS = "\U0001f4cb Alert\u0259l\u0259rim"
BTN_HELP = "\u2139\ufe0f K\u00f6m\u0259k"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Persistent bottom reply keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_SEARCH), KeyboardButton(text=BTN_NEW_ALERT)],
            [KeyboardButton(text=BTN_MY_ALERTS), KeyboardButton(text=BTN_HELP)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Məhsul adı yazın...",
    )


def main_menu_inline() -> InlineKeyboardMarkup:
    """Inline version of main menu embedded in messages."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001f50d Axtar", callback_data="menu:search"),
            InlineKeyboardButton(text="\U0001f4ca Yeni Alert", callback_data="menu:alert"),
        ],
        [
            InlineKeyboardButton(text="\U0001f4cb Alert\u0259l\u0259rim", callback_data="menu:myalerts"),
            InlineKeyboardButton(text="\u2139\ufe0f K\u00f6m\u0259k", callback_data="menu:help"),
        ],
    ])


def after_alert_created_keyboard() -> InlineKeyboardMarkup:
    """Shown after an alert is successfully created."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4cb Alert\u0259l\u0259rim\u0259 bax", callback_data="menu:myalerts")],
        [InlineKeyboardButton(text="\U0001f4ca Yeni alert yarat", callback_data="menu:alert")],
    ])


def after_search_keyboard(query: str) -> InlineKeyboardMarkup:
    """Shown after search results — offer to create alert or search again."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="\U0001f4ca Bu m\u0259hsul \u00fc\u00e7\u00fcn alert",
            callback_data=f"search:alert:{query[:40]}",
        )],
        [InlineKeyboardButton(text="\U0001f50d Yeni axtar\u0131\u015f", callback_data="menu:search")],
        [InlineKeyboardButton(text="\U0001f3e0 Menyu", callback_data="menu:main")],
    ])


def store_selection_keyboard(selected: set[str] | None = None) -> InlineKeyboardMarkup:
    selected = selected or set()
    buttons = []
    for slug, config in STORE_CONFIGS.items():
        check = " \u2705" if slug in selected else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{config['name']}{check}",
                callback_data=f"store:{slug}",
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="Ham\u0131s\u0131 / All \u2705", callback_data="store:all"),
    ])
    buttons.append([
        InlineKeyboardButton(text="T\u0259sdiql\u0259 / Confirm \u27a1\ufe0f", callback_data="store:confirm"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def alert_list_keyboard(alerts: list) -> InlineKeyboardMarkup:
    buttons = []
    for alert in alerts:
        status = "\U0001f7e2" if alert.is_active and not alert.is_triggered else "\U0001f534"
        price_info = f" ({alert.lowest_price_found} \u20bc)" if alert.lowest_price_found else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {alert.search_query}{price_info}",
                callback_data=f"alert:view:{alert.id}",
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="\U0001f4ca Yeni alert yarat", callback_data="menu:alert"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def alert_detail_keyboard(alert_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f504 \u0130ndi yoxla / Check Now", callback_data=f"alert:check:{alert_id}")],
        [InlineKeyboardButton(text="\U0001f5d1 Sil / Delete", callback_data=f"alert:delete:{alert_id}")],
        [
            InlineKeyboardButton(text="\u2b05\ufe0f Geri / Back", callback_data="alert:list"),
            InlineKeyboardButton(text="\U0001f3e0 Menyu / Menu", callback_data="menu:main"),
        ],
    ])


def pagination_keyboard(page: int, total_pages: int, prefix: str = "page") -> InlineKeyboardMarkup:
    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton(text="\u2b05\ufe0f", callback_data=f"{prefix}:{page - 1}"))
    buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton(text="\u27a1\ufe0f", callback_data=f"{prefix}:{page + 1}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


def cancel_inline_keyboard() -> InlineKeyboardMarkup:
    """Single cancel button for FSM flows."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u274c L\u0259\u011fv et / Cancel", callback_data="action:cancel")],
    ])


def start_actions_inline() -> InlineKeyboardMarkup:
    """Rich post-/start menu with search prominently on top."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f50d M\u0259hsul axtar", callback_data="menu:search")],
        [
            InlineKeyboardButton(text="\U0001f4ca Yeni Alert", callback_data="menu:alert"),
            InlineKeyboardButton(text="\U0001f4cb Alertl\u0259rim", callback_data="menu:myalerts"),
        ],
        [InlineKeyboardButton(text="\u2139\ufe0f K\u00f6m\u0259k", callback_data="menu:help")],
    ])


def no_results_keyboard(query: str) -> InlineKeyboardMarkup:
    """Shown when search returns no results."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f50d Yenid\u0259n axtar", callback_data="menu:search")],
        [InlineKeyboardButton(
            text="\U0001f4ca Bel\u0259 d\u0259 alert yarat",
            callback_data=f"search:alert:{query[:40]}",
        )],
        [InlineKeyboardButton(text="\U0001f3e0 Menyu", callback_data="menu:main")],
    ])


def no_alerts_keyboard() -> InlineKeyboardMarkup:
    """Shown when user has no alerts."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4ca \u0130lk alerti yarat", callback_data="menu:alert")],
        [InlineKeyboardButton(text="\U0001f50d \u018fvv\u0259lc\u0259 axtar", callback_data="menu:search")],
        [InlineKeyboardButton(text="\U0001f3e0 Menyu", callback_data="menu:main")],
    ])


def after_delete_keyboard() -> InlineKeyboardMarkup:
    """Shown after an alert is successfully deleted."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u2b05\ufe0f Alertl\u0259r\u0259 qay\u0131t", callback_data="alert:list")],
        [InlineKeyboardButton(text="\U0001f4ca Yeni alert", callback_data="menu:alert")],
        [InlineKeyboardButton(text="\U0001f3e0 Menyu", callback_data="menu:main")],
    ])


def price_drop_keyboard() -> InlineKeyboardMarkup:
    """Shown in price drop notifications."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4cb Alertl\u0259rim\u0259 bax", callback_data="menu:myalerts")],
    ])
