"""
Core brain: conversation logic independent of Telegram, sandbox UI, or CLI.

Use process(chat_id, event) to get a list of responses to send.
"""

from core.brain import process
from core.responses import (
    ReplyText,
    EditMessage,
    SendDocument,
    AnswerCallback,
)

__all__ = [
    'process',
    'ReplyText',
    'EditMessage',
    'SendDocument',
    'AnswerCallback',
]
