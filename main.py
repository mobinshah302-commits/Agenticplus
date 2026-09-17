import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot import config
from bot.db import db
from bot.handlers import main_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("agentbot")


async def main():
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN تنظیم نشده! متغیر محیطی BOT_TOKEN رو ست کن.")

    await db.init()
    log.info("دیتابیس آماده شد.")

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(main_router)

    log.info("ربات در حال اجراست...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
