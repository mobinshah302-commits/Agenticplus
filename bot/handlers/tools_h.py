from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from .. import texts, keyboards
from ..db import db

router = Router()


@router.message(F.text == "🛠 ابزارها")
async def show_tools(message: Message):
    tools = await db.get_tools_enabled(message.from_user.id)
    await message.answer(texts.TOOLS_HEADER, reply_markup=keyboards.tools_kb(tools))


@router.callback_query(F.data.startswith("tool_toggle:"))
async def toggle_tool(callback: CallbackQuery):
    tool = callback.data.split(":", 1)[1]
    tools = await db.get_tools_enabled(callback.from_user.id)
    new_val = not tools.get(tool, True)
    await db.set_tool_enabled(callback.from_user.id, tool, new_val)
    tools[tool] = new_val
    await callback.message.edit_reply_markup(reply_markup=keyboards.tools_kb(tools))
    await callback.answer("✅ فعال شد" if new_val else "❌ غیرفعال شد")
