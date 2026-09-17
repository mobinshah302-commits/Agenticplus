"""
یک لایه‌ی یکپارچه روی چند API مختلف:
- دریافت لیست مدل‌ها (برای نمایش به کاربر بعد از وارد کردن کلید)
- ارسال پیام چت و گرفتن پاسخ (+ تعداد توکن مصرفی، برای اعمال محدودیت مصرف)
- تولید تصویر / ویدیو
"""
import httpx
from typing import Any

TIMEOUT = httpx.Timeout(120.0, connect=20.0)


class AIError(Exception):
    pass


# ============================================================
#                     دریافت لیست مدل‌ها
# ============================================================

async def fetch_models(api_style: str, base_url: str, api_key: str) -> list[str]:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            if api_style in ("openai", "openai_image"):
                r = await client.get(
                    f"{base_url.rstrip('/')}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                r.raise_for_status()
                data = r.json()
                ids = [m["id"] for m in data.get("data", [])]
                return sorted(ids)

            if api_style == "anthropic":
                r = await client.get(
                    f"{base_url.rstrip('/')}/models",
                    headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
                )
                r.raise_for_status()
                data = r.json()
                return [m["id"] for m in data.get("data", [])]

            if api_style == "gemini":
                r = await client.get(f"{base_url.rstrip('/')}/models?key={api_key}")
                r.raise_for_status()
                data = r.json()
                names = []
                for m in data.get("models", []):
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        names.append(m["name"].split("/")[-1])
                return sorted(names)

            if api_style == "replicate":
                # ریپلیکیت مدل رو با owner/name مشخص می‌کنه؛ لیست عمومی نداره، کاربر باید بنویسه
                return []

            if api_style == "stability":
                r = await client.get(
                    f"{base_url.rstrip('/')}/v1/engines/list",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                r.raise_for_status()
                data = r.json()
                return [e["id"] for e in data]

        except httpx.HTTPStatusError as e:
            raise AIError(f"خطا در دریافت مدل‌ها ({e.response.status_code}): {e.response.text[:300]}")
        except Exception as e:
            raise AIError(f"خطا در اتصال به API: {e}")

    return []


# ============================================================
#                      ارسال پیام چت
# ============================================================

async def chat_completion(api_style: str, base_url: str, api_key: str, model: str,
                           messages: list[dict], temperature: float = 0.7,
                           tools_hint: str | None = None) -> dict[str, Any]:
    """
    messages: [{"role": "user"/"assistant"/"system", "content": "..."}]
    خروجی: {"text": str, "input_tokens": int, "output_tokens": int}
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            if api_style == "openai":
                payload = {"model": model, "messages": messages, "temperature": temperature}
                r = await client.post(
                    f"{base_url.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
                r.raise_for_status()
                data = r.json()
                text = data["choices"][0]["message"]["content"] or ""
                usage = data.get("usage", {})
                return {
                    "text": text,
                    "input_tokens": usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("completion_tokens", 0),
                }

            if api_style == "anthropic":
                system_msg = "\n".join(m["content"] for m in messages if m["role"] == "system")
                conv = [m for m in messages if m["role"] != "system"]
                payload = {
                    "model": model,
                    "max_tokens": 4096,
                    "temperature": temperature,
                    "messages": conv,
                }
                if system_msg:
                    payload["system"] = system_msg
                r = await client.post(
                    f"{base_url.rstrip('/')}/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                r.raise_for_status()
                data = r.json()
                text = "".join(b.get("text", "") for b in data.get("content", []))
                usage = data.get("usage", {})
                return {
                    "text": text,
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                }

            if api_style == "gemini":
                system_msg = "\n".join(m["content"] for m in messages if m["role"] == "system")
                contents = []
                for m in messages:
                    if m["role"] == "system":
                        continue
                    role = "model" if m["role"] == "assistant" else "user"
                    contents.append({"role": role, "parts": [{"text": m["content"]}]})
                payload: dict[str, Any] = {
                    "contents": contents,
                    "generationConfig": {"temperature": temperature},
                }
                if system_msg:
                    payload["systemInstruction"] = {"parts": [{"text": system_msg}]}
                r = await client.post(
                    f"{base_url.rstrip('/')}/models/{model}:generateContent?key={api_key}",
                    json=payload,
                )
                r.raise_for_status()
                data = r.json()
                cand = data["candidates"][0]
                text = "".join(p.get("text", "") for p in cand["content"]["parts"])
                usage = data.get("usageMetadata", {})
                return {
                    "text": text,
                    "input_tokens": usage.get("promptTokenCount", 0),
                    "output_tokens": usage.get("candidatesTokenCount", 0),
                }

            raise AIError(f"سبک API پشتیبانی‌نشده برای چت: {api_style}")

        except httpx.HTTPStatusError as e:
            raise AIError(f"خطای API ({e.response.status_code}): {e.response.text[:400]}")
        except AIError:
            raise
        except Exception as e:
            raise AIError(f"خطا در ارتباط با مدل: {e}")


# ============================================================
#                    تولید تصویر
# ============================================================

async def generate_image(api_style: str, base_url: str, api_key: str, model: str, prompt: str) -> list[bytes]:
    """خروجی: لیستی از بایت‌های تصویر تولیدشده"""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            if api_style == "openai_image":
                r = await client.post(
                    f"{base_url.rstrip('/')}/images/generations",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"model": model or "dall-e-3", "prompt": prompt, "n": 1, "size": "1024x1024"},
                )
                r.raise_for_status()
                data = r.json()
                images = []
                for item in data.get("data", []):
                    if "b64_json" in item:
                        import base64
                        images.append(base64.b64decode(item["b64_json"]))
                    elif "url" in item:
                        img_r = await client.get(item["url"])
                        images.append(img_r.content)
                return images

            if api_style == "stability":
                r = await client.post(
                    f"{base_url.rstrip('/')}/v2beta/stable-image/generate/core",
                    headers={"Authorization": f"Bearer {api_key}", "Accept": "image/*"},
                    files={"prompt": (None, prompt), "output_format": (None, "png")},
                )
                r.raise_for_status()
                return [r.content]

            if api_style == "replicate":
                pred = await _replicate_run(client, base_url, api_key, model, {"prompt": prompt})
                images = []
                for url in pred:
                    img_r = await client.get(url)
                    images.append(img_r.content)
                return images

            raise AIError(f"سبک API پشتیبانی‌نشده برای تصویر: {api_style}")

        except httpx.HTTPStatusError as e:
            raise AIError(f"خطای تولید تصویر ({e.response.status_code}): {e.response.text[:300]}")
        except AIError:
            raise
        except Exception as e:
            raise AIError(f"خطا در تولید تصویر: {e}")


# ============================================================
#                    تولید ویدیو (عمدتا از طریق Replicate)
# ============================================================

async def generate_video(api_style: str, base_url: str, api_key: str, model: str, prompt: str) -> list[str]:
    """خروجی: لیستی از URL ویدیوهای تولیدشده (ویدیو معمولا حجیمه، لینکشو می‌فرستیم نه بایت خام)"""
    async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=20.0)) as client:
        try:
            if api_style == "replicate":
                return await _replicate_run(client, base_url, api_key, model, {"prompt": prompt})
            raise AIError(f"سبک API پشتیبانی‌نشده برای ویدیو: {api_style}")
        except httpx.HTTPStatusError as e:
            raise AIError(f"خطای تولید ویدیو ({e.response.status_code}): {e.response.text[:300]}")
        except AIError:
            raise
        except Exception as e:
            raise AIError(f"خطا در تولید ویدیو: {e}")


async def _replicate_run(client: httpx.AsyncClient, base_url: str, api_key: str,
                          model: str, input_payload: dict) -> list[str]:
    """
    model باید به شکل 'owner/name' یا 'owner/name:version' باشه (کاربر موقع افزودن API وارد می‌کنه).
    """
    import asyncio

    r = await client.post(
        f"{base_url.rstrip('/')}/predictions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"version": model, "input": input_payload} if ":" in model else {"model": model, "input": input_payload},
    )
    r.raise_for_status()
    pred = r.json()
    get_url = pred["urls"]["get"]

    for _ in range(120):  # حداکثر ~۱۰ دقیقه صبر
        await asyncio.sleep(5)
        r2 = await client.get(get_url, headers={"Authorization": f"Bearer {api_key}"})
        r2.raise_for_status()
        pred = r2.json()
        if pred["status"] == "succeeded":
            out = pred["output"]
            if isinstance(out, str):
                return [out]
            if isinstance(out, list):
                return out
            return []
        if pred["status"] in ("failed", "canceled"):
            raise AIError(f"تولید محتوا ناموفق بود: {pred.get('error')}")

    raise AIError("زمان تولید محتوا به پایان رسید (timeout)")
