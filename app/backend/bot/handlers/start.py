from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.backend.bot.keyboards import (
    BTN_HELP,
    BTN_MY_ALERTS,
    BTN_NEW_ALERT,
    BTN_SEARCH,
    cancel_inline_keyboard,
    main_menu_inline,
    main_menu_keyboard,
    start_actions_inline,
)
from app.backend.db.base import async_session_factory
from app.backend.services.alert_service import get_or_create_user

router = Router()

WELCOME_MESSAGE = (
    "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
    "\U0001f916  UcuzBot\n"
    "Qiym\u0259t \u0130zl\u0259yici / Price Tracker\n"
    "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
    "Xo\u015f g\u0259ldiniz, {first_name}! \U0001f44b\n\n"
    "Az\u0259rbaycan ma\u011fazalar\u0131nda \u0259n ucuz qiym\u0259ti tap\u0131n:\n"
    "\U0001f3ea Kontakt \u00b7 Baku Electronics \u00b7 Irshad \u00b7 Maxi.az \u00b7 Tap.az \u00b7 Umico\n\n"
    "\U0001f4cc Nec\u0259 istifad\u0259 etm\u0259li:\n"
    "1\ufe0f\u20e3 M\u0259hsul ad\u0131n\u0131 yaz\u0131n \u2014 avtomatik axtar\u0131\u015f ba\u015flayar\n"
    "2\ufe0f\u20e3 H\u0259d\u0259f qiym\u0259t t\u0259yin edin\n"
    "3\ufe0f\u20e3 Qiym\u0259t d\u00fc\u015f\u0259nd\u0259 x\u0259b\u0259rdarl\u0131q al\u0131n!\n\n"
    "\U0001f447 A\u015fa\u011f\u0131dak\u0131 d\u00fcym\u0259l\u0259rd\u0259n ba\u015flay\u0131n:"
)

HELP_MESSAGE = (
    "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
    "\u2139\ufe0f  UcuzBot K\u00f6m\u0259k / Help\n"
    "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
    "\U0001f50d  M\u0259hsul axtarma\n"
    "   Sad\u0259c\u0259 m\u0259hsul ad\u0131n\u0131 yaz\u0131n v\u0259 ya \"\U0001f50d Axtar\" d\u00fcym\u0259sin\u0259 bas\u0131n.\n"
    "   B\u00fct\u00fcn ma\u011fazalarda eyni anda axtar\u0131\u015f apar\u0131l\u0131r.\n\n"
    "\U0001f4ca  Qiym\u0259t alert\u0259\n"
    "   \"\U0001f4ca Yeni Alert\" d\u00fcym\u0259sin\u0259 bas\u0131n.\n"
    "   M\u0259hsul ad\u0131 v\u0259 h\u0259d\u0259f qiym\u0259t daxil edin \u2014 qiym\u0259t d\u00fc\u015f\u0259nd\u0259\n"
    "   avtomatik x\u0259b\u0259rdarl\u0131q alacaqs\u0131n\u0131z.\n\n"
    "\U0001f4cb  Alertl\u0259rim\n"
    "   \"\U0001f4cb Alertl\u0259rim\" d\u00fcym\u0259si il\u0259 aktiv alertl\u0259rinizi g\u00f6r\u00fcn,\n"
    "   t\u0259f\u0259rr\u00fcat\u0131na bax\u0131n v\u0259 ya silin.\n\n"
    "\U0001f4a1 Pulsuz hesab: 5 alert limiti\n"
    "\U0001f310 ucuzbot.az"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    async with async_session_factory() as session:
        await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            language_code=message.from_user.language_code or "az",
        )
        await session.commit()
    first_name = message.from_user.first_name or "dostum"
    await message.answer(
        WELCOME_MESSAGE.format(first_name=first_name),
        reply_markup=main_menu_keyboard(),
    )
    await message.answer("N\u0259 etm\u0259k ist\u0259yirsiniz?", reply_markup=start_actions_inline())


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_MESSAGE, reply_markup=main_menu_inline())


# ── Reply keyboard button handlers ──

@router.message(F.text == BTN_SEARCH)
async def reply_btn_search(message: Message, state: FSMContext):
    from app.backend.bot.handlers.search import SearchFlow

    await state.clear()
    await state.set_state(SearchFlow.waiting_for_query)
    await message.answer(
        "\U0001f50d M\u0259hsul ad\u0131n\u0131 yaz\u0131n:\n"
        "Type the product name:",
        reply_markup=cancel_inline_keyboard(),
    )


@router.message(F.text == BTN_NEW_ALERT)
async def reply_btn_alert(message: Message, state: FSMContext):
    from app.backend.bot.handlers.alerts import AlertCreation

    await state.set_state(AlertCreation.waiting_for_query)
    await message.answer(
        "\U0001f50d Hans\u0131 m\u0259hsulu izl\u0259m\u0259k ist\u0259yirsiniz?\n"
        "What product do you want to track?",
        reply_markup=cancel_inline_keyboard(),
    )


@router.message(F.text == BTN_MY_ALERTS)
async def reply_btn_myalerts(message: Message):
    from app.backend.bot.handlers.alerts import cmd_myalerts

    await cmd_myalerts(message)


@router.message(F.text == BTN_HELP)
async def reply_btn_help(message: Message):
    await cmd_help(message)
