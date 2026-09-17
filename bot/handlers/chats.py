from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from .. import texts, keyboards
from ..db import db

router = Router()


@router.message(F.text == "💬 چت‌ها")
async def show_chats(message: Message):
    user = await db.get_user(message.from_user.id)
    chats = await db.list_chats(message.from_user.id)
    await message.answer(texts.CHATS_HEADER, reply_markup=keyboards.chats_kb(chats, user["active_chat_id"]))


@router.callback_query(F.data == "chat_new")
async def new_chat(callback: CallbackQuery):
    chat_id = await db.create_chat(callback.from_user.id)
    await callback.message.answer(texts.NEW_CHAT_STARTED)
    await callback.answer()
    chats = await db.list_chats(callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=keyboards.chats_kb(chats, chat_id))


@router.callback_query(F.data.startswith("chat_open:"))
async def open_chat(callback: CallbackQuery):
    chat_id = int(callback.data.split(":", 1)[1])
    chat = await db.get_chat(chat_id)
    if not chat or chat["user_id"] != callback.from_user.id:
        await callback.answer("چت پیدا نشد", show_alert=True)
        return
    await db.update_user(callback.from_user.id, active_chat_id=chat_id)
    first_msg = await db.get_first_user_message(chat_id)
    snippet = (first_msg[:80] + "…") if first_msg and len(first_msg) > 80 else (first_msg or "چت خالی")
    await callback.message.answer(f"{texts.CHAT_RESUMED}\n\n📌 <i>شروع چت:</i> {snippet}")
    await callback.answer()


@router.callback_query(F.data.startswith("chat_del:"))
async def delete_chat(callback: CallbackQuery):
    chat_id = int(callback.data.split(":", 1)[1])
    chat = await db.get_chat(chat_id)
    if not chat or chat["user_id"] != callback.from_user.id:
        await callback.answer("چت پیدا نشد", show_alert=True)
        return
    await db.delete_chat(chat_id)
    user = await db.get_user(callback.from_user.id)
    if user["active_chat_id"] == chat_id:
        await db.update_user(callback.from_user.id, active_chat_id=None)
    chats = await db.list_chats(callback.from_user.id)
    await callback.message.edit_text(texts.CHATS_HEADER, reply_markup=keyboards.chats_kb(chats, None))
    await callback.answer("🗑 حذف شد")
