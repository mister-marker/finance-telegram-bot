from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from aiogram.types import Update

from finance_bot.config import settings
from finance_bot.main import bot, dp
from finance_bot.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.BASE_WEBHOOK_URL:
        raise RuntimeError(
            "BASE_WEBHOOK_URL is not set in .env — cannot register the Telegram webhook"
        )

    print("🚀 Запуск FastAPI...")

    # создаем таблицы
    await init_db()

    # webhook URL берётся из конфигурации, а не задаётся в коде
    webhook_url = f"{settings.BASE_WEBHOOK_URL.rstrip('/')}{settings.WEBHOOK_PATH}"
    await bot.set_webhook(webhook_url)

    print(f"✅ Webhook установлен: {webhook_url}")

    yield

    # корректно закрываем сессию бота при остановке
    await bot.session.close()


app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    update = Update(**data)

    # передаем обновление в aiogram
    await dp.feed_update(bot, update)

    return {"ok": True}
