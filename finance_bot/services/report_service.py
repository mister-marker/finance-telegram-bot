import csv
import io
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from finance_bot.database import AsyncSessionLocal
from finance_bot.models import Transaction, Category, User

class ReportService:
    @staticmethod
    async def get_report_data(user_telegram_id: int, period: str):
        now = datetime.now(timezone.utc)
        if period == "day":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "month":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = now # Fallback
            
        async with AsyncSessionLocal() as session:
            query = (
                select(Transaction)
                .join(User)
                .join(Category)
                .options(selectinload(Transaction.category))
                .where(
                    User.telegram_id == user_telegram_id,
                    Transaction.created_at >= start_date
                )
            )
            result = await session.execute(query)
            transactions = result.scalars().all()
            
        income = sum(t.amount for t in transactions if t.category.is_income)
        expense = sum(t.amount for t in transactions if not t.category.is_income)
        
        return {
            "income": income,
            "expense": expense,
            "balance": income - expense,
            "count": len(transactions),
            "start_date": start_date
        }

    @staticmethod
    async def generate_csv(user_telegram_id: int) -> io.StringIO:
        async with AsyncSessionLocal() as session:
            query = (
                select(Transaction)
                .join(User)
                .join(Category)
                .options(selectinload(Transaction.category))
                .where(User.telegram_id == user_telegram_id)
                .order_by(Transaction.created_at.desc())
            )
            result = await session.execute(query)
            transactions = result.scalars().all()
            
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Дата", "Тип", "Категория", "Сумма", "Описание"])
        
        for t in transactions:
            writer.writerow([
                t.created_at.strftime("%Y-%m-%d %H:%M"),
                "Доход" if t.category.is_income else "Расход",
                t.category.name,
                t.amount,
                t.description or ""
            ])
            
        output.seek(0)
        return output
