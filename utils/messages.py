"""
All user-facing message strings.
Edit this file to change bot language/tone without touching handler logic.
"""

WELCOME = (
    "سلام! 👋\n"
    "به ربات صدور نامه ویزای خدمه کشتی خوش آمدید.\n\n"
    "لطفاً نوع ویزا را انتخاب کنید:"
)

ASK_SHIP_NAME = "نام کشتی را وارد کنید:"
ASK_SHIP_OWNER = "نام مالک کشتی را وارد کنید:"
ASK_SHIP_IMO = "شماره IMO کشتی را وارد کنید:"
ASK_SHIP_REG_DATE = "تاریخ ثبت کشتی را وارد کنید (مثال: ۲۰۲۳/۰۵/۱۵):"

ASK_ORIGIN = "مبدا سفر را وارد کنید (مثال: فرودگاه امام خمینی):"
ASK_DESTINATION = "مقصد سفر را وارد کنید (مثال: بندرعباس):"

ASK_CREW_FULLNAME = "نام و نام خانوادگی خدمه را وارد کنید:"
ASK_CREW_PASSPORT = "شماره پاسپورت را وارد کنید:"
ASK_CREW_PASSPORT_EXPIRY = "تاریخ انقضای پاسپورت را وارد کنید (مثال: ۲۰۲۶/۰۱/۰۱):"
ASK_CREW_CDC = "شماره سند دریانوردی (CDC) را وارد کنید:"
ASK_CREW_CDC_EXPIRY = "تاریخ انقضای CDC را وارد کنید (مثال: ۲۰۲۶/۰۱/۰۱):"
ASK_CREW_GENDER = "جنسیت را انتخاب کنید:"
ASK_CREW_DOB = "تاریخ تولد را وارد کنید (مثال: ۱۹۸۵/۰۳/۲۰):"
ASK_CREW_RANK = "سمت خدمه در کشتی را وارد کنید (مثال: کاپیتان، سرمهندس):"

ASK_MORE_CREW = "آیا خدمه دیگری نیز وجود دارد؟"

CONFIRM_PROMPT = "{summary}\n\n---\nآیا اطلاعات فوق صحیح است؟"

GENERATING = "⏳ در حال صدور اسناد، لطفاً صبر کنید..."
DOCS_READY = "✅ اسناد با موفقیت صادر شد:"

CANCELLED = "عملیات لغو شد. برای شروع مجدد /start را ارسال کنید."
PLEASE_START = "لطفاً برای شروع دستور /start را ارسال کنید."
RESTARTED = "فرآیند از ابتدا شروع شد. نوع ویزا را انتخاب کنید:"
ERROR_GENERAL = "⚠️ خطایی رخ داد. لطفاً /start را ارسال کنید و مجدداً تلاش کنید."
ERROR_PDF = "⚠️ فایل Word با موفقیت صادر شد اما تبدیل به PDF ممکن نبود.\nبرای تبدیل به PDF، LibreOffice را نصب کنید."
