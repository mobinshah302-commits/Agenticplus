from aiogram import Router

from . import start, providers_h, chats, tools_h, settings_h, messages_h

main_router = Router()
main_router.include_router(start.router)
main_router.include_router(providers_h.router)
main_router.include_router(chats.router)
main_router.include_router(tools_h.router)
main_router.include_router(settings_h.router)
main_router.include_router(messages_h.router)  # همیشه آخر - چون هر متنی رو می‌گیره
