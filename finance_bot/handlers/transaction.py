from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from finance_bot.database import AsyncSessionLocal
from finance_bot.models import User, Category, Transaction
from finance_bot.key_boards import get_main_keyboard, get_cancel_keyboard

router = Router()


class TransactionStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_category = State()
    waiting_for_description = State()


# старт операции
@router.message(F.text.in_({"➕ Доход", "➖ Расход"}))
async def start_transaction(message: Message, state: FSMContext):
    is_income = message.text == "➕ Доход"
    await state.update_data(is_income=is_income)
    await state.set_state(TransactionStates.waiting_for_amount)

    await message.answer(
        f"Введите сумму {'дохода' if is_income else 'расхода'}:",
        reply_markup=get_cancel_keyboard()
    )


# ввод суммы
@router.message(TransactionStates.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            raise ValueError
    except Exception:
        await message.answer("Введите корректное число больше 0")
        return

    await state.update_data(amount=amount)

    data = await state.get_data()
    is_income = data.get("is_income")

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Category)
            .join(User)
            .where(
                User.telegram_id == message.from_user.id,
                Category.is_income == is_income
            )
        )
        categories = result.scalars().all()

    if not categories:
        await message.answer(
            "Нет категорий. Сначала добавь их.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        return

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=c.name)] for c in categories] +
                 [[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

    await state.set_state(TransactionStates.waiting_for_category)
    await message.answer("Выбери категорию:", reply_markup=keyboard)


# выбор категории
@router.message(TransactionStates.waiting_for_category)
async def process_category(message: Message, state: FSMContext):
    category_name = message.text
    data = await state.get_data()
    is_income = data.get("is_income")

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Category)
            .join(User)
            .where(
                User.telegram_id == message.from_user.id,
                Category.name == category_name,
                Category.is_income == is_income
            )
        )
        category = result.scalar_one_or_none()

    if category is None:
        await message.answer("Выбери категорию из списка")
        return

    await state.update_data(category_id=category.id)

    await state.set_state(TransactionStates.waiting_for_description)
    await message.answer(
        "Описание (или '-' чтобы пропустить):",
        reply_markup=get_cancel_keyboard()
    )


# 📝 описание + сохранение
@router.message(TransactionStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    description = message.text if message.text != "-" else None
    data = await state.get_data()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            await message.answer("Ошибка: пользователь не найден")
            await state.clear()
            return

        transaction = Transaction(
            user_id=user.id,
            category_id=data.get("category_id"),
            amount=data.get("amount"),
            description=description
        )

        session.add(transaction)
        await session.commit()

    await state.clear()
    await message.answer(
        " ✅ Сохранено ✅ ",
        reply_markup=get_main_keyboard()
    )