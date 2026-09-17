from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from .. import texts, keyboards
from ..db import db
from ..states import Settings

router = Router()


@router.message(F.text == "⚙️ تنظیمات")
async def show_settings(message: Message):
    user = await db.get_user(message.from_user.id)
    text = (
        f"{texts.SETTINGS_HEADER}\n\n"
        f"🌡 دما (Temperature): <b>{user['temperature']}</b>\n"
        f"⏱ تایم‌اوت اجرای کد: <b>{user['code_timeout']}s</b>\n"
        f"📅 سقف توکن روزانه: <b>{user['daily_token_limit']:,}</b>\n"
        f"🗓 سقف توکن ماهانه: <b>{user['monthly_token_limit']:,}</b>"
    )
    await message.answer(text, reply_markup=keyboards.settings_kb())


@router.message(F.text == "📊 مصرف توکن")
async def show_usage(message: Message):
    user = await db.get_user(message.from_user.id)
    text = (
        f"{texts.USAGE_HEADER}\n\n"
        f"امروز: <b>{user['tokens_used_today']:,}</b> / {user['daily_token_limit']:,}\n"
        f"این ماه: <b>{user['tokens_used_month']:,}</b> / {user['monthly_token_limit']:,}\n\n"
        "برای تغییر سقف‌ها به ⚙️ تنظیمات برو."
    )
    await message.answer(text)


@router.callback_query(F.data == "set_temp")
async def ask_temp(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Settings.entering_temperature)
    await callback.message.answer("🌡 یه عدد بین 0 تا 1.5 بفرست (مثلا 0.7):")
    await callback.answer()


@router.message(Settings.entering_temperature)
async def set_temp(message: Message, state: FSMContext):
    try:
        val = float(message.text.strip())
        assert 0 <= val <= 1.5
    except (ValueError, AssertionError):
        await message.answer("❗️ عدد معتبر بین 0 تا 1.5 بفرست:")
        return
    await db.update_user(message.from_user.id, temperature=val)
    await state.clear()
    await message.answer(f"✅ دما روی {val} تنظیم شد.", reply_markup=keyboards.MAIN_MENU)


@router.callback_query(F.data == "set_timeout")
async def ask_timeout(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Settings.entering_code_timeout)
    await callback.message.answer("⏱ حداکثر زمان اجرای کد رو به ثانیه بفرست (مثلا 300):")
    await callback.answer()


@router.message(Settings.entering_code_timeout)
async def set_timeout(message: Message, state: FSMContext):
    try:
        val = int(message.text.strip())
        assert val > 0
    except (ValueError, AssertionError):
        await message.answer("❗️ یه عدد صحیح مثبت بفرست:")
        return
    await db.update_user(message.from_user.id, code_timeout=val)
    await state.clear()
    await message.answer(f"✅ تایم‌اوت روی {val} ثانیه تنظیم شد.", reply_markup=keyboards.MAIN_MENU)


@router.callback_query(F.data == "set_daily")
async def ask_daily(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Settings.entering_daily_limit)
    await callback.message.answer("📅 سقف توکن روزانه رو بفرست (مثلا 200000):")
    await callback.answer()


@router.message(Settings.entering_daily_limit)
async def set_daily(message: Message, state: FSMContext):
    try:
        val = int(message.text.strip().replace(",", ""))
        assert val > 0
    except (ValueError, AssertionError):
        await message.answer("❗️ یه عدد صحیح مثبت بفرست:")
        return
    await db.update_user(message.from_user.id, daily_token_limit=val)
    await state.clear()
    await message.answer(f"✅ سقف روزانه روی {val:,} تنظیم شد.", reply_markup=keyboards.MAIN_MENU)


@router.callback_query(F.data == "set_monthly")
async def ask_monthly(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Settings.entering_monthly_limit)
    await callback.message.answer("🗓 سقف توکن ماهانه رو بفرست (مثلا 3000000):")
    await callback.answer()


@router.message(Settings.entering_monthly_limit)
async def set_monthly(message: Message, state: FSMContext):
    try:
        val = int(message.text.strip().replace(",", ""))
        assert val > 0
    except (ValueError, AssertionError):
        await message.answer("❗️ یه عدد صحیح مثبت بفرست:")
        return
    await db.update_user(message.from_user.id, monthly_token_limit=val)
    await state.clear()
    await message.answer(f"✅ سقف ماهانه روی {val:,} تنظیم شد.", reply_markup=keyboards.MAIN_MENU)
