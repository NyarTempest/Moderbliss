import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db

from report import router as report_router
from moderation import router as moderation_router
from admin import router as admin_router
from profile import router as profile_router


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )

    dp = Dispatcher(
        storage=MemoryStorage()
    )

    await init_db()

    dp.include_router(admin_router)
    dp.include_router(profile_router)
    dp.include_router(report_router)
    dp.include_router(moderation_router)

    print("✅ Bot started")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
