from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from .. import texts, keyboards
from ..db import db

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await db.ensure_user(message.from_user.id)
    await message.answer(texts.WELCOME, reply_markup=keyboards.MAIN_MENU)


@router.message(F.text == "ℹ️ راهنما")
async def help_msg(message: Message):
    await message.answer(
        "📖 <b>راهنمای سریع</b>\n\n"
        "1️⃣ از 🔑 مدیریت API یک کلید چت اضافه کن (یا از پرووایدرهای معروف، یا کاستوم)\n"
        "2️⃣ از 💬 چت‌ها یه چت جدید بزن و شروع کن به تایپ کردن\n"
        "3️⃣ ایجنت خودش تشخیص می‌ده کِی نیاز به وب‌سرچ، اجرای کد، یا ساخت عکس/ویدیو داره\n"
        "4️⃣ از 🛠 ابزارها می‌تونی هرکدوم از قابلیت‌ها رو خاموش/روشن کنی\n"
        "5️⃣ از ⚙️ تنظیمات و 📊 مصرف توکن مدیریت هزینه و رفتار مدل رو کنترل کن\n\n"
        "کد و پکیج‌هایی که نصب می‌کنی توی محیط شخصی خودتن و بین سشن‌ها می‌مونن.",
    )
