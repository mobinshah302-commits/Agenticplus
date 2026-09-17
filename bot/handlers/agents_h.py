from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from .. import texts, keyboards, agent_profiles
from ..db import db

router = Router()


@router.message(F.text == "🧬 انتخاب ایجنت")
async def show_agents(message: Message):
    current = await db.get_agent_profile(message.from_user.id)
    await message.answer(texts.AGENTS_HEADER, reply_markup=keyboards.agent_list_kb(0, current))


@router.callback_query(F.data.startswith("agent_page:"))
async def paginate_agents(callback: CallbackQuery):
    page = int(callback.data.split(":", 1)[1])
    current = await db.get_agent_profile(callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=keyboards.agent_list_kb(page, current))
    await callback.answer()


@router.callback_query(F.data.startswith("agent_use:"))
async def use_agent(callback: CallbackQuery):
    key = callback.data.split(":", 1)[1]
    await db.set_agent_profile(callback.from_user.id, key)
    info = agent_profiles.get_agent(key)
    await callback.message.edit_reply_markup(reply_markup=keyboards.agent_list_kb(0, key))
    await callback.answer(f"✅ ایجنت روی «{info['label']}» تنظیم شد")
    if info.get("note"):
        await callback.message.answer(f"ℹ️ {info['label']}\n{info['note']}")
