"""
Entry point for the Ship Visa Telegram Bot.

Architecture
────────────
- core/brain.py   → business logic (state machine, session, responses). UI-agnostic.
- bot.py          → Telegram adapter: receives updates, calls brain, sends responses.
- sandbox/server  → sandbox adapter: can run brain in-process or proxy to bot.
"""
import os
import logging

os.environ.setdefault('NO_PROXY', 'api.telegram.org')

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, TypeHandler

from config import BOT_TOKEN, ALLOWED_USER_IDS, PROXY_URL
from core.brain import process
from core.responses import ReplyText, EditMessage, SendDocument, AnswerCallback

logging.basicConfig(
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def _allowed(update: Update) -> bool:
    if not ALLOWED_USER_IDS:
        return True
    return update.effective_user.id in ALLOWED_USER_IDS


def _to_markup(rows):
    """Convert core keyboard (list of list of {text, callback_data}) to InlineKeyboardMarkup."""
    if not rows:
        return None
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(b['text'], callback_data=b['callback_data']) for b in row]
        for row in rows
    ])


def _update_to_event(update: Update):
    """Turn a Telegram Update into a brain event (message or callback)."""
    if update.message:
        return {'type': 'message', 'text': (update.message.text or '')}
    if update.callback_query:
        return {
            'type': 'callback',
            'data': update.callback_query.data or '',
            'message_id': update.callback_query.message.message_id,
        }
    return None


async def _handle_update(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Single handler: delegate to brain and apply responses to Telegram."""
    if not _allowed(update):
        return

    user = update.effective_user
    user_info = f'{user.full_name} (id={user.id})' if user else 'unknown'
    if update.message:
        logger.info('[MSG] %s → %s', user_info, update.message.text or update.message.document)
    elif update.callback_query:
        logger.info('[BTN] %s → %s', user_info, update.callback_query.data)

    event = _update_to_event(update)
    if not event:
        return

    chat_id = update.effective_chat.id
    callback_message_id = None
    if update.callback_query:
        callback_message_id = update.callback_query.message.message_id

    responses = process(chat_id, event)

    for r in responses:
        if isinstance(r, AnswerCallback):
            if update.callback_query:
                await update.callback_query.answer()
            continue
        if isinstance(r, ReplyText):
            await ctx.bot.send_message(
                chat_id,
                r.text,
                parse_mode=r.parse_mode or None,
                reply_markup=_to_markup(r.reply_markup),
            )
            continue
        if isinstance(r, EditMessage):
            mid = r.message_id or callback_message_id
            if mid is not None:
                await ctx.bot.edit_message_text(
                    r.text,
                    chat_id=chat_id,
                    message_id=mid,
                    parse_mode=r.parse_mode or None,
                    reply_markup=_to_markup(r.reply_markup),
                )
            else:
                await ctx.bot.send_message(
                    chat_id,
                    r.text,
                    parse_mode=r.parse_mode or None,
                    reply_markup=_to_markup(r.reply_markup),
                )
            continue
        if isinstance(r, SendDocument):
            with open(r.file_path, 'rb') as f:
                await ctx.bot.send_document(
                    chat_id,
                    document=f,
                    filename=r.filename,
                    caption=r.caption or None,
                )
            continue


def main() -> None:
    sandbox_mode = os.getenv('SANDBOX_MODE')
    token = os.getenv('BOT_TOKEN', 'sandbox') if sandbox_mode else BOT_TOKEN
    builder = Application.builder().token(token)

    sandbox_port = os.getenv('SANDBOX_PORT', '8888')

    if sandbox_mode:
        base = f'http://127.0.0.1:{sandbox_port}/bot'
        builder = builder.base_url(base).base_file_url(f'http://127.0.0.1:{sandbox_port}/file/bot')
        logger.info('🔧 SANDBOX MODE – fake API at %s', base)
    elif PROXY_URL:
        builder = builder.proxy(PROXY_URL).get_updates_proxy(PROXY_URL)

    app = builder.build()
    app.add_handler(TypeHandler(Update, _handle_update))

    logger.info('Bot is running. Press Ctrl+C to stop.')
    app.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()
