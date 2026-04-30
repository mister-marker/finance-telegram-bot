from fastapi import FastAPI, Request
from aiogram.types import Update

from finance_bot.main import bot, dp
from finance_bot.database import init_db

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    print("🚀 Запуск FastAPI...")

    # создаем таблицы
    await init_db()

    # webhook URL
    webhook_url = "https://finance-telegram-bot-i09l.onrender.com/webhook"

    await bot.set_webhook(webhook_url)

    print(f"✅ Webhook установлен: {webhook_url}")


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    update = Update(**data)

    # передаем обновление в aiogram
    await dp.feed_update(bot, update)

    return {"ok": True}