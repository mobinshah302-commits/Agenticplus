# -*- coding: utf-8 -*-
"""
تشخیص حالت پیام: «ایجنت» (نیاز به ابزار/اقدام واقعی) یا «چت عادی».
مرحله‌ی اول یک هیوریستیک ارزون (بدون تماس با API) هست؛ فقط وقتی مبهم باشه یک تماس
کوچیک و ارزون به همون مدل کاربر می‌زنیم که فقط AGENT یا CHAT رو برگردونه.
"""
import re

AGENT_KEYWORDS = [
    # فارسی — اجرای کد / فایل / پروژه
    "کد", "اجرا کن", "اجراش کن", "دیباگ", "باگ", "ارور", "خطا", "اسکریپت", "پروژه",
    "فایل", "دانلود", "آپلود", "بفرست", "پیوست", "زیپ", "بساز", "نصب کن", "پکیج",
    "دیپلوی", "ریلوی", "رندر", "پایتون", "جاوااسکریپت", "دیتابیس", "ربات",
    # فارسی — جستجو/اطلاعات به‌روز
    "سرچ کن", "جستجو کن", "بگرد", "اخبار", "قیمت", "امروز", "الان", "لینک", "سایت",
    "باز کن", "صفحه", "وب",
    # فارسی — تولید رسانه
    "عکس بساز", "تصویر بساز", "ویدیو بساز", "طراحی کن",
    # انگلیسی
    "run ", "execute", "debug", "error", "script", "install", "download", "deploy",
    "search for", "generate image", "generate video", "write code", "fix this",
    "create a file", "send me the file", "send the file", ".py", ".js", ".zip",
    ".csv", ".json", "github", "api key",
]

GREETING_ONLY = [
    "سلام", "درود", "خوبی", "چطوری", "چطورید", "hi", "hello", "hey",
    "خداحافظ", "ممنون", "مرسی", "متشکرم", "تشکر", "خسته نباشی", "باشه", "اوکی", "ok",
]


def heuristic_mode(text: str) -> str | None:
    t = (text or "").strip().lower()
    if not t:
        return "chat"
    if any(k in t for k in AGENT_KEYWORDS):
        return "agent"
    if len(t) <= 40 and any(g in t for g in GREETING_ONLY):
        return "chat"
    return None  # مبهم


CLASSIFY_PROMPT = (
    "فقط یک کلمه جواب بده، بدون هیچ توضیح اضافه: اگه پیام زیر برای انجامش واقعاً نیاز به "
    "اجرای کد، جستجوی وب، ساخت فایل/تصویر/ویدیو یا هر اقدام عملی دیگه‌ای داره، بنویس AGENT. "
    "اگه فقط یک گفتگوی عادی/سوال دانشی/نظرخواهیه که با متن ساده جواب داده می‌شه، بنویس CHAT.\n\n"
    "پیام کاربر: {msg}"
)


async def decide_mode(text: str, tools_enabled: dict, classify_fn) -> str:
    """
    classify_fn: یک async callable(prompt: str) -> str که یک تکمیل کوتاه از مدل کاربر می‌گیره.
    """
    if not any(tools_enabled.values()):
        return "chat"

    h = heuristic_mode(text)
    if h:
        return h

    try:
        verdict = await classify_fn(CLASSIFY_PROMPT.format(msg=text[:500]))
        return "chat" if "CHAT" in (verdict or "").upper() else "agent"
    except Exception:
        # اگه تشخیص شکست خورد، برای اینکه قابلیتی از دست نره، سمت ایجنت رو انتخاب کن
        return "agent"
