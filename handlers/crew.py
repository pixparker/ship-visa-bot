"""
Handlers for collecting crew member information (looped for multiple crew).
"""
from telegram import Update
from telegram.ext import ContextTypes

import session_manager
from states import State
from utils.keyboards import gender_keyboard, yes_no_keyboard
from utils.messages import (
    ASK_CREW_PASSPORT, ASK_CREW_PASSPORT_EXPIRY,
    ASK_CREW_CDC, ASK_CREW_CDC_EXPIRY, ASK_CREW_GENDER,
    ASK_CREW_DOB, ASK_CREW_RANK, ASK_MORE_CREW, ASK_CREW_FULLNAME,
)


async def crew_fullname(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    s = session_manager.get_session(update.effective_chat.id)
    s.current_crew.full_name = update.message.text.strip()
    await update.message.reply_text(ASK_CREW_PASSPORT)
    return State.CREW_PASSPORT


async def crew_passport(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    s = session_manager.get_session(update.effective_chat.id)
    s.current_crew.passport_number = update.message.text.strip()
    await update.message.reply_text(ASK_CREW_PASSPORT_EXPIRY)
    return State.CREW_PASSPORT_EXPIRY


async def crew_passport_expiry(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    s = session_manager.get_session(update.effective_chat.id)
    s.current_crew.passport_expiry = update.message.text.strip()
    await update.message.reply_text(ASK_CREW_CDC)
    return State.CREW_CDC


async def crew_cdc(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    s = session_manager.get_session(update.effective_chat.id)
    s.current_crew.cdc_number = update.message.text.strip()
    await update.message.reply_text(ASK_CREW_CDC_EXPIRY)
    return State.CREW_CDC_EXPIRY


async def crew_cdc_expiry(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    s = session_manager.get_session(update.effective_chat.id)
    s.current_crew.cdc_expiry = update.message.text.strip()
    await update.message.reply_text(ASK_CREW_GENDER, reply_markup=gender_keyboard())
    return State.CREW_GENDER


async def crew_gender(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    gender = query.data.split(":", 1)[1]
    s = session_manager.get_session(query.message.chat_id)
    s.current_crew.gender = gender

    await query.edit_message_text(ASK_CREW_DOB)
    return State.CREW_DOB


async def crew_dob(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    s = session_manager.get_session(update.effective_chat.id)
    s.current_crew.date_of_birth = update.message.text.strip()
    await update.message.reply_text(ASK_CREW_RANK)
    return State.CREW_RANK


async def crew_rank(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    s = session_manager.get_session(update.effective_chat.id)
    s.current_crew.rank = update.message.text.strip()
    s.add_current_crew()

    count = len(s.crew)
    await update.message.reply_text(
        f"اطلاعات خدمه شماره {count} ثبت شد. ✅\n\n" + ASK_MORE_CREW,
        reply_markup=yes_no_keyboard(),
    )
    return State.ADD_MORE_CREW


async def add_more_crew(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "more_crew:yes":
        await query.edit_message_text(ASK_CREW_FULLNAME)
        return State.CREW_FULLNAME
    else:
        # Proceed to confirmation
        from handlers.confirm import show_confirmation
        return await show_confirmation(query)
