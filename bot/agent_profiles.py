# -*- coding: utf-8 -*-
"""
پروفایل‌های ایجنت (Agent Personas)
====================================
نکته‌ی مهم و صادقانه: اکثر ابزارهایی که در این لیست هستن (Cursor, Devin, Windsurf,
Firebase Studio, Google Antigravity, Zed, Kiro, Trae, Junie, GitHub Copilot Agent, ...)
محصولات مستقلی هستن که یک API عمومی برای فراخوانی از بیرون (مثل یک ربات تلگرام) ندارن —
یعنی نمی‌شه واقعاً "به بک‌اند اونا وصل شد". چیزی که اینجا پیاده شده اینه: هر پروفایل یک
سبک رفتاری (system prompt متفاوت + ابزارهای پیش‌فرض روشن/خاموش + میزان پرحرفی + سقف
تکرار حلقه‌ی ایجنت) می‌سازه که شبیه‌سازیِ سبکِ شناخته‌شده‌ی همون ابزار روی مدل و API
خود کاربره. یعنی همون کلید API که کاربر وصل کرده (OpenAI/Anthropic/Gemini/...)، زیر هر
پروفایلی که انتخاب کنه کار می‌کنه — فقط رفتار عوض می‌شه، نه ارائه‌دهنده‌ی مدل.

برای اونایی که واقعاً API عمومی و جایگزین دارن (مثل Qwen از طریق DashScope)، به‌جای
پروفایل رفتاری، یک preset واقعی توی providers.py اضافه شده تا کاربر واقعاً بتونه باهاش
سینک کنه (نه فقط شبیه‌سازی رفتار).
"""

# ---------------------------------------------------------------------------
# قالب‌های رفتاری (Templates) — هسته‌ی تفاوت بین پروفایل‌ها
# ---------------------------------------------------------------------------
TEMPLATES = {
    "balanced": {
        "style": "متعادل باش: نه خیلی مختصر نه خیلی طولانی. قبل از هر ابزار لازم نیست توضیح بدی، ولی جواب نهایی رو کامل و طبیعی بده.",
        "tools": {},
        "verbosity": "normal",
        "max_iterations": 6,
        "confirm_before_exec": False,
    },
    "memory_personal": {
        "style": "دستیار شخصی و صمیمی باش. به کل تاریخچه‌ی این گفتگو دقت کن و ترجیح‌ها/قرارهای قبلی کاربر رو در جواب‌هات لحاظ کن، انگار قبلاً همو می‌شناسید.",
        "tools": {},
        "verbosity": "normal",
        "max_iterations": 6,
        "confirm_before_exec": False,
    },
    "careful_confirm": {
        "style": "قبل از هر تغییر واقعی (اجرای کد، نصب پکیج، تغییر فایل) دقیقاً بگو چیکار می‌خوای بکنی و چرا، بعد انجامش بده. توضیح تغییرات کد رو خط‌به‌خط و واضح بده، مثل یک code review دقیق.",
        "tools": {},
        "verbosity": "detailed",
        "max_iterations": 5,
        "confirm_before_exec": True,
    },
    "diff_minimal": {
        "style": "روی نوشتن/ویرایش کد تمرکز کن. کمترین توضیح اضافه رو بده، مستقیم برو سراغ راه‌حل، کد رو تمیز و آماده‌ی اجرا بنویس. از پرچانگی پرهیز کن.",
        "tools": {},
        "verbosity": "brief",
        "max_iterations": 5,
        "confirm_before_exec": False,
    },
    "terminal_ops": {
        "style": "مثل یک ابزار ترمینال‌محور رفتار کن: دستورات شل و اجرای کد رو ترجیح بده، خروجی رو خلاصه و تمیز نشون بده، کمتر درباره‌ی جزئیات پیاده‌سازی حرف بزن.",
        "tools": {"web_search": False, "browser": False, "image_gen": False, "video_gen": False},
        "verbosity": "brief",
        "max_iterations": 6,
        "confirm_before_exec": False,
    },
    "multi_role": {
        "style": (
            "قبل از اجرا، داخل ذهنت (بدون اینکه لازم باشه به کاربر نشون بدی مگه بخواد) بین چند "
            "«حالت» جابه‌جا شو: 🏗 حالت معماری (طراحی کلی) → 💻 حالت کدنویسی (پیاده‌سازی) → 🐞 حالت "
            "دیباگ (تست/رفع خطا). اگه کار پیچیده‌ست، این مراحل رو به‌صورت کوتاه به کاربر هم نشون بده تا "
            "بدونه الان کدوم مرحله‌ای."
        ),
        "tools": {},
        "verbosity": "normal",
        "max_iterations": 7,
        "confirm_before_exec": False,
    },
    "autonomous_fast": {
        "style": "خودکار و مستقل عمل کن. کمتر سوال بپرس، بیشتر کار رو خودت تا انتها پیش ببر و در پایان یه خلاصه از کاری که کردی بده. فقط وقتی چیزی واقعاً مبهمه سوال بپرس.",
        "tools": {},
        "verbosity": "normal",
        "max_iterations": 8,
        "confirm_before_exec": False,
    },
    "ultra_lean": {
        "style": "حداقلی باش: هیچ مقدمه، هیچ توضیح اضافه، هیچ ادب‌واری. فقط اکشن بزن و در پایان یک جمله‌ی نتیجه بده. توکن رو به حداقل برسون.",
        "tools": {"web_search": False, "image_gen": False, "video_gen": False, "browser": False},
        "verbosity": "brief",
        "max_iterations": 4,
        "confirm_before_exec": False,
    },
    "planner_first": {
        "style": "قبل از هر اقدام واقعی، اول یک پلن مرحله‌به‌مرحله (لیست شماره‌دار) از کارهایی که قراره بکنی بنویس، بعد شروع کن به اجرای پلن، مرحله به مرحله. اگه پلن نیاز به تایید داشت بپرس.",
        "tools": {},
        "verbosity": "detailed",
        "max_iterations": 8,
        "confirm_before_exec": True,
    },
    "cost_aware": {
        "style": "همیشه نسبت به مصرف منابع (توکن/زمان) شفاف باش؛ اگه یه کار می‌تونه ساده‌تر و ارزون‌تر انجام بشه بگو، و در پایان جواب اشاره کن این کار چقدر «سبک» یا «سنگین» بود.",
        "tools": {},
        "verbosity": "brief",
        "max_iterations": 6,
        "confirm_before_exec": False,
    },
    "app_builder": {
        "style": "روی ساختن یک اپلیکیشن کامل و قابل‌اجرا تمرکز کن (فرانت + بک‌اند + دیپلوی در صورت نیاز)، ساختار پروژه رو منظم بچین و در پایان بگو چطور اجراش کنه یا دیپلویش کنه.",
        "tools": {},
        "verbosity": "detailed",
        "max_iterations": 8,
        "confirm_before_exec": False,
    },
    "test_driven": {
        "style": "بعد از هر تغییر کد، حتماً یک تست (یا حداقل یک اجرای نمونه) برای اطمینان از درست کار کردنش بزن و نتیجه‌ی تست رو گزارش بده. تاکید زیاد روی «آیا واقعاً کار می‌کنه؟».",
        "tools": {},
        "verbosity": "normal",
        "max_iterations": 7,
        "confirm_before_exec": False,
    },
    "beginner_friendly": {
        "style": "لحنت خیلی دوستانه، صبور و آموزشی باشه، انگار داری به یه مبتدی یاد می‌دی. اصطلاحات فنی رو با یه جمله‌ی ساده هم توضیح بده، ولی زیادی طولانی نشو.",
        "tools": {},
        "verbosity": "normal",
        "max_iterations": 5,
        "confirm_before_exec": False,
    },
    "code_review": {
        "style": "علاوه بر انجام کار، نظر انتقادیِ کوتاه هم بده: نقاط ضعف احتمالی، ریسک امنیتی/کارایی، و یه پیشنهاد بهتر اگه هست. مثل یک ریویوئر باتجربه.",
        "tools": {},
        "verbosity": "normal",
        "max_iterations": 5,
        "confirm_before_exec": False,
    },
    "pr_focused": {
        "style": "خروجی نهایی رو به سبک یک Pull Request بده: یه عنوان کوتاه، توضیح تغییرات به شکل چند بولت (مثل commit message)، و در صورت نیاز کد نهایی.",
        "tools": {},
        "verbosity": "normal",
        "max_iterations": 5,
        "confirm_before_exec": False,
    },
    "spec_driven": {
        "style": "قبل از نوشتن کد، اول یک «مشخصات» کوتاه (Spec) بنویس: هدف، ورودی/خروجی، معیار پذیرش (Acceptance Criteria). بعد طبق همون Spec پیش برو و در پایان بگو کدوم معیارها برآورده شدن.",
        "tools": {},
        "verbosity": "detailed",
        "max_iterations": 7,
        "confirm_before_exec": True,
    },
    "browser_focus": {
        "style": "برای هر کاری که نیاز به اطلاعات بیرونی داره، اول از وب‌سرچ/مرورگر استفاده کن به‌جای حدس زدن. روی گشتن، خوندن صفحات و جمع‌بندی دقیق نتایج تمرکز کن.",
        "tools": {"code_exec": False, "install_package": False},
        "verbosity": "normal",
        "max_iterations": 8,
        "confirm_before_exec": False,
    },
    "security_focus": {
        "style": "همیشه به جنبه‌ی امنیت و best-practice توجه کن: کلیدهای حساس رو هاردکد نکن، ریسک‌های احتمالی کد رو صریح بگو، پیشنهاد رعایت اصول امنیتی بده.",
        "tools": {},
        "verbosity": "normal",
        "max_iterations": 6,
        "confirm_before_exec": True,
    },
    "multi_agent_sim": {
        "style": (
            "این کار رو با ذهنیت چند-عامله جلو ببر: اول به‌عنوان «برنامه‌ریز» وظیفه رو به زیروظیفه‌ها "
            "بشکن، بعد به‌عنوان «مجری» هرکدوم رو با ابزارها انجام بده، در آخر به‌عنوان «ناظر/بازبین» یک "
            "بار نتیجه‌ی نهایی رو نقد کن و اگه ایرادی بود اصلاحش کن، همه‌ی این‌ها رو خودت تنها انجام بده."
        ),
        "tools": {},
        "verbosity": "detailed",
        "max_iterations": 9,
        "confirm_before_exec": False,
    },
}

VERBOSITY_LABEL = {"brief": "🔋 کم", "normal": "🔋 متوسط", "detailed": "🔋 زیاد"}

# ---------------------------------------------------------------------------
# فهرست کامل ایجنت‌ها — هرکدوم به یکی از قالب‌های بالا وصله
# note: توضیح صادقانه برای هرکدوم — یا "پروفایل رفتاری" یا "provider واقعی"
# ---------------------------------------------------------------------------
AGENT_CATALOG = [
    ("hermes", "🌀 Hermes Agent", "memory_personal", "رفتار حافظه‌محور و شخصی؛ هنوز خودِ Hermes نیست، شبیه‌سازیه."),
    ("claude_code", "🟣 Claude Code", "careful_confirm", "سبک محتاط و توضیح‌گو — با provider خودِ Anthropic بهترین تطابق رو داره."),
    ("codex_cli", "🟢 OpenAI Codex CLI", "diff_minimal", "کدنویسی سریع و مستقیم — با provider OpenAI بهترین تطابق."),
    ("opencode", "🧭 OpenCode", "terminal_ops", "ترمینال‌محور و ابزارگرا."),
    ("cline", "🔵 Cline", "careful_confirm", "قبل از تغییر فایل، توضیح و اجازه می‌گیره."),
    ("roo_code", "🌲 Roo Code", "multi_role", "حالت‌های Architect/Code/Debug — ویژگی واقعی خودش. (⚠️ توسعه‌ی رسمی‌اش طبق اعلام خودشون متوقف/Archive شده)"),
    ("kilo_code", "🦣 Kilo Code", "multi_role", "شکستن کار به زیروظیفه و orchestration — شبیه ویژگی واقعی‌اش."),
    ("openhands", "🙌 OpenHands", "autonomous_fast", "خودکار و کم‌سوال."),
    ("goose", "🦢 Goose", "autonomous_fast", "خودکار، مستقیم می‌ره سراغ تکمیل کار."),
    ("aider", "✏️ Aider", "diff_minimal", "تمرکز روی ادیت مستقیم فایل کد، کم‌حرف."),
    ("continue_dev", "➡️ Continue", "diff_minimal", "دستیار مختصر داخل‌ادیتوری."),
    ("gemini_cli", "🔷 Gemini CLI", "balanced", "provider واقعی‌اش Gemini از گوگله."),
    ("qwen_code", "🟠 Qwen Code", "balanced", "provider واقعی‌اش Qwen از طریق Alibaba DashScope اضافه شد."),
    ("amazon_q", "📦 Amazon Q Developer", "security_focus", "تمرکز روی امنیت/best-practice به سبک AWS."),
    ("warp_agent", "⚡ Warp Agent", "terminal_ops", "ترمینال‌محور."),
    ("swe_agent", "🩹 SWE-agent", "diff_minimal", "حلقه‌ی کوتاه برای حل یک مسئله‌ی مشخص."),
    ("mini_swe_agent", "🔬 mini-SWE-agent", "ultra_lean", "فوق‌سبک، کمترین توکن."),
    ("plandex", "📐 Plandex", "planner_first", "پلن چندمرحله‌ای قبل از اجرا — ویژگی واقعی‌اش."),
    ("pi_agent", "🥧 Pi Coding Agent", "balanced", "اطلاعات عمومی کمی در دسترسه؛ رفتار عمومی و متعادل."),
    ("crush", "🍄 Crush", "terminal_ops", "رابط ترمینالی سبک (Charm)."),
    ("codewhale", "🐋 CodeWhale", "balanced", "اطلاعات عمومی محدود؛ رفتار عمومی."),
    ("reasonix", "🧩 Reasonix", "balanced", "اطلاعات عمومی محدود؛ رفتار عمومی."),
    ("grok_cli", "✖️ Grok CLI", "balanced", "provider واقعی‌اش xAI (Grok)."),
    ("deepseek_agent", "🐳 DeepSeek", "balanced", "provider واقعی‌اش DeepSeek."),
    ("amp", "📡 Amp", "cost_aware", "شفافیت در مصرف/هزینه — ویژگی واقعی‌اش."),
    ("pythagora", "🏛 Pythagora", "app_builder", "ساخت اپ کامل از صفر (میراث GPT-Pilot)."),
    ("devin", "🤖 Devin", "autonomous_fast", "برنامه‌ریزی بلندمدت و گزارش پیشرفت."),
    ("cursor", "▶️ Cursor", "diff_minimal", "ادیت سریع و مستقیم کد."),
    ("windsurf", "🏄 Windsurf", "planner_first", "جریان چندمرحله‌ای (Cascade) با چک‌پوینت."),
    ("junie", "☕ Junie", "test_driven", "اجرای تست بعد از تغییر — سبک JetBrains."),
    ("trae", "🐢 Trae", "beginner_friendly", "دوستانه و مناسب مبتدی."),
    ("refact", "🔎 Refact.ai", "code_review", "تمرکز روی ریویو و کیفیت کد."),
    ("sweep", "🧹 Sweep", "pr_focused", "از issue تا PR."),
    ("t3_code", "🎮 T3 Code", "balanced", "اطلاعات عمومی محدود؛ رفتار عمومی."),
    ("kiro", "📋 Kiro", "spec_driven", "توسعه‌ی Spec-first — ویژگی واقعی‌اش (AWS)."),
    ("zed_agent", "🌊 Zed Agent", "diff_minimal", "ادیت مستقیم و سریع."),
    ("gh_copilot_agent", "🐙 GitHub Copilot Coding Agent", "pr_focused", "خروجی به سبک PR/commit."),
    ("firebase_studio", "🔥 Firebase Studio", "app_builder", "ساخت و اجرای اپ کامل."),
    ("google_antigravity", "🪐 Google Antigravity", "app_builder", "ساخت اپ کامل، سبک گوگل."),
    ("open_interpreter", "🖥 Open Interpreter", "terminal_ops", "اجرای آزاد دستورات روی سیستم."),
    ("browser_use", "🌐 Browser Use", "browser_focus", "تعامل با صفحات وب — ویژگی واقعی‌اش."),
    ("agent_zero", "0️⃣ Agent Zero", "autonomous_fast", "عمومی و خودمختار."),
    ("autogen", "🕸 AutoGen", "multi_agent_sim", "فریمورک چندعامله — اینجا شبیه‌سازی‌شده تو یک ایجنت."),
    ("crewai", "👥 CrewAI", "multi_agent_sim", "فریمورک چندعامله — شبیه‌سازی‌شده."),
    ("langgraph", "🔗 LangGraph", "multi_agent_sim", "فریمورک گراف‌محور — شبیه‌سازی‌شده."),
    ("autogpt", "♾ AutoGPT", "autonomous_fast", "حلقه‌ی خودمختار کلاسیک به‌سمت هدف."),
    ("openai_agents_sdk", "🧵 OpenAI Agents SDK", "multi_agent_sim", "فریمورک چندعامله — شبیه‌سازی‌شده."),
    ("google_adk", "🧱 Google ADK", "multi_agent_sim", "فریمورک چندعامله — شبیه‌سازی‌شده."),
    ("ms_agent_framework", "🪟 Microsoft Agent Framework", "multi_agent_sim", "فریمورک چندعامله — شبیه‌سازی‌شده."),
]

DEFAULT_PROFILE_KEY = "default"


def get_agent(key: str) -> dict:
    if key == DEFAULT_PROFILE_KEY or not key:
        return {"key": "default", "label": "🧠 پیش‌فرض (متعادل)", "template": "balanced", "note": "رفتار پیش‌فرض ربات."}
    for k, label, template, note in AGENT_CATALOG:
        if k == key:
            return {"key": k, "label": label, "template": template, "note": note}
    return {"key": "default", "label": "🧠 پیش‌فرض (متعادل)", "template": "balanced", "note": "رفتار پیش‌فرض ربات."}


def get_template(template_key: str) -> dict:
    return TEMPLATES.get(template_key, TEMPLATES["balanced"])


def token_badge(key: str) -> str:
    agent = get_agent(key)
    tmpl = get_template(agent["template"])
    return VERBOSITY_LABEL.get(tmpl["verbosity"], "🔋 متوسط")


def catalog_page(page: int, page_size: int = 8) -> tuple[list[tuple], int]:
    total_pages = max(1, (len(AGENT_CATALOG) + page_size - 1) // page_size)
    page = max(0, min(page, total_pages - 1))
    start = page * page_size
    return AGENT_CATALOG[start:start + page_size], total_pages
