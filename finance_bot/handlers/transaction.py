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

@router.message(F.text.in_({"➕ Доход", "➖ Расход"}))
async def start_transaction(message: Message, state: FSMContext):
    is_income = message.text == "➕ Доход"
    await state.update_data(is_income=is_income)
    await state.set_state(TransactionStates.waiting_for_amount)
    await message.answer(
        f"Введите сумму {'дохода' if is_income else 'расхода'}:",
        reply_markup=get_cancel_keyboard()
    )

@router.message(TransactionStates.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите корректное положительное число.")
        return

    await state.update_data(amount=amount)
    
    # Get categories
    data = await state.get_data()
    is_income = data['is_income']
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Category)
            .join(User)
            .where(User.telegram_id == message.from_user.id, Category.is_income == is_income)
        )
        categories = result.scalars().all()
    
    if not categories:
        await message.answer("Категории не найдены. Пожалуйста, обратитесь к настройкам.", reply_markup=get_main_keyboard())
        await state.clear()
        return

    # Build category keyboard
    kb_rows = [[KeyboardButton(text=c.name)] for c in categories]
    kb_rows.append([KeyboardButton(text="❌ Отмена")])
    keyboard = ReplyKeyboardMarkup(keyboard=kb_rows, resize_keyboard=True)
    
    await state.set_state(TransactionStates.waiting_for_category)
    await message.answer("Выберите категорию:", reply_markup=keyboard)

@router.message(TransactionStates.waiting_for_category)
async def process_category(message: Message, state: FSMContext):
    category_name = message.text
    data = await state.get_data()
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Category)
            .join(User)
            .where(
                User.telegram_id == message.from_user.id, 
                Category.name == category_name,
                Category.is_income == data['is_income']
            )
        )
        category = result.scalar_one_or_none()
        
        if not category:
            await message.answer("Неверная категория. Пожалуйста, выберите из списка.")
            return
        
        await state.update_data(category_id=category.id)
    
    await state.set_state(TransactionStates.waiting_for_description)
    await message.answer("Введите описание (или отправьте '-' чтобы пропустить):", reply_markup=get_cancel_keyboard())

@router.message(TransactionStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    description = message.text if message.text != "-" else None
    data = await state.get_data()
    
    async with AsyncSessionLocal() as session:
        # Get user id maps to telegram_id
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one()
        
        transaction = Transaction(
            user_id=user.id,
            category_id=data['category_id'],
            amount=data['amount'],
            description=description
        )
        session.add(transaction)
        await session.commit()
    
    await state.clear()
    await message.answer("Транзакция сохранена! ✅", reply_markup=get_main_keyboard())
