"""
حلقه‌ی ایجنت: مستقل از اینکه پرووایدر متن از function-calling رسمی پشتیبانی کنه یا نه،
از یک قرارداد ساده‌ی متنی استفاده می‌کنیم تا روی همه‌ی پرووایدرها (OpenAI/Anthropic/Gemini/...)
یکسان کار کنه.

مدل باید وقتی می‌خواد ابزاری صدا بزنه، دقیقا یک بلاک به این شکل توی پاسخش بذاره:

```tool
{"tool": "web_search", "args": {"query": "..."}}
```

بعد از اجرای ابزار، نتیجه به‌عنوان یک پیام user جدید (با پیشوند [نتیجه ابزار]) به مکالمه
اضافه می‌شه و دوباره از مدل جواب می‌خوایم. این حلقه تا وقتی مدل بدون بلاک tool جواب بده
یا به سقف تکرار برسه ادامه پیدا می‌کنه.
"""
import json
import re
from . import ai_client, websearch, sandbox, config

TOOL_BLOCK_RE = re.compile(r"```tool\s*(\{.*?\})\s*```", re.DOTALL)

SYSTEM_PROMPT_TEMPLATE = """تو یک ایجنت هوش مصنوعیِ شخصیِ کاربر هستی، فارسی و حرفه‌ای صحبت می‌کنی.
می‌تونی از ابزارهای زیر (اگه در دسترس باشن) استفاده کنی. برای صدا زدن یک ابزار، دقیقا این
فرمت رو توی پاسخت بذار (و فقط همینو بفرست، بدون متن اضافه قبل/بعدش وقتی ابزار صدا می‌زنی):

```tool
{{"tool": "TOOL_NAME", "args": {{...}}}}
```

ابزارهای در دسترس:
{tools_desc}

بعد از گرفتن نتیجه‌ی ابزار، یا ابزار دیگه صدا بزن یا جواب نهایی رو به فارسی روون و کامل بده.
اگه هیچ ابزاری لازم نیست، مستقیم و طبیعی جواب بده — لازم نیست همیشه از ابزار استفاده کنی.
"""

TOOL_DESCRIPTIONS = {
    "web_search": '{"tool": "web_search", "args": {"query": "متن جستجو"}} — جستجوی وب و گرفتن نتایج تازه',
    "browser": '{"tool": "browser", "args": {"url": "..."}} — باز کردن یک صفحه‌ی وب و خوندن متنش',
    "code_exec": '{"tool": "code_exec", "args": {"language": "python|javascript|bash", "code": "..."}} — اجرای کد در محیط شخصی کاربر',
    "install_package": '{"tool": "install_package", "args": {"manager": "pip|npm", "package": "..."}} — نصب یک پکیج در محیط کاربر',
    "image_gen": '{"tool": "image_gen", "args": {"prompt": "..."}} — ساخت تصویر (نیازمند API تصویر فعال کاربر)',
    "video_gen": '{"tool": "video_gen", "args": {"prompt": "..."}} — ساخت ویدیو (نیازمند API ویدیو فعال کاربر)',
}


def build_system_prompt(enabled_tools: list[str]) -> str:
    desc = "\n".join(f"- {TOOL_DESCRIPTIONS[t]}" for t in enabled_tools if t in TOOL_DESCRIPTIONS)
    if not desc:
        desc = "(هیچ ابزاری فعلا فعال نیست، فقط با دانش خودت جواب بده)"
    return SYSTEM_PROMPT_TEMPLATE.format(tools_desc=desc)


def extract_tool_call(text: str) -> dict | None:
    m = TOOL_BLOCK_RE.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def strip_tool_block(text: str) -> str:
    return TOOL_BLOCK_RE.sub("", text).strip()


class ToolContext:
    """برای استریم کردن وضعیت میانی (مثلا '🔎 در حال جستجو...') به تلگرام."""

    def __init__(self, on_status=None):
        self.on_status = on_status  # async callable(str)
        self.media: list[tuple[str, object]] = []  # ("image", bytes) | ("video", url_str)

    async def status(self, text: str):
        if self.on_status:
            await self.on_status(text)


async def execute_tool(user_id: int, call: dict, ctx: ToolContext,
                        image_provider=None, video_provider=None) -> str:
    tool = call.get("tool")
    args = call.get("args", {}) or {}

    if tool == "web_search":
        query = args.get("query", "")
        await ctx.status(f"🔎 در حال جستجوی وب برای: {query}")
        try:
            results = await websearch.search(query)
        except Exception as e:
            return f"[خطای جستجو]: {e}"
        if not results:
            return "[نتیجه‌ای پیدا نشد]"
        lines = [f"- {r['title']}: {r['snippet']} ({r['url']})" for r in results]
        return "نتایج جستجو:\n" + "\n".join(lines)

    if tool == "browser":
        url = args.get("url", "")
        await ctx.status(f"🌐 در حال باز کردن: {url}")
        try:
            text = await websearch.fetch_page_text(url)
            return f"محتوای صفحه:\n{text}"
        except Exception as e:
            return f"[خطای باز کردن صفحه]: {e}"

    if tool == "code_exec":
        lang = args.get("language", "python")
        code = args.get("code", "")
        await ctx.status(f"🖥 در حال اجرای کد ({lang})...")
        result = await sandbox.run_code(user_id, lang, code)
        out = f"exit_code={result['exit_code']}\nstdout:\n{result['stdout']}\nstderr:\n{result['stderr']}"
        return out

    if tool == "install_package":
        manager = args.get("manager", "pip")
        package = args.get("package", "")
        await ctx.status(f"📦 در حال نصب {package} ({manager})...")
        result = await sandbox.install_package(user_id, manager, package)
        return f"exit_code={result['exit_code']}\nstdout:\n{result['stdout']}\nstderr:\n{result['stderr']}"

    if tool == "image_gen":
        if not image_provider:
            return "[خطا: هیچ API تصویری فعال نکردی. اول از منوی 🔑 مدیریت API یکی اضافه کن]"
        prompt = args.get("prompt", "")
        await ctx.status("🎨 در حال ساخت تصویر...")
        try:
            images = await ai_client.generate_image(
                image_provider["api_style"], image_provider["base_url"],
                _decrypt(image_provider), image_provider["model"], prompt,
            )
            for img_bytes in images:
                ctx.media.append(("image", img_bytes))
            return f"[تصویر با موفقیت ساخته شد و برای کاربر ارسال می‌شود. تعداد: {len(images)}]"
        except ai_client.AIError as e:
            return f"[خطای ساخت تصویر]: {e}"

    if tool == "video_gen":
        if not video_provider:
            return "[خطا: هیچ API ویدیویی فعال نکردی. اول از منوی 🔑 مدیریت API یکی اضافه کن]"
        prompt = args.get("prompt", "")
        await ctx.status("🎬 در حال ساخت ویدیو (ممکنه چند دقیقه طول بکشه)...")
        try:
            urls = await ai_client.generate_video(
                video_provider["api_style"], video_provider["base_url"],
                _decrypt(video_provider), video_provider["model"], prompt,
            )
            for url in urls:
                ctx.media.append(("video", url))
            return f"[ویدیو با موفقیت ساخته شد و لینکش برای کاربر ارسال می‌شود: {', '.join(urls)}]"
        except ai_client.AIError as e:
            return f"[خطای ساخت ویدیو]: {e}"

    return f"[ابزار ناشناخته: {tool}]"


def _decrypt(provider_row) -> str:
    from . import crypto
    return crypto.decrypt(provider_row["api_key_enc"])
