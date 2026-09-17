import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

API_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

main_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🤖 شروع چت جدید"), KeyboardButton(text="⚙️ تنظیمات")],
    [KeyboardButton(text="📊 وضعیت ربات"), KeyboardButton(text="🔌 تغییر مدل")]
], resize_keyboard=True)

def get_model_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="GPT-4o", callback_data="model_gpt4o")],
        [InlineKeyboardButton(text="Claude 3.5", callback_data="model_claude")],
        [InlineKeyboardButton(text="Gemini 1.5", callback_data="model_gemini")]
    ])

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("سلام! من دستیار هوشمند شما هستم. از دکمه‌های زیر استفاده کنید:", reply_markup=main_kb)

@dp.message(F.text == "🔌 تغییر مدل")
async def choose_model(message: types.Message):
    await message.answer("لطفاً مدل مورد نظر را انتخاب کنید:", reply_markup=get_model_kb())

@dp.callback_query(F.data.startswith("model_"))
async def model_selected(callback: types.CallbackQuery):
    model = callback.data.split("_")[1]
    await callback.message.answer(f"✅ مدل با موفقیت روی {model} تنظیم شد.")
    await callback.answer()

@dp.message(F.text == "⚙️ تنظیمات")
async def settings(message: types.Message):
    await message.answer("🔧 **پنل تنظیمات:**\n\n- وضعیت کلید API: فعال\n- پرووایدر فعلی: پیش‌فرض", parse_mode="Markdown")

@dp.message(F.text == "📊 وضعیت ربات")
async def show_status(message: types.Message):
    await message.answer("🟢 سیستم فعال و آماده پاسخگویی.", reply_markup=main_kb)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
