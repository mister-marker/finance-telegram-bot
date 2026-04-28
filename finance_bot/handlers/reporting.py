from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext

from finance_bot.key_boards import get_report_period_keyboard
from finance_bot.services.report_service import ReportService

router = Router()

@router.message(F.text == "📊 Отчет")
async def cmd_report(message: Message):
    await message.answer("Выберите период отчета:", reply_markup=get_report_period_keyboard())

@router.callback_query(F.data.startswith("report_"))
async def process_report_callback(callback: CallbackQuery):
    period = callback.data.split("_")[1]
    data = await ReportService.get_report_data(callback.from_user.id, period)
    
    period_names = {"day": "день", "week": "неделю", "month": "месяц"}
    period_name = period_names.get(period, period)

    text = (
        f"📊 **Отчет за {period_name}**\n\n"
        f"💰 Доход: {data['income']:.2f}\n"
        f"💸 Расход: {data['expense']:.2f}\n"
        f"⚖️ Баланс: {data['balance']:.2f}\n\n"
        f"Транзакций: {data['count']}\n"
        f"С даты: {data['start_date'].strftime('%Y-%m-%d')}"
    )
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()

@router.message(F.text == "📥 Экспорт CSV")
async def cmd_export(message: Message):
    wait_msg = await message.answer("Генерация CSV...")
    
    csv_file = await ReportService.generate_csv(message.from_user.id)
    file_bytes = csv_file.getvalue().encode()
    
    input_file = BufferedInputFile(file_bytes, filename=f"finance_export_{message.from_user.id}.csv")
    
    await message.answer_document(input_file, caption="Вот ваши финансовые данные.")
    await wait_msg.delete()
