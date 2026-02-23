# Ship Visa Bot

ربات تلگرام برای صدور خودکار نامه درخواست ویزای خدمه کشتی.

---

## راه‌اندازی سریع

### ۱. پیش‌نیازها

- Python 3.11+
- LibreOffice (برای تبدیل Word به PDF)
- توکن ربات تلگرام از [@BotFather](https://t.me/BotFather)

### ۲. نصب

```bash
git clone <repo-url>
cd ship-visa-bot

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### ۳. تنظیمات

```bash
cp .env.example .env
# سپس توکن ربات را در .env وارد کنید:
# BOT_TOKEN=your_token_here
```

### ۴. ساخت قالب Word

```bash
python documents/create_template.py
```

این دستور فایل `documents/templates/visa_letter.docx` را می‌سازد.
می‌توانید آن را در Word/LibreOffice باز کرده و ظاهر را شخصی‌سازی کنید — فقط `{{ placeholders }}` را دست نزنید.

### ۵. اجرا

```bash
python bot.py
```

---

## اجرا با Docker

```bash
cp .env.example .env
# BOT_TOKEN را پر کنید

docker compose up --build -d
```

---

## ساختار پروژه

```
ship-visa-bot/
├── bot.py                  ← نقطه ورود اصلی + ConversationHandler
├── config.py               ← متغیرهای محیطی
├── states.py               ← State enum (هر قدم wizard یک عدد)
├── models.py               ← VisaSession, ShipDetails, CrewMember
├── session_manager.py      ← ذخیره‌سازی موقت داده‌های هر چت
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
│
├── handlers/
│   ├── start.py            ← /start و انتخاب نوع ویزا
│   ├── ship.py             ← اطلاعات کشتی و مسیر
│   ├── crew.py             ← حلقه دریافت اطلاعات خدمه
│   └── confirm.py          ← تایید نهایی و صدور اسناد
│
├── documents/
│   ├── generator.py        ← پر کردن قالب Word + تبدیل به PDF
│   ├── create_template.py  ← ساختن قالب (یک بار اجرا شود)
│   └── templates/
│       └── visa_letter.docx
│
└── utils/
    ├── keyboards.py        ← InlineKeyboard ها
    └── messages.py         ← تمام متن‌های نمایش داده شده به کاربر
```

---

## اضافه کردن قابلیت جدید

| کار | فایل |
|-----|------|
| افزودن نوع ویزای جدید | `utils/keyboards.py` → `VISA_TYPES` |
| تغییر متن پیام‌ها | `utils/messages.py` |
| افزودن فیلد جدید به خدمه | `models.py` + یک State جدید + یک handler در `handlers/crew.py` + فیلد در قالب |
| تغییر ظاهر نامه | `documents/templates/visa_letter.docx` |
| استفاده از Gotenberg برای PDF | `documents/generator.py` → `_convert_to_pdf` |

---

## متغیرهای قالب Word

| متغیر | توضیح |
|--------|--------|
| `{{ issue_date }}` | تاریخ صدور |
| `{{ visa_type }}` | نوع ویزا |
| `{{ ship_name }}` | نام کشتی |
| `{{ ship_owner }}` | مالک کشتی |
| `{{ ship_imo }}` | شماره IMO |
| `{{ ship_reg_date }}` | تاریخ ثبت |
| `{{ origin }}` | مبدا |
| `{{ destination }}` | مقصد |
| `{{ crew_count }}` | تعداد خدمه |
| `{% tr for member in crew %}` | شروع حلقه خدمه در جدول |
| `{{ member.full_name }}` و سایر فیلدها | داده‌های هر خدمه |
| `{% tr endfor %}` | پایان حلقه |

---

## نیازمندی‌های PDF

روی سرور لینوکس:

```bash
apt-get install libreoffice
```

روی مک:

```bash
brew install libreoffice
```
# ship-visa-bot
