from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from .. import texts, keyboards, ai_client, crypto
from ..db import db
from ..providers import ALL_PRESETS
from ..states import AddProvider

router = Router()


@router.message(F.text == "🔑 مدیریت API")
async def show_providers(message: Message):
    providers = await db.list_providers(message.from_user.id)
    if not providers:
        await message.answer(
            "هنوز هیچ API ای اضافه نکردی 👇",
            reply_markup=keyboards.provider_manage_kb([]),
        )
        return
    await message.answer("🔑 <b>API های تو:</b>", reply_markup=keyboards.provider_manage_kb(providers))


@router.callback_query(F.data == "addp_start")
async def addp_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddProvider.choosing_kind)
    await callback.message.answer(texts.CHOOSE_KIND, reply_markup=keyboards.kind_choice_kb())
    await callback.answer()


@router.callback_query(F.data == "addp_back_kind")
async def addp_back_kind(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddProvider.choosing_kind)
    await callback.message.edit_text(texts.CHOOSE_KIND, reply_markup=keyboards.kind_choice_kb())
    await callback.answer()


@router.callback_query(AddProvider.choosing_kind, F.data.startswith("addp_kind:"))
async def addp_kind_chosen(callback: CallbackQuery, state: FSMContext):
    kind = callback.data.split(":", 1)[1]
    await state.update_data(kind=kind)
    await state.set_state(AddProvider.choosing_preset)
    await callback.message.edit_text(texts.CHOOSE_PRESET, reply_markup=keyboards.preset_choice_kb(kind))
    await callback.answer()


@router.callback_query(AddProvider.choosing_preset, F.data.startswith("addp_preset:"))
async def addp_preset_chosen(callback: CallbackQuery, state: FSMContext):
    preset_key = callback.data.split(":", 1)[1]
    data = await state.get_data()
    kind = data["kind"]

    if preset_key == "custom":
        await state.update_data(preset_key=None, api_style="openai", name="Custom API")
        await state.set_state(AddProvider.entering_custom_url)
        await callback.message.answer(texts.ENTER_CUSTOM_URL, reply_markup=keyboards.cancel_kb())
        await callback.answer()
        return

    preset = ALL_PRESETS[kind][preset_key]
    await state.update_data(
        preset_key=preset_key, api_style=preset["api_style"],
        base_url=preset["base_url"], name=preset["label"],
    )
    await state.set_state(AddProvider.entering_api_key)
    await callback.message.answer(texts.ENTER_API_KEY, reply_markup=keyboards.cancel_kb())
    await callback.answer()


@router.message(AddProvider.entering_custom_url)
async def addp_custom_url(message: Message, state: FSMContext):
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("❗️ آدرس معتبر نیست. یه چیزی مثل https://api.example.com/v1 بفرست:")
        return
    await state.update_data(base_url=url)
    await state.set_state(AddProvider.entering_api_key)
    await message.answer(texts.ENTER_API_KEY, reply_markup=keyboards.cancel_kb())


@router.message(AddProvider.entering_api_key)
async def addp_api_key(message: Message, state: FSMContext):
    api_key = message.text.strip()
    # سعی می‌کنیم پیام کلید رو حذف کنیم که توی تاریخچه‌ی چت نمونه (امنیت بیشتر)
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    await state.update_data(api_key=api_key)

    status_msg = await message.answer(texts.FETCHING_MODELS)
    try:
        models = await ai_client.fetch_models(data["api_style"], data["base_url"], api_key)
    except ai_client.AIError as e:
        await status_msg.edit_text(f"❌ {e}\n\nدوباره کلید رو بفرست یا /cancel بزن:")
        return

    if models:
        await state.update_data(models=models)
        await state.set_state(AddProvider.choosing_model)
        await status_msg.edit_text(texts.CHOOSE_MODEL, reply_markup=keyboards.models_kb(models))
    else:
        await state.set_state(AddProvider.entering_custom_model)
        await status_msg.edit_text(texts.NO_MODELS_FOUND_ENTER_MANUALLY)


@router.callback_query(AddProvider.choosing_model, F.data.startswith("addp_model:"))
async def addp_model_chosen(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split(":", 1)[1])
    data = await state.get_data()
    model = data["models"][idx]
    await _finalize_provider(callback.from_user.id, data, model, callback.message, state)
    await callback.answer()


@router.message(AddProvider.entering_custom_model)
async def addp_custom_model(message: Message, state: FSMContext):
    model = message.text.strip()
    data = await state.get_data()
    await _finalize_provider(message.from_user.id, data, model, message, state)


async def _finalize_provider(user_id: int, data: dict, model: str, message: Message, state: FSMContext):
    enc_key = crypto.encrypt(data["api_key"])
    await db.add_provider(
        user_id=user_id, kind=data["kind"], name=data["name"],
        api_style=data["api_style"], base_url=data["base_url"],
        api_key_enc=enc_key, model=model,
    )
    await state.clear()
    await message.answer(f"{texts.PROVIDER_SAVED}\n\n📦 مدل: <code>{model}</code>", reply_markup=keyboards.MAIN_MENU)


@router.callback_query(F.data.startswith("prov_del:"))
async def prov_delete(callback: CallbackQuery):
    provider_id = int(callback.data.split(":", 1)[1])
    await db.delete_provider(provider_id)
    providers = await db.list_providers(callback.from_user.id)
    await callback.message.edit_text("🔑 <b>API های تو:</b>", reply_markup=keyboards.provider_manage_kb(providers))
    await callback.answer("حذف شد ✅")


@router.callback_query(F.data.startswith("prov_use:"))
async def prov_use(callback: CallbackQuery):
    provider_id = int(callback.data.split(":", 1)[1])
    provider = await db.get_provider(provider_id)
    if provider["kind"] == "chat":
        await db.update_user(callback.from_user.id, active_provider_id=provider_id)
        await callback.answer(f"✅ چت روی {provider['name']} ({provider['model']}) تنظیم شد")
    else:
        await callback.answer(f"ℹ️ این یک API {provider['kind']} هست و به‌صورت خودکار توسط ایجنت استفاده می‌شه")


@router.callback_query(F.data == "cancel_flow")
async def cancel_flow(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("لغو شد.", reply_markup=keyboards.MAIN_MENU)
    await callback.answer()
