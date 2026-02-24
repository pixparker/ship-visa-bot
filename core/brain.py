"""
Brain: pure conversation logic. No Telegram or UI dependencies.

Input: chat_id, event (message or callback).
Output: list of Response objects for the adapter to send.
"""
import logging
import os
from typing import List, Union

import session_manager
from states import State

from core.keyboards import (
    visa_type_keyboard,
    gender_keyboard,
    yes_no_keyboard,
    confirm_keyboard,
)
from core.responses import (
    ReplyText,
    EditMessage,
    SendDocument,
    AnswerCallback,
)
from utils.messages import (
    WELCOME,
    RESTARTED,
    PLEASE_START,
    ASK_SHIP_NAME,
    ASK_SHIP_OWNER,
    ASK_SHIP_IMO,
    ASK_SHIP_REG_DATE,
    ASK_ORIGIN,
    ASK_DESTINATION,
    ASK_CREW_FULLNAME,
    ASK_CREW_PASSPORT,
    ASK_CREW_PASSPORT_EXPIRY,
    ASK_CREW_CDC,
    ASK_CREW_CDC_EXPIRY,
    ASK_CREW_GENDER,
    ASK_CREW_DOB,
    ASK_CREW_RANK,
    ASK_MORE_CREW,
    CONFIRM_PROMPT,
    GENERATING,
    DOCS_READY,
    CANCELLED,
    ERROR_GENERAL,
    ERROR_PDF,
)

logger = logging.getLogger(__name__)

# Type for event: either a text message or a callback
MessageEvent = dict  # {"type": "message", "text": str}
CallbackEvent = dict  # {"type": "callback", "data": str, "message_id": int}


def process(
    chat_id: int,
    event: Union[MessageEvent, CallbackEvent],
) -> List[Union[ReplyText, EditMessage, SendDocument, AnswerCallback]]:
    """
    Process one user event and return a list of responses to send.

    event["type"] is "message" or "callback".
    For "message": event["text"] is the message text.
    For "callback": event["data"] is callback_data, event.get("message_id") may be set by adapter.
    """
    out: List[Union[ReplyText, EditMessage, SendDocument, AnswerCallback]] = []
    ev_type = event.get('type')
    state = session_manager.get_state(chat_id)

    # ── Not in conversation: only /start is accepted ──
    if state is None:
        if ev_type == 'message' and (event.get('text') or '').strip() == '/start':
            session_manager.reset_session(chat_id)
            session_manager.set_state(chat_id, State.VISA_TYPE)
            out.append(ReplyText(WELCOME, reply_markup=visa_type_keyboard()))
        else:
            out.append(ReplyText(PLEASE_START))
        return out

    # ── Message: /start restarts, /cancel cancels; else handle by state ──
    if ev_type == 'message':
        text = (event.get('text') or '').strip()
        if text == '/start':
            session_manager.reset_session(chat_id)
            session_manager.set_state(chat_id, State.VISA_TYPE)
            out.append(ReplyText(RESTARTED, reply_markup=visa_type_keyboard()))
            return out
        if text == '/cancel':
            session_manager.set_state(chat_id, None)
            out.append(ReplyText(CANCELLED))
            return out

        s = session_manager.get_session(chat_id)

        if state == State.SHIP_NAME:
            s.ship.name = text
            session_manager.set_state(chat_id, State.SHIP_OWNER)
            out.append(ReplyText(ASK_SHIP_OWNER))
            return out
        if state == State.SHIP_OWNER:
            s.ship.owner = text
            session_manager.set_state(chat_id, State.SHIP_IMO)
            out.append(ReplyText(ASK_SHIP_IMO))
            return out
        if state == State.SHIP_IMO:
            s.ship.imo_number = text
            session_manager.set_state(chat_id, State.SHIP_REG_DATE)
            out.append(ReplyText(ASK_SHIP_REG_DATE))
            return out
        if state == State.SHIP_REG_DATE:
            s.ship.registration_date = text
            session_manager.set_state(chat_id, State.ORIGIN)
            out.append(ReplyText(ASK_ORIGIN))
            return out
        if state == State.ORIGIN:
            s.routing.origin = text
            session_manager.set_state(chat_id, State.DESTINATION)
            out.append(ReplyText(ASK_DESTINATION))
            return out
        if state == State.DESTINATION:
            s.routing.destination = text
            session_manager.set_state(chat_id, State.CREW_FULLNAME)
            out.append(ReplyText(
                'اطلاعات مسیر ثبت شد. ✅\n\n'
                'اکنون اطلاعات خدمه را وارد کنید.\n\n' + ASK_CREW_FULLNAME
            ))
            return out
        if state == State.CREW_FULLNAME:
            s.current_crew.full_name = text
            session_manager.set_state(chat_id, State.CREW_PASSPORT)
            out.append(ReplyText(ASK_CREW_PASSPORT))
            return out
        if state == State.CREW_PASSPORT:
            s.current_crew.passport_number = text
            session_manager.set_state(chat_id, State.CREW_PASSPORT_EXPIRY)
            out.append(ReplyText(ASK_CREW_PASSPORT_EXPIRY))
            return out
        if state == State.CREW_PASSPORT_EXPIRY:
            s.current_crew.passport_expiry = text
            session_manager.set_state(chat_id, State.CREW_CDC)
            out.append(ReplyText(ASK_CREW_CDC))
            return out
        if state == State.CREW_CDC:
            s.current_crew.cdc_number = text
            session_manager.set_state(chat_id, State.CREW_CDC_EXPIRY)
            out.append(ReplyText(ASK_CREW_CDC_EXPIRY))
            return out
        if state == State.CREW_CDC_EXPIRY:
            s.current_crew.cdc_expiry = text
            session_manager.set_state(chat_id, State.CREW_GENDER)
            out.append(ReplyText(ASK_CREW_GENDER, reply_markup=gender_keyboard()))
            return out
        if state == State.CREW_DOB:
            s.current_crew.date_of_birth = text
            session_manager.set_state(chat_id, State.CREW_RANK)
            out.append(ReplyText(ASK_CREW_RANK))
            return out
        if state == State.CREW_RANK:
            s.current_crew.rank = text
            s.add_current_crew()
            count = len(s.crew)
            session_manager.set_state(chat_id, State.ADD_MORE_CREW)
            out.append(ReplyText(
                f'اطلاعات خدمه شماره {count} ثبت شد. ✅\n\n' + ASK_MORE_CREW,
                reply_markup=yes_no_keyboard(),
            ))
            return out

        # Unhandled message in this state (e.g. VISA_TYPE expects callback)
        out.append(ReplyText(PLEASE_START))
        return out

    # ── Callback ──
    if ev_type != 'callback':
        return out

    data = event.get('data', '')
    out.append(AnswerCallback())

    if state == State.VISA_TYPE and data.startswith('visa_type:'):
        visa_type = data.split(':', 1)[1]
        s = session_manager.get_session(chat_id)
        s.visa_type = visa_type
        session_manager.set_state(chat_id, State.SHIP_NAME)
        out.append(EditMessage(
            f'نوع ویزا: *{visa_type}*\n\nلطفاً اطلاعات کشتی را وارد کنید.\n\nنام کشتی را وارد کنید:',
            parse_mode='Markdown',
        ))
        return out

    if state == State.CREW_GENDER and data.startswith('gender:'):
        gender = data.split(':', 1)[1]
        s = session_manager.get_session(chat_id)
        s.current_crew.gender = gender
        session_manager.set_state(chat_id, State.CREW_DOB)
        out.append(EditMessage(ASK_CREW_DOB))
        return out

    if state == State.ADD_MORE_CREW:
        if data == 'more_crew:yes':
            session_manager.set_state(chat_id, State.CREW_FULLNAME)
            out.append(EditMessage(ASK_CREW_FULLNAME))
            return out
        if data == 'more_crew:no':
            s = session_manager.get_session(chat_id)
            session_manager.set_state(chat_id, State.CONFIRM)
            text = CONFIRM_PROMPT.format(summary=s.summary())
            out.append(EditMessage(text, parse_mode='Markdown', reply_markup=confirm_keyboard()))
            return out

    if state == State.CONFIRM:
        if data == 'confirm:no':
            session_manager.set_state(chat_id, None)
            out.append(EditMessage(CANCELLED))
            return out
        if data == 'confirm:yes':
            s = session_manager.get_session(chat_id)
            out.append(EditMessage(GENERATING))
            try:
                from documents.generator import generate_documents
                word_path, pdf_path = generate_documents(s, chat_id)
            except Exception:
                logger.exception('Document generation failed')
                out.append(ReplyText(ERROR_GENERAL))
                session_manager.set_state(chat_id, None)
                return out

            out.append(ReplyText(DOCS_READY))
            out.append(SendDocument(word_path, os.path.basename(word_path)))

            if pdf_path and os.path.exists(pdf_path):
                out.append(SendDocument(pdf_path, os.path.basename(pdf_path)))
            else:
                out.append(ReplyText(ERROR_PDF))

            for path in [word_path, pdf_path]:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass

            session_manager.set_state(chat_id, None)
            return out

    return out
