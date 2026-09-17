import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATA_DIR = os.getenv("DATA_DIR", "./data")
DB_PATH = os.path.join(DATA_DIR, "db", "bot.sqlite3")
SANDBOX_ROOT = os.path.join(DATA_DIR, "sandboxes")
FERNET_KEY = os.getenv("FERNET_KEY", "")
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()}

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(SANDBOX_ROOT, exist_ok=True)

# پیش‌فرض‌های مصرف توکن (کاربر می‌تونه از تنظیمات تغییرشون بده)
DEFAULT_DAILY_TOKEN_LIMIT = 200_000
DEFAULT_MONTHLY_TOKEN_LIMIT = 3_000_000

MAX_TOOL_ITERATIONS = 6          # حداکثر دفعاتی که ایجنت می‌تونه پشت‌سرهم ابزار صدا بزنه
CODE_EXEC_TIMEOUT_SECONDS = 300  # تایم‌اوت پیش‌فرض اجرای کد (قابل تغییر در تنظیمات هر کاربر)
CHAT_LIST_PAGE_SIZE = 8
