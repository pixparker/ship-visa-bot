"""
Response types returned by the brain. Adapters (Telegram, sandbox, CLI) translate these to their API.
"""
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class ReplyText:
    """Send a new message (e.g. reply to user)."""
    text: str
    parse_mode: str = ''
    reply_markup: Optional[List[List[dict]]] = None  # inline_keyboard: [[{text, callback_data}, ...], ...]


@dataclass
class EditMessage:
    """Edit an existing message (e.g. after inline button click)."""
    text: str
    parse_mode: str = ''
    reply_markup: Optional[List[List[dict]]] = None
    message_id: Optional[int] = None  # adapter may pass it from context


@dataclass
class SendDocument:
    """Send a file (e.g. generated Word/PDF)."""
    file_path: str
    filename: str
    caption: str = ''


@dataclass
class AnswerCallback:
    """Acknowledge a callback query (no-op for sandbox/CLI)."""
    pass
