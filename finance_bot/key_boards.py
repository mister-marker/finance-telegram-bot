from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Доход"), KeyboardButton(text="➖ Расход")],
            [KeyboardButton(text="📊 Отчет"), KeyboardButton(text="📥 Экспорт CSV")],
            [KeyboardButton(text="⚙️ Настройки")]
        ],
        resize_keyboard=True,
        persistent=True
    )

def get_report_period_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Сегодня", callback_data="report_day")
    builder.button(text="Неделя", callback_data="report_week")
    builder.button(text="Месяц", callback_data="report_month")
    builder.adjust(3)
    return builder.as_markup()

def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
