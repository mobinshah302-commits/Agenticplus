"""
پریست‌های API های معروف. کاربر فقط کلید رو می‌زنه، بقیه‌ی تنظیمات (آدرس، فرمت) خودکاره.
"""

# ---- ارائه‌دهنده‌های متن (chat) معروف ----
CHAT_PRESETS = {
    "openai": {
        "label": "🟢 OpenAI (GPT)",
        "api_style": "openai",
        "base_url": "https://api.openai.com/v1",
    },
    "anthropic": {
        "label": "🟣 Anthropic (Claude)",
        "api_style": "anthropic",
        "base_url": "https://api.anthropic.com/v1",
    },
    "gemini": {
        "label": "🔵 Google (Gemini)",
        "api_style": "gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
    },
    "openrouter": {
        "label": "🌐 OpenRouter",
        "api_style": "openai",
        "base_url": "https://openrouter.ai/api/v1",
    },
    "groq": {
        "label": "⚡ Groq",
        "api_style": "openai",
        "base_url": "https://api.groq.com/openai/v1",
    },
    "deepseek": {
        "label": "🐋 DeepSeek",
        "api_style": "openai",
        "base_url": "https://api.deepseek.com/v1",
    },
    "mistral": {
        "label": "🌬️ Mistral",
        "api_style": "openai",
        "base_url": "https://api.mistral.ai/v1",
    },
    "xai": {
        "label": "✖️ xAI (Grok)",
        "api_style": "openai",
        "base_url": "https://api.x.ai/v1",
    },
    "qwen": {
        "label": "🟠 Alibaba (Qwen)",
        "api_style": "openai",
        "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    },
    "together": {
        "label": "🤝 Together AI",
        "api_style": "openai",
        "base_url": "https://api.together.xyz/v1",
    },
}

# ---- ارائه‌دهنده‌های تصویر ----
IMAGE_PRESETS = {
    "openai_image": {
        "label": "🟢 OpenAI (DALL·E)",
        "api_style": "openai_image",
        "base_url": "https://api.openai.com/v1",
    },
    "stability": {
        "label": "🎨 Stability AI",
        "api_style": "stability",
        "base_url": "https://api.stability.ai",
    },
    "replicate_image": {
        "label": "🔁 Replicate",
        "api_style": "replicate",
        "base_url": "https://api.replicate.com/v1",
    },
}

# ---- ارائه‌دهنده‌های ویدیو ----
VIDEO_PRESETS = {
    "replicate_video": {
        "label": "🔁 Replicate (Video Models)",
        "api_style": "replicate",
        "base_url": "https://api.replicate.com/v1",
    },
}

ALL_PRESETS = {"chat": CHAT_PRESETS, "image": IMAGE_PRESETS, "video": VIDEO_PRESETS}
