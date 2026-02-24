"""
In-memory session store keyed by chat_id (Telegram or sandbox).
Each chat has one active VisaSession and one conversation state.
Replace with Redis or a DB-backed store for multi-process deployments.
"""
from typing import Dict, Optional

from models import VisaSession
from states import State

_sessions: Dict[int, VisaSession] = {}
_states: Dict[int, State] = {}


def get_session(chat_id: int) -> VisaSession:
    if chat_id not in _sessions:
        _sessions[chat_id] = VisaSession()
    return _sessions[chat_id]


def reset_session(chat_id: int) -> VisaSession:
    _sessions[chat_id] = VisaSession()
    return _sessions[chat_id]


def get_state(chat_id: int) -> Optional[State]:
    return _states.get(chat_id)


def set_state(chat_id: int, state: Optional[State]) -> None:
    if state is None:
        _states.pop(chat_id, None)
    else:
        _states[chat_id] = state
