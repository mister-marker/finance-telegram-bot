from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from finance_bot.database import AsyncSessionLocal
from finance_bot.models import User, Category
from finance_bot.key_boards import get_main_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(telegram_id=message.from_user.id, username=message.from_user.username)
            session.add(user)
            await session.flush()

            #
            default_cats = [
                ("Зарплата", True), ("Бонус", True),
                ("Еда", False), ("Транспорт", False), ("Развлечения", False), ("Прочее", False)
            ]
            for name, is_income in default_cats:
                session.add(Category(user_id=user.id, name=name, is_income=is_income, is_default=True))
            
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
    
    await message.answer(
        "Добро пожаловать в Finance Bot! 💰\nИспользуйте меню ниже для управления финансами.",
        reply_markup=get_main_keyboard()
    )

@router.message(F.text == "❌ Отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=get_main_keyboard())
