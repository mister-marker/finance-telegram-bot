import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from finance_bot.config import settings
from finance_bot.handlers import common, transaction, reporting

# логирование
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# создаем бота
bot = Bot(token=settings.BOT_TOKEN.get_secret_value())

# диспетчер (маршрутизатор сообщений)
dp = Dispatcher(storage=MemoryStorage())

# подключаем обработчики
dp.include_router(common.router)
dp.include_router(transaction.router)
dp.include_router(reporting.router)