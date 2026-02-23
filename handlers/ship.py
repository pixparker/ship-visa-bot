"""
Handlers for collecting ship details and routing information.
Each handler stores one field, replies with the next question, and advances the state.
"""
from telegram import Update
from telegram.ext import ContextTypes

import session_manager
from states import State
from utils.messages import (
    ASK_SHIP_OWNER, ASK_SHIP_IMO, ASK_SHIP_REG_DATE,
    ASK_ORIGIN, ASK_DESTINATION, ASK_CREW_FULLNAME,
)


async def ship_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    s = session_manager.get_session(update.effective_chat.id)
    s.ship.name = update.message.text.strip()
    await update.message.reply_text(ASK_SHIP_OWNER)
    return State.SHIP_OWNER


async def ship_owner(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    s = session_manager.get_session(update.effective_chat.id)
    s.ship.owner = update.message.text.strip()
    await update.message.reply_text(ASK_SHIP_IMO)
    return State.SHIP_IMO


async def ship_imo(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    s = session_manager.get_session(update.effective_chat.id)
    s.ship.imo_number = update.message.text.strip()
    await update.message.reply_text(ASK_SHIP_REG_DATE)
    return State.SHIP_REG_DATE


async def ship_reg_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    s = session_manager.get_session(update.effective_chat.id)
    s.ship.registration_date = update.message.text.strip()
    await update.message.reply_text(ASK_ORIGIN)
    return State.ORIGIN


async def routing_origin(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    s = session_manager.get_session(update.effective_chat.id)
    s.routing.origin = update.message.text.strip()
    await update.message.reply_text(ASK_DESTINATION)
    return State.DESTINATION


async def routing_destination(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    s = session_manager.get_session(update.effective_chat.id)
    s.routing.destination = update.message.text.strip()
    await update.message.reply_text(
        "اطلاعات مسیر ثبت شد. ✅\n\n"
        "اکنون اطلاعات خدمه را وارد کنید.\n\n" + ASK_CREW_FULLNAME
    )
    return State.CREW_FULLNAME
