import re
from datetime import datetime
from typing import List

from core import exceptions
from core.db import async_session
from core.settings import settings
from models import Expense, Category, Budget
from schemas.expense import MessageSchema, ExpenseSchema


async def add_expense(raw_message: str):
    """Добавляет новую трату.
    Принимает на вход текст сообщения, пришедшего в бот."""
    m = _parse_message(raw_message)
    async with async_session() as db:
        category_id = await Category.get_category_id(db=db, category_name=m.category_text)
        e = await Expense.create(db=db, amount=m.amount, category_id=category_id, created=datetime.utcnow())
    return ExpenseSchema(id=e.id, amount=e.amount, category=m.category_text)


async def get_today_statistics() -> str:
    """Возвращает строкой статистику расходов за сегодня"""
    async with async_session() as db:
        expenses = await Expense.get_statistics(db=db, period='today')
        expenses = [ExpenseSchema.from_db(e) for e in expenses]
    return (f"Расходы сегодня:\n"
            f"всего — {sum([e.amount for e in expenses])} {settings.CURRENCY} "
            f"из {await _get_budget_limit()}.\n\n" +
            "\n".join([f'{e.amount} {settings.CURRENCY} | {e.category} | {e.created.date()}' for e in expenses]) +
            "\n\nЗа текущий месяц: /month")


async def get_month_statistics() -> str:
    """Возвращает строкой статистику расходов за текущий месяц"""
    async with async_session() as db:
        expenses = await Expense.get_statistics(db=db, period='month')
        expenses = [ExpenseSchema.from_db(e) for e in expenses]
    return (f"Расходы в текущем месяце:\n"
            f"всего — {sum([e.amount for e in expenses])} {settings.CURRENCY} "
            f"из {datetime.utcnow().day * await _get_budget_limit()}\n\n" +
            "\n".join([f'{e.amount} {settings.CURRENCY} | {e.category} | {e.created.date()}' for e in expenses]))


async def delete_expense(expense_id: int) -> None:
    """Удаляет трату по ее идентификатору"""
    async with async_session() as db:
        await Expense.delete_by_id(db=db, instance_id=expense_id)


def _parse_message(raw_message: str) -> MessageSchema:
    """Парсит текст пришедшего сообщения о новом расходе."""
    regexp_result = re.match(r"([\d+\.\d+]+) (.*)", raw_message)
    if not regexp_result or not regexp_result.group(0) \
            or not regexp_result.group(1) or not regexp_result.group(2):
        raise exceptions.NotCorrectMessage(
            "Не могу понять сообщение. Напишите сообщение в формате, "
            "например:\n1500 метро")

    amount = regexp_result.group(1).replace(" ", "")
    category_text = regexp_result.group(2).strip().lower()
    return MessageSchema(amount=float(amount), category_text=category_text)


async def last() -> List[ExpenseSchema]:
    """Возвращает последние несколько расходов"""
    async with async_session() as db:
        expenses = await Expense.get_last(db=db)
        last_expenses = [ExpenseSchema.from_db(e) for e in expenses]
    return last_expenses


async def _get_budget_limit() -> int:
    """Возвращает дневной лимит трат."""
    async with async_session() as db:
        budget = await Budget.get(db=db)
    return budget.daily_limit if budget else 0
