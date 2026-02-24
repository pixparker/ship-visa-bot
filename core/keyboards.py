"""
Inline keyboard structures as plain data (no Telegram dependency).
Each function returns a list of rows; each row is a list of {text, callback_data}.
"""
from typing import List

# Must match utils/keyboards.py VISA_TYPES
VISA_TYPES = [
    '۷۲ ساعته ورود',
    '۷۲ ساعته خروج',
    'ترانزیت',
    'سایر',
]


def visa_type_keyboard() -> List[List[dict]]:
    return [[{'text': vt, 'callback_data': f'visa_type:{vt}'}] for vt in VISA_TYPES]


def gender_keyboard() -> List[List[dict]]:
    return [
        [
            {'text': 'مرد', 'callback_data': 'gender:مرد'},
            {'text': 'زن', 'callback_data': 'gender:زن'},
        ]
    ]


def yes_no_keyboard() -> List[List[dict]]:
    return [
        [
            {'text': '✅ بله', 'callback_data': 'more_crew:yes'},
            {'text': '❌ خیر', 'callback_data': 'more_crew:no'},
        ]
    ]


def confirm_keyboard() -> List[List[dict]]:
    return [
        [
            {'text': '✅ تایید و صدور نامه', 'callback_data': 'confirm:yes'},
            {'text': '❌ لغو', 'callback_data': 'confirm:no'},
        ]
    ]
