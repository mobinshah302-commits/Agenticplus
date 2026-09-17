import json
import time
import aiosqlite
from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    created_at INTEGER NOT NULL,
    active_chat_id INTEGER,
    active_provider_id INTEGER,
    temperature REAL DEFAULT 0.7,
    daily_token_limit INTEGER DEFAULT 200000,
    monthly_token_limit INTEGER DEFAULT 3000000,
    tokens_used_today INTEGER DEFAULT 0,
    tokens_used_month INTEGER DEFAULT 0,
    last_reset_day TEXT,
    last_reset_month TEXT,
    tools_enabled TEXT DEFAULT '{"web_search":true,"code_exec":true,"image_gen":true,"video_gen":true,"browser":true,"list_files":true,"send_file":true}',
    code_timeout INTEGER DEFAULT 300,
    agent_profile TEXT DEFAULT 'default'
);

CREATE TABLE IF NOT EXISTS providers (
    provider_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    kind TEXT NOT NULL,              -- 'chat' | 'image' | 'video'
    name TEXT NOT NULL,              -- نام نمایشی (مثلا OpenAI, Custom)
    api_style TEXT NOT NULL,         -- 'openai' | 'anthropic' | 'gemini' | 'replicate' | 'stability'
    base_url TEXT,
    api_key_enc TEXT NOT NULL,
    model TEXT,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS chats (
    chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    msg_id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    role TEXT NOT NULL,              -- 'user' | 'assistant' | 'tool'
    content TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
"""


class DB:
    def __init__(self):
        self.conn: aiosqlite.Connection | None = None

    async def init(self):
        self.conn = await aiosqlite.connect(config.DB_PATH)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.executescript(SCHEMA)
        await self.conn.commit()
        await self._migrate()

    async def _migrate(self):
        """اضافه کردن ستون‌های جدید به دیتابیس‌های قدیمی که از قبل ساخته شدن."""
        migrations = [
            "ALTER TABLE users ADD COLUMN agent_profile TEXT DEFAULT 'default'",
        ]
        for stmt in migrations:
            try:
                await self.conn.execute(stmt)
                await self.conn.commit()
            except Exception:
                pass  # ستون از قبل وجود داره

    # ---------- users ----------
    async def ensure_user(self, user_id: int):
        await self.conn.execute(
            "INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?, ?)",
            (user_id, int(time.time())),
        )
        await self.conn.commit()

    async def get_user(self, user_id: int) -> aiosqlite.Row:
        await self.ensure_user(user_id)
        cur = await self.conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return await cur.fetchone()

    async def update_user(self, user_id: int, **fields):
        if not fields:
            return
        cols = ", ".join(f"{k}=?" for k in fields)
        vals = list(fields.values()) + [user_id]
        await self.conn.execute(f"UPDATE users SET {cols} WHERE user_id=?", vals)
        await self.conn.commit()

    DEFAULT_TOOLS = {
        "web_search": True, "code_exec": True, "image_gen": True, "video_gen": True,
        "browser": True, "list_files": True, "send_file": True,
    }

    async def get_tools_enabled(self, user_id: int) -> dict:
        u = await self.get_user(user_id)
        try:
            tools = json.loads(u["tools_enabled"])
        except Exception:
            tools = {}
        merged = dict(self.DEFAULT_TOOLS)
        merged.update(tools)
        return merged

    async def set_tool_enabled(self, user_id: int, tool: str, value: bool):
        tools = await self.get_tools_enabled(user_id)
        tools[tool] = value
        await self.update_user(user_id, tools_enabled=json.dumps(tools))

    async def set_tools_bulk(self, user_id: int, updates: dict):
        tools = await self.get_tools_enabled(user_id)
        tools.update(updates)
        await self.update_user(user_id, tools_enabled=json.dumps(tools))

    # ---------- agent profile (persona) ----------
    async def get_agent_profile(self, user_id: int) -> str:
        u = await self.get_user(user_id)
        try:
            return u["agent_profile"] or "default"
        except Exception:
            return "default"

    async def set_agent_profile(self, user_id: int, profile_key: str):
        await self.update_user(user_id, agent_profile=profile_key)

    # ---------- providers (API keys) ----------
    async def add_provider(self, user_id: int, kind: str, name: str, api_style: str,
                            base_url: str | None, api_key_enc: str, model: str | None) -> int:
        cur = await self.conn.execute(
            "INSERT INTO providers (user_id, kind, name, api_style, base_url, api_key_enc, model, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (user_id, kind, name, api_style, base_url, api_key_enc, model, int(time.time())),
        )
        await self.conn.commit()
        return cur.lastrowid

    async def list_providers(self, user_id: int, kind: str | None = None):
        if kind:
            cur = await self.conn.execute(
                "SELECT * FROM providers WHERE user_id=? AND kind=? ORDER BY provider_id DESC", (user_id, kind)
            )
        else:
            cur = await self.conn.execute(
                "SELECT * FROM providers WHERE user_id=? ORDER BY provider_id DESC", (user_id,)
            )
        return await cur.fetchall()

    async def get_provider(self, provider_id: int):
        cur = await self.conn.execute("SELECT * FROM providers WHERE provider_id=?", (provider_id,))
        return await cur.fetchone()

    async def delete_provider(self, provider_id: int):
        await self.conn.execute("DELETE FROM providers WHERE provider_id=?", (provider_id,))
        await self.conn.commit()

    async def set_provider_model(self, provider_id: int, model: str):
        await self.conn.execute("UPDATE providers SET model=? WHERE provider_id=?", (model, provider_id))
        await self.conn.commit()

    # ---------- chats ----------
    async def create_chat(self, user_id: int, title: str = "چت جدید") -> int:
        cur = await self.conn.execute(
            "INSERT INTO chats (user_id, title, created_at) VALUES (?,?,?)",
            (user_id, title, int(time.time())),
        )
        await self.conn.commit()
        chat_id = cur.lastrowid
        await self.update_user(user_id, active_chat_id=chat_id)
        return chat_id

    async def list_chats(self, user_id: int, limit: int = 50):
        cur = await self.conn.execute(
            "SELECT * FROM chats WHERE user_id=? ORDER BY chat_id DESC LIMIT ?", (user_id, limit)
        )
        return await cur.fetchall()

    async def get_chat(self, chat_id: int):
        cur = await self.conn.execute("SELECT * FROM chats WHERE chat_id=?", (chat_id,))
        return await cur.fetchone()

    async def set_chat_title_if_default(self, chat_id: int, title: str):
        chat = await self.get_chat(chat_id)
        if chat and chat["title"] == "چت جدید":
            await self.conn.execute("UPDATE chats SET title=? WHERE chat_id=?", (title[:60], chat_id))
            await self.conn.commit()

    async def delete_chat(self, chat_id: int):
        await self.conn.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
        await self.conn.execute("DELETE FROM chats WHERE chat_id=?", (chat_id,))
        await self.conn.commit()

    # ---------- messages ----------
    async def add_message(self, chat_id: int, role: str, content: str):
        await self.conn.execute(
            "INSERT INTO messages (chat_id, role, content, created_at) VALUES (?,?,?,?)",
            (chat_id, role, content, int(time.time())),
        )
        await self.conn.commit()

    async def get_messages(self, chat_id: int, limit: int = 60):
        cur = await self.conn.execute(
            "SELECT * FROM messages WHERE chat_id=? ORDER BY msg_id ASC LIMIT ?", (chat_id, limit)
        )
        return await cur.fetchall()

    async def get_first_user_message(self, chat_id: int) -> str | None:
        cur = await self.conn.execute(
            "SELECT content FROM messages WHERE chat_id=? AND role='user' ORDER BY msg_id ASC LIMIT 1",
            (chat_id,),
        )
        row = await cur.fetchone()
        return row["content"] if row else None


db = DB()
