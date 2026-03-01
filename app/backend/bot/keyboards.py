import random

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.backend.services.category_detector import CATEGORIES
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
        [
            InlineKeyboardButton(text="\u2699\ufe0f T\u0259nziml\u0259m\u0259l\u0259r", callback_data="menu:settings"),
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


def category_selection_keyboard(categories: list) -> InlineKeyboardMarkup:
    """Shown after query to let user pick a product category for filtering."""
    buttons = []
    for cat in categories:
        buttons.append([
            InlineKeyboardButton(
                text=f"{cat.emoji} {cat.name_az}",
                callback_data=f"cat:{cat.slug}",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


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


def _category_emoji(product_category: str | None) -> str:
    if not product_category:
        return ""
    cat = CATEGORIES.get(product_category)
    return f"{cat.emoji} " if cat else ""


def alert_list_keyboard(alerts: list) -> InlineKeyboardMarkup:
    buttons = []
    for alert in alerts:
        status = "\U0001f7e2" if alert.is_active and not alert.is_triggered else "\U0001f534"
        cat_emoji = _category_emoji(getattr(alert, "product_category", None))
        price_info = f" ({alert.lowest_price_found} \u20bc)" if alert.lowest_price_found else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {cat_emoji}{alert.search_query}{price_info}",
                callback_data=f"alert:view:{alert.id}",
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="\U0001f4ca Yeni alert yarat", callback_data="menu:alert"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def alert_detail_keyboard(alert_id: int, is_triggered: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    if is_triggered:
        buttons.append([InlineKeyboardButton(
            text="\U0001f504 Yenid\u0259n aktivl\u0259\u015fdir / Reactivate",
            callback_data=f"alert:reactivate:{alert_id}",
        )])
    else:
        buttons.append([InlineKeyboardButton(
            text="\U0001f504 \u0130ndi yoxla / Check Now",
            callback_data=f"alert:check:{alert_id}",
        )])
    buttons.append([InlineKeyboardButton(
        text="\u270f\ufe0f Redakt\u0259 / Edit",
        callback_data=f"alert:edit:{alert_id}",
    )])
    buttons.append([InlineKeyboardButton(text="\U0001f5d1 Sil / Delete", callback_data=f"alert:delete:{alert_id}")])
    buttons.append([
        InlineKeyboardButton(text="\u2b05\ufe0f Geri / Back", callback_data="alert:list"),
        InlineKeyboardButton(text="\U0001f3e0 Menyu / Menu", callback_data="menu:main"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def alert_edit_keyboard(alert_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="\U0001f4b0 Qiym\u0259ti d\u0259yi\u015f",
            callback_data=f"alert:editprice:{alert_id}",
        )],
        [InlineKeyboardButton(
            text="\U0001f3ea Ma\u011fazalar\u0131 d\u0259yi\u015f",
            callback_data=f"alert:editstores:{alert_id}",
        )],
        [InlineKeyboardButton(
            text="\U0001f4c2 Kateqoriyan\u0131 d\u0259yi\u015f",
            callback_data=f"alert:editcat:{alert_id}",
        )],
        [InlineKeyboardButton(
            text="\u2b05\ufe0f Geri",
            callback_data=f"alert:view:{alert_id}",
        )],
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
        [
            InlineKeyboardButton(text="\u2699\ufe0f T\u0259nziml\u0259m\u0259l\u0259r", callback_data="menu:settings"),
            InlineKeyboardButton(text="\u2139\ufe0f K\u00f6m\u0259k", callback_data="menu:help"),
        ],
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


def settings_keyboard() -> InlineKeyboardMarkup:
    """Main settings menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="\U0001f515 Sakit saatlar / Quiet hours",
            callback_data="settings:quiethours",
        )],
        [InlineKeyboardButton(text="\u2b05\ufe0f Menyu", callback_data="menu:main")],
    ])


def quiet_hours_keyboard() -> InlineKeyboardMarkup:
    """Quiet hours sub-menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="\U0001f319 T\u0259yin et / Set",
            callback_data="settings:quietset",
        )],
        [InlineKeyboardButton(
            text="\U0001f5d1 S\u00f6nd\u00fcr / Disable",
            callback_data="settings:quietoff",
        )],
        [InlineKeyboardButton(text="\u2b05\ufe0f Geri", callback_data="menu:settings")],
    ])


def price_drop_keyboard() -> InlineKeyboardMarkup:
    """Shown in price drop notifications."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4cb Alertl\u0259rim\u0259 bax", callback_data="menu:myalerts")],
    ])


# ── Delete confirmation ──

def delete_confirmation_keyboard(alert_id: int) -> InlineKeyboardMarkup:
    """Confirmation screen before deleting an alert."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="\u2705 B\u0259li, sil / Yes, delete",
            callback_data=f"alert:confirmdelete:{alert_id}",
        )],
        [InlineKeyboardButton(
            text="\u274c Xeyr, geri / No, go back",
            callback_data=f"alert:view:{alert_id}",
        )],
    ])


# ── Onboarding ──

ONBOARDING_STEPS = {
    1: {
        "title": "\U0001f50d Axtar\u0131\u015f / Search",
        "text": (
            "M\u0259hsul ad\u0131n\u0131 yaz\u0131n \u2014 b\u00fct\u00fcn ma\u011fazalarda eyni anda axtar\u0131l\u0131r.\n\n"
            "Type a product name \u2014 all stores are searched at once.\n\n"
            "M\u0259s\u0259l\u0259n: \"iPhone 15\", \"Samsung TV\", \"Nike Air Max\""
        ),
    },
    2: {
        "title": "\U0001f4ca Alert / Price Alert",
        "text": (
            "H\u0259d\u0259f qiym\u0259t t\u0259yin edin \u2014 qiym\u0259t d\u00fc\u015f\u0259nd\u0259 sizə x\u0259b\u0259r ver\u0259c\u0259yik.\n\n"
            "Set a target price \u2014 we'll notify you when it drops.\n\n"
            "Maksimum 5 alert yarada bil\u0259rsiniz."
        ),
    },
    3: {
        "title": "\u2699\ufe0f T\u0259nziml\u0259m\u0259l\u0259r / Settings",
        "text": (
            "Sakit saatlar t\u0259yin edin \u2014 gec\u0259 vaxt\u0131 bildiri\u015f g\u00f6nd\u0259rilm\u0259sin.\n\n"
            "Set quiet hours \u2014 no notifications during the night.\n\n"
            "/settings komutu il\u0259 ist\u0259nil\u0259n vaxt d\u0259yi\u015f\u0259 bil\u0259rsiniz."
        ),
    },
}


def onboarding_keyboard(step: int) -> InlineKeyboardMarkup:
    """Navigation keyboard for onboarding steps."""
    if step < 3:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="N\u00f6vb\u0259ti \u27a1\ufe0f",
                callback_data=f"onboarding:{step + 1}",
            )],
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="Ba\u015fla! \U0001f680",
                callback_data="onboarding:done",
            )],
        ])


# ── Contextual tips ──

CONTEXTUAL_TIPS = {
    "after_alert_created": "\U0001f4a1 /settings il\u0259 sakit saatlar t\u0259yin ed\u0259 bil\u0259rsiniz",
    "search_no_results": "\U0001f4a1 Daha q\u0131sa a\u00e7ar s\u00f6zl\u0259r s\u0131nay\u0131n. M\u0259s: 'iphone 15 pro' \u0259v\u0259zin\u0259 'iphone 15'",
    "alert_detail": "\U0001f4a1 \u270f\ufe0f Redakt\u0259 il\u0259 h\u0259d\u0259f qiym\u0259ti d\u0259yi\u015f\u0259 bil\u0259rsiniz",
}


def maybe_tip(tip_key: str, chance: float = 0.3) -> str:
    """Return a contextual tip with given probability, else empty string."""
    if random.random() < chance:
        tip = CONTEXTUAL_TIPS.get(tip_key, "")
        return f"\n\n{tip}" if tip else ""
    return ""
