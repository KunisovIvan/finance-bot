import re
from datetime import datetime, timedelta

from core import exceptions
from core.db import async_session
from core.settings import settings
from models import Expense, Category, Budget
from schemas.expense import MessageSchema, ExpenseSchema, CategorySchema


async def add_expense(raw_message: str):
    """
    Добавляет новую трату.
    Принимает на вход текст сообщения, пришедшего в бот.
    """
    m = _parse_message(raw_message)
    async with async_session() as db:
        category_id = await Category.get_category_id(db=db, category_name=m.category_text)
        e = await Expense.create(db=db, amount=m.amount, category_id=category_id, created=datetime.utcnow())
    return ExpenseSchema(id=e.id, amount=e.amount, category_name=m.category_text)


async def get_statistics(period: str) -> str:
    """Возвращает строкой статистику расходов за текущий месяц"""
    async with async_session() as db:
        categories = await Category.get_all(db=db, selectinload_attr='expenses')
        categories = [CategorySchema.from_db(c) for c in categories]
        #
        if period == 'month':
            deadline = datetime.utcnow().replace(day=1).date()
            msg_title = 'Расходы в текущем месяце'
            budget = datetime.utcnow().day * await _get_budget_limit()
        else:
            deadline = datetime.utcnow().date()
            msg_title = 'Расходы за сегодня'
            budget = await _get_budget_limit()
        #
        c_rows = []
        full_amounts = 0
        #
        for c in categories:
            expenses = list(filter(lambda e: e.created.date() >= deadline, c.expenses))
            amount = sum([e.amount for e in expenses])
            if amount > 0:
                full_amounts += amount
                command = f'/cat_d{c.id}' if period == 'today' else f'/cat_m{c.id}'
                c_rows.append(f'{amount} {settings.CURRENCY} | {c.name} | {command}')
    #
    answer_message = (f"{msg_title}:\n всего — {full_amounts} {settings.CURRENCY} из {budget}\n\n" + "\n".join(c_rows))
    if period == 'today':
        answer_message += "\n\nЗа текущий месяц: /month"
    #
    return answer_message


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


async def get_category(category_id, period):
    """Получает одну запись о категории вместе с ее расходами по её идентификатору"""
    async with async_session() as db:
        category = await Category.by_id(db=db, instance_id=category_id, selectinload_attr='expenses')
        c = CategorySchema.from_db(category)
        #
        if period == 'm':
            deadline = datetime.utcnow().date().replace(day=1)
            date_format = '%d-%m-%Y'
            msg_title = f'Расходы по категории {c.name} за месяц'
        else:
            deadline = datetime.utcnow().date()
            date_format = "%H:%M"
            msg_title = f'Расходы по категории {c.name} за сегодня'
        #
        expenses = list(filter(lambda e: e.created.date() >= deadline, c.expenses))
    return (
            f"{msg_title}:\n"
            f"всего — {sum([e.amount for e in expenses])} {settings.CURRENCY}.\n\n" +
            "\n".join([
                f'{e.amount} {settings.CURRENCY} | {c.name} | '
                f'{(e.created + timedelta(hours=settings.DIFFERENCE_WITH_UTC)).strftime(date_format)} | /del{e.id}'
                for e in expenses
            ])
    )


async def _get_budget_limit() -> int:
    """Возвращает дневной лимит трат."""
    async with async_session() as db:
        budget = await Budget.get(db=db)
    return budget.daily_limit if budget else 0
