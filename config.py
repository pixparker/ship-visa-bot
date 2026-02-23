import os
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]

# Optional: restrict bot to specific Telegram user IDs
_raw = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS: List[int] = [int(uid) for uid in _raw.split(",") if uid.strip()]

# Optional: HTTP/SOCKS5 proxy (required in Iran)
# Examples:
#   PROXY_URL=http://127.0.0.1:8118
#   PROXY_URL=socks5://127.0.0.1:1080
PROXY_URL: Optional[str] = os.getenv("PROXY_URL") or None

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, "documents", "templates", "visa_letter.docx")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

os.makedirs(OUTPUT_DIR, exist_ok=True)
