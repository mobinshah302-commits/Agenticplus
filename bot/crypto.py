"""
رمزنگاری کلیدهای API کاربرها قبل از ذخیره در دیتابیس.
اگر FERNET_KEY در env ست نشده باشه، یک کلید تازه می‌سازیم و توی فایل کنار دیتابیس
ذخیره می‌کنیم تا بین ری‌استارت‌ها ثابت بمونه (وگرنه کلیدهای قبلی decrypt نمی‌شن).
"""
import os
from cryptography.fernet import Fernet
from . import config

_KEY_FILE = os.path.join(config.DATA_DIR, "db", ".fernet.key")


def _load_or_create_key() -> bytes:
    if config.FERNET_KEY:
        return config.FERNET_KEY.encode()
    if os.path.exists(_KEY_FILE):
        with open(_KEY_FILE, "rb") as f:
            return f.read().strip()
    key = Fernet.generate_key()
    os.makedirs(os.path.dirname(_KEY_FILE), exist_ok=True)
    with open(_KEY_FILE, "wb") as f:
        f.write(key)
    return key


_fernet = Fernet(_load_or_create_key())


def encrypt(text: str) -> str:
    return _fernet.encrypt(text.encode()).decode()


def decrypt(token: str) -> str:
    return _fernet.decrypt(token.encode()).decode()
