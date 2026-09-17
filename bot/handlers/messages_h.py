import datetime

from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile

from .. import texts, keyboards, ai_client, agent, crypto, config, mode
from ..db import db

router = Router()

MENU_TEXTS = {
    "💬 چت‌ها", "🔑 مدیریت API", "🛠 ابزارها", "⚙️ تنظیمات", "📊 مصرف توکن", "ℹ️ راهنما",
    "🧬 انتخاب ایجنت",
}


async def _reset_usage_if_needed(user_id: int, user):
    today = datetime.date.today().isoformat()
    month = today[:7]
    updates = {}
    if user["last_reset_day"] != today:
        updates["tokens_used_today"] = 0
        updates["last_reset_day"] = today
    if user["last_reset_month"] != month:
        updates["tokens_used_month"] = 0
        updates["last_reset_month"] = month
    if updates:
        await db.update_user(user_id, **updates)
        user = await db.get_user(user_id)
    return user


async def _send_media(message: Message, ctx_media):
    for kind, payload in ctx_media:
        try:
            if kind == "image":
                await message.answer_photo(BufferedInputFile(payload, filename="image.png"))
            elif kind == "video":
                await message.answer(f"🎬 ویدیوی آماده:\n{payload}")
            elif kind == "file":
                filename, data = payload
                await message.answer_document(BufferedInputFile(data, filename=filename))
        except Exception as e:
            await message.answer(f"⚠️ نتونستم این پیوست رو بفرستم ({kind}): {e}")


@router.message(F.text & ~F.text.in_(MENU_TEXTS) & ~F.text.startswith("/"))
async def handle_chat_message(message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    user = await _reset_usage_if_needed(user_id, user)

    if user["tokens_used_today"] >= user["daily_token_limit"]:
        await message.answer(texts.LIMIT_REACHED.format(period="روزانه"))
        return
    if user["tokens_used_month"] >= user["monthly_token_limit"]:
        await message.answer(texts.LIMIT_REACHED.format(period="ماهانه"))
        return

    if not user["active_provider_id"]:
        providers = await db.list_providers(user_id, kind="chat")
        if not providers:
            await message.answer(texts.NO_PROVIDER_YET)
            return
        await db.update_user(user_id, active_provider_id=providers[0]["provider_id"])
        user = await db.get_user(user_id)

    provider = await db.get_provider(user["active_provider_id"])
    if not provider:
        await message.answer(texts.NO_PROVIDER_YET)
        return

    if not user["active_chat_id"]:
        chat_id = await db.create_chat(user_id)
    else:
        chat_id = user["active_chat_id"]

    await db.add_message(chat_id, "user", message.text)
    await db.set_chat_title_if_default(chat_id, message.text)

    api_key = crypto.decrypt(provider["api_key_enc"])
    agent_key = await db.get_agent_profile(user_id)

    tools_enabled_raw = await db.get_tools_enabled(user_id)
    tools_enabled = agent.effective_tools_enabled(tools_enabled_raw, agent_key)

    history = await db.get_messages(chat_id)

    async def classify_fn(prompt: str) -> str:
        r = await ai_client.chat_completion(
            provider["api_style"], provider["base_url"], api_key, provider["model"],
            [{"role": "user", "content": prompt}], temperature=0,
        )
        return r["text"]

    msg_mode = await mode.decide_mode(message.text, tools_enabled, classify_fn)

    total_input_tokens = 0
    total_output_tokens = 0
    final_text = ""
    media = []

    if msg_mode == "chat":
        # ---- حالت چت عادی: یک تماس ساده و سبک، بدون فرمت ابزار و بدون حلقه ----
        api_messages = [{"role": "system", "content": agent.build_chat_mode_prompt(agent_key)}]
        for m in history:
            role = m["role"] if m["role"] in ("user", "assistant") else "user"
            api_messages.append({"role": role, "content": m["content"]})

        try:
            result = await ai_client.chat_completion(
                provider["api_style"], provider["base_url"], api_key, provider["model"],
                api_messages, temperature=user["temperature"],
            )
        except ai_client.AIError as e:
            await message.answer(f"❌ خطا: {e}")
            return

        total_input_tokens += result["input_tokens"]
        total_output_tokens += result["output_tokens"]
        reply_text = result["text"]

        # شبکه‌ی ایمنی: اگه با وجود دستور صریح، مدل بازم یک بلاک ابزار فرستاد، به‌جای نادیده
        # گرفتنش، همون‌جا سوییچ می‌کنیم به حالت کامل ایجنت و ادامه می‌دیم.
        call = agent.extract_tool_call(reply_text)
        if call is None:
            final_text = reply_text
        else:
            msg_mode = "agent"

    if msg_mode == "agent":
        # ---- حالت ایجنت: حلقه‌ی کامل با ابزارها ----
        status_msg = await message.answer(texts.THINKING)

        async def on_status(text: str):
            try:
                await status_msg.edit_text(text)
            except Exception:
                pass

        system_prompt = agent.build_system_prompt(
            [k for k, v in tools_enabled.items() if v], agent_key,
        )
        api_messages = [{"role": "system", "content": system_prompt}]
        for m in history:
            role = m["role"] if m["role"] in ("user", "assistant") else "user"
            api_messages.append({"role": role, "content": m["content"]})

        ctx = agent.ToolContext(on_status=on_status)

        image_providers = await db.list_providers(user_id, kind="image")
        video_providers = await db.list_providers(user_id, kind="video")
        image_provider = image_providers[0] if image_providers and tools_enabled.get("image_gen") else None
        video_provider = video_providers[0] if video_providers and tools_enabled.get("video_gen") else None

        max_iter = agent.max_iterations_for(agent_key)

        try:
            for _ in range(max_iter):
                result = await ai_client.chat_completion(
                    provider["api_style"], provider["base_url"], api_key, provider["model"],
                    api_messages, temperature=user["temperature"],
                )
                total_input_tokens += result["input_tokens"]
                total_output_tokens += result["output_tokens"]
                reply_text = result["text"]

                call = agent.extract_tool_call(reply_text)
                if not call:
                    final_text = reply_text
                    break

                api_messages.append({"role": "assistant", "content": reply_text})

                tool_result = await agent.execute_tool(
                    user_id, call, ctx, image_provider=image_provider, video_provider=video_provider,
                )
                api_messages.append({"role": "user", "content": f"[نتیجه ابزار]\n{tool_result[:3000]}"})
            else:
                final_text = "⚠️ ایجنت خیلی زیاد ابزار صدا زد و به سقف تکرار رسید. لطفا سوالتو دقیق‌تر بپرس."

        except ai_client.AIError as e:
            await status_msg.edit_text(f"❌ خطا: {e}")
            return

        media = ctx.media
        try:
            await status_msg.delete()
        except Exception:
            pass

    await db.add_message(chat_id, "assistant", final_text or "(بدون پاسخ متنی)")

    new_today = user["tokens_used_today"] + total_input_tokens + total_output_tokens
    new_month = user["tokens_used_month"] + total_input_tokens + total_output_tokens
    await db.update_user(user_id, tokens_used_today=new_today, tokens_used_month=new_month)

    if final_text.strip():
        await message.answer(final_text, reply_markup=keyboards.MAIN_MENU)

    await _send_media(message, media)

    if total_input_tokens or total_output_tokens:
        await message.answer(
            f"🔹 توکن مصرفی این پیام: {total_input_tokens + total_output_tokens:,} "
            f"(ورودی {total_input_tokens:,} / خروجی {total_output_tokens:,})"
        )
