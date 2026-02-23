"""
Reusable InlineKeyboard builders.
Add new keyboard factories here as the bot grows.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ── Visa types ────────────────────────────────────────────────────────────────
VISA_TYPES: list[str] = [
    "۷۲ ساعته ورود",
    "۷۲ ساعته خروج",
    "ترانزیت",
    "سایر",
]


def visa_type_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(vt, callback_data=f"visa_type:{vt}")]
        for vt in VISA_TYPES
    ]
    return InlineKeyboardMarkup(buttons)


# ── Gender ────────────────────────────────────────────────────────────────────
def gender_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("مرد", callback_data="gender:مرد"),
            InlineKeyboardButton("زن", callback_data="gender:زن"),
        ]
    ])


# ── Yes / No ──────────────────────────────────────────────────────────────────
def yes_no_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ بله", callback_data="more_crew:yes"),
            InlineKeyboardButton("❌ خیر", callback_data="more_crew:no"),
        ]
    ])


# ── Confirm / Cancel ──────────────────────────────────────────────────────────
def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تایید و صدور نامه", callback_data="confirm:yes"),
            InlineKeyboardButton("❌ لغو", callback_data="confirm:no"),
        ]
    ])
