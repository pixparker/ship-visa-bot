"""
In-memory session store keyed by Telegram chat_id.
Each chat has one active VisaSession at a time.
Replace with Redis or a DB-backed store for multi-process deployments.
"""
from typing import Dict
from models import VisaSession

_sessions: Dict[int, VisaSession] = {}


def get_session(chat_id: int) -> VisaSession:
    if chat_id not in _sessions:
        _sessions[chat_id] = VisaSession()
    return _sessions[chat_id]


def reset_session(chat_id: int) -> VisaSession:
    _sessions[chat_id] = VisaSession()
    return _sessions[chat_id]
