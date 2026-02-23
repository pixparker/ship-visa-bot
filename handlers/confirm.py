"""
Confirmation step and document generation/delivery.
"""
import logging
import os
from telegram import Update
from telegram.ext import ContextTypes

import session_manager
from states import State
from utils.keyboards import confirm_keyboard
from utils.messages import (
    CONFIRM_PROMPT, GENERATING, DOCS_READY,
    CANCELLED, ERROR_GENERAL, ERROR_PDF,
)
from documents.generator import generate_documents

logger = logging.getLogger(__name__)


async def show_confirmation(query_or_update) -> int:
    """
    Called after the user says 'no more crew'.
    Accepts either a CallbackQuery (from crew.py) or an Update (direct use).
    """
    if hasattr(query_or_update, "message"):
        # It's a CallbackQuery
        chat_id = query_or_update.message.chat_id
        edit_fn = query_or_update.edit_message_text
    else:
        # It's an Update object
        chat_id = query_or_update.effective_chat.id
        edit_fn = query_or_update.message.reply_text

    s = session_manager.get_session(chat_id)
    text = CONFIRM_PROMPT.format(summary=s.summary())
    await edit_fn(text, parse_mode="Markdown", reply_markup=confirm_keyboard())
    return State.CONFIRM


async def handle_confirmation(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "confirm:no":
        await query.edit_message_text(CANCELLED)
        return -1  # ConversationHandler.END

    chat_id = query.message.chat_id
    s = session_manager.get_session(chat_id)

    # Notify the user we are processing
    await query.edit_message_text(GENERATING)

    try:
        word_path, pdf_path = generate_documents(s, chat_id)
    except Exception:
        logger.exception("Document generation failed")
        await ctx.bot.send_message(chat_id, ERROR_GENERAL)
        return -1

    await ctx.bot.send_message(chat_id, DOCS_READY)

    # Send Word file
    with open(word_path, "rb") as f:
        await ctx.bot.send_document(chat_id, document=f, filename=os.path.basename(word_path))

    # Send PDF file (if available)
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            await ctx.bot.send_document(chat_id, document=f, filename=os.path.basename(pdf_path))
    else:
        await ctx.bot.send_message(chat_id, ERROR_PDF)

    # Clean up generated files
    for path in [word_path, pdf_path]:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

    session_manager.reset_session(chat_id)
    return -1  # ConversationHandler.END
