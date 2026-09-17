from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
from .providers import ALL_PRESETS
from . import agent_profiles

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💬 چت‌ها"), KeyboardButton(text="🔑 مدیریت API")],
        [KeyboardButton(text="🛠 ابزارها"), KeyboardButton(text="🧬 انتخاب ایجنت")],
        [KeyboardButton(text="⚙️ تنظیمات"), KeyboardButton(text="📊 مصرف توکن")],
        [KeyboardButton(text="ℹ️ راهنما")],
    ],
    resize_keyboard=True,
)

KIND_LABELS = {"chat": "💬 چت (متن)", "image": "🎨 تصویرساز", "video": "🎬 ویدیوساز"}


def kind_choice_kb() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=v, callback_data=f"addp_kind:{k}")] for k, v in KIND_LABELS.items()]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def preset_choice_kb(kind: str) -> InlineKeyboardMarkup:
    presets = ALL_PRESETS[kind]
    rows = [[InlineKeyboardButton(text=p["label"], callback_data=f"addp_preset:{key}")]
            for key, p in presets.items()]
    rows.append([InlineKeyboardButton(text="🛠 آدرس کاستوم (Custom API)", callback_data="addp_preset:custom")])
    rows.append([InlineKeyboardButton(text="⬅️ بازگشت", callback_data="addp_back_kind")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def models_kb(models: list[str], prefix: str = "addp_model") -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=m, callback_data=f"{prefix}:{i}")] for i, m in enumerate(models[:40])]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def provider_manage_kb(providers) -> InlineKeyboardMarkup:
    rows = []
    for p in providers:
        label = f"{p['kind']} | {p['name']} | {p['model'] or '—'}"
        rows.append([
            InlineKeyboardButton(text=label, callback_data=f"prov_use:{p['provider_id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"prov_del:{p['provider_id']}"),
        ])
    rows.append([InlineKeyboardButton(text="➕ افزودن API جدید", callback_data="addp_start")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def chats_kb(chats, active_chat_id: int | None) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="➕ چت جدید", callback_data="chat_new")]]
    for c in chats:
        mark = "🟢 " if c["chat_id"] == active_chat_id else "🗂 "
        title = c["title"] or "چت جدید"
        rows.append([
            InlineKeyboardButton(text=f"{mark}{title}", callback_data=f"chat_open:{c['chat_id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"chat_del:{c['chat_id']}"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def tools_kb(tools: dict) -> InlineKeyboardMarkup:
    labels = {
        "web_search": "🔎 وب‌سرچ",
        "code_exec": "🖥 اجرای کد",
        "image_gen": "🎨 ساخت تصویر",
        "video_gen": "🎬 ساخت ویدیو",
        "browser": "🌐 مرورگر",
        "list_files": "📁 لیست فایل‌ها",
        "send_file": "📤 ارسال فایل",
    }
    rows = []
    for key, label in labels.items():
        state = "✅" if tools.get(key, True) else "❌"
        rows.append([InlineKeyboardButton(text=f"{state} {label}", callback_data=f"tool_toggle:{key}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def settings_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🌡 دمای پاسخ (Temperature)", callback_data="set_temp")],
        [InlineKeyboardButton(text="⏱ تایم‌اوت اجرای کد", callback_data="set_timeout")],
        [InlineKeyboardButton(text="📅 سقف توکن روزانه", callback_data="set_daily")],
        [InlineKeyboardButton(text="🗓 سقف توکن ماهانه", callback_data="set_monthly")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def agent_list_kb(page: int, current_key: str) -> InlineKeyboardMarkup:
    items, total_pages = agent_profiles.catalog_page(page)
    rows = []
    if page == 0:
        default_mark = "🟢 " if current_key in ("default", "", None) else ""
        rows.append([InlineKeyboardButton(text=f"{default_mark}🧠 پیش‌فرض (متعادل)", callback_data="agent_use:default")])
    for key, label, template, note in items:
        mark = "🟢 " if key == current_key else ""
        badge = agent_profiles.token_badge(key)
        rows.append([InlineKeyboardButton(text=f"{mark}{label} · {badge}", callback_data=f"agent_use:{key}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ قبلی", callback_data=f"agent_page:{page-1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="بعدی ➡️", callback_data=f"agent_page:{page+1}"))
    if nav:
        rows.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ لغو", callback_data="cancel_flow")]])
