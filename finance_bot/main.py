import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from finance_bot.config import settings
from finance_bot.database import init_db
from finance_bot.handlers import common, transaction, reporting

# Логи
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

bot = Bot(token=settings.BOT_TOKEN.get_secret_value())

dp = Dispatcher(storage=MemoryStorage())

dp.include_router(common.router)
dp.include_router(transaction.router)
dp.include_router(reporting.router)

async def main():
    print("🚀 Бот запускается...")
    # создаем таблицы
    await init_db()
    # удаляем webhook
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())