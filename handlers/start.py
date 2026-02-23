"""
/start command and visa-type selection.
"""
from telegram import Update
from telegram.ext import ContextTypes

import session_manager
from states import State
from utils.keyboards import visa_type_keyboard
from utils.messages import WELCOME, RESTARTED


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point. Reset any existing session and ask for visa type."""
    chat_id = update.effective_chat.id
    session_manager.reset_session(chat_id)

    text = WELCOME if update.message.text == "/start" else RESTARTED
    await update.message.reply_text(text, reply_markup=visa_type_keyboard())
    return State.VISA_TYPE


async def handle_visa_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the selected visa type and ask for ship name."""
    query = update.callback_query
    await query.answer()

    visa_type = query.data.split(":", 1)[1]
    session = session_manager.get_session(query.message.chat_id)
    session.visa_type = visa_type

    await query.edit_message_text(
        f"نوع ویزا: *{visa_type}*\n\nلطفاً اطلاعات کشتی را وارد کنید.\n\nنام کشتی را وارد کنید:",
        parse_mode="Markdown",
    )
    return State.SHIP_NAME
