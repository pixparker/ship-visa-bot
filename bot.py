"""
Entry point for the Ship Visa Telegram Bot.

Architecture
─────────────
bot.py                  ← start here
├── handlers/
│   ├── start.py        ← /start, visa type selection
│   ├── ship.py         ← ship & routing info collection
│   ├── crew.py         ← crew member loop
│   └── confirm.py      ← summary + document generation
├── documents/
│   ├── generator.py    ← docxtpl Word + LibreOffice PDF
│   └── create_template.py  ← one-time template builder
├── utils/
│   ├── keyboards.py    ← InlineKeyboard factories
│   └── messages.py     ← all user-facing strings
├── models.py           ← VisaSession, ShipDetails, CrewMember …
├── session_manager.py  ← in-memory chat state store
├── states.py           ← State enum
└── config.py           ← env vars & paths
"""
import os
import logging

# Tell httpx to bypass system proxy (Shadowrocket/VPN HTTP proxy at 1082)
# for Telegram's API. Shadowrocket TUN mode handles routing at kernel level,
# so no explicit proxy is needed. Without this, httpx picks up the macOS
# system proxy and the TLS handshake times out.
os.environ.setdefault("NO_PROXY", "api.telegram.org")

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    TypeHandler,
    filters,
)

from config import BOT_TOKEN, ALLOWED_USER_IDS, PROXY_URL
from states import State
from handlers.start import start, handle_visa_type
from handlers.ship import (
    ship_name, ship_owner, ship_imo, ship_reg_date,
    routing_origin, routing_destination,
)
from handlers.crew import (
    crew_fullname, crew_passport, crew_passport_expiry,
    crew_cdc, crew_cdc_expiry, crew_gender, crew_dob,
    crew_rank, add_more_crew,
)
from handlers.confirm import handle_confirmation
from utils.messages import CANCELLED

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ── Access control (optional) ─────────────────────────────────────────────────
def _allowed(update, ctx) -> bool:
    if not ALLOWED_USER_IDS:
        return True
    return update.effective_user.id in ALLOWED_USER_IDS


TEXT = filters.TEXT & ~filters.COMMAND


async def _log_update(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Log every incoming update to the console (group=-1 runs before all other handlers)."""
    user = update.effective_user
    user_info = f"{user.full_name} (id={user.id})" if user else "unknown"

    if update.message:
        logger.info("[MSG] %s → %s", user_info, update.message.text or update.message.document)
    elif update.callback_query:
        logger.info("[BTN] %s → %s", user_info, update.callback_query.data)


def build_conversation_handler() -> ConversationHandler:
    """
    Single ConversationHandler that covers the entire wizard.
    Adding a new step = add a new State + handler here.
    """
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            State.VISA_TYPE: [
                CallbackQueryHandler(handle_visa_type, pattern=r"^visa_type:")
            ],
            # ── Ship info ──────────────────────────────────────────────────
            State.SHIP_NAME: [MessageHandler(TEXT, ship_name)],
            State.SHIP_OWNER: [MessageHandler(TEXT, ship_owner)],
            State.SHIP_IMO: [MessageHandler(TEXT, ship_imo)],
            State.SHIP_REG_DATE: [MessageHandler(TEXT, ship_reg_date)],
            # ── Routing ────────────────────────────────────────────────────
            State.ORIGIN: [MessageHandler(TEXT, routing_origin)],
            State.DESTINATION: [MessageHandler(TEXT, routing_destination)],
            # ── Crew loop ──────────────────────────────────────────────────
            State.CREW_FULLNAME: [MessageHandler(TEXT, crew_fullname)],
            State.CREW_PASSPORT: [MessageHandler(TEXT, crew_passport)],
            State.CREW_PASSPORT_EXPIRY: [MessageHandler(TEXT, crew_passport_expiry)],
            State.CREW_CDC: [MessageHandler(TEXT, crew_cdc)],
            State.CREW_CDC_EXPIRY: [MessageHandler(TEXT, crew_cdc_expiry)],
            State.CREW_GENDER: [
                CallbackQueryHandler(crew_gender, pattern=r"^gender:")
            ],
            State.CREW_DOB: [MessageHandler(TEXT, crew_dob)],
            State.CREW_RANK: [MessageHandler(TEXT, crew_rank)],
            State.ADD_MORE_CREW: [
                CallbackQueryHandler(add_more_crew, pattern=r"^more_crew:")
            ],
            # ── Confirmation ───────────────────────────────────────────────
            State.CONFIRM: [
                CallbackQueryHandler(handle_confirmation, pattern=r"^confirm:")
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("cancel", _cancel),
        ],
        # Re-raise exceptions so they are visible in logs
        # allow_reentry=True lets users restart mid-flow via /start
        allow_reentry=True,
    )


async def _cancel(update, ctx) -> int:
    await update.message.reply_text(CANCELLED)
    return ConversationHandler.END


def main() -> None:
    builder = Application.builder().token(BOT_TOKEN)
    if PROXY_URL:
        builder = builder.proxy(PROXY_URL).get_updates_proxy(PROXY_URL)
    app = builder.build()
    app.add_handler(TypeHandler(Update, _log_update), group=-1)
    app.add_handler(build_conversation_handler())

    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
