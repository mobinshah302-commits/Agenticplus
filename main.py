import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

# Configuration
API_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Main Keyboard
main_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🤖 شروع چت جدید"), KeyboardButton(text="⚙️ تنظیمات")],
    [KeyboardButton(text="📊 وضعیت ربات"), KeyboardButton(text="🔌 تغییر مدل")]
], resize_keyboard=True)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("سلام! من دستیار هوشمند شما هستم. از دکمه‌های زیر استفاده کنید:", reply_markup=main_kb)

@dp.message(F.text == "📊 وضعیت ربات")
async def show_status(message: types.Message):
    status_text = (
        "📊 **وضعیت سیستم:**\n\n"
        "🟢 وضعیت: فعال (Active)\n"
        "⚡ سرعت پردازش: بهینه\n"
        "📦 حالت: آماده برای اجرای دستورات\n"
        "⏳ در حال انتظار برای ورودی کاربر..."
    )
    await message.answer(status_text, parse_mode="Markdown")

@dp.message(F.text == "🤖 شروع چت جدید")
async def new_chat(message: types.Message):
    await message.answer("چت جدید آغاز شد. هر چه می‌خواهید بپرسید...")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
