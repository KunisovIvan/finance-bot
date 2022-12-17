from aiogram import Bot
from aiogram import Dispatcher, executor, types

from core import exceptions, expenses
from core.db import async_session
from core.logging_utils import logger
from core.middlewares import AccessMiddleware
from core.settings import settings
from models import Category

bot = Bot(token=settings.API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(AccessMiddleware(settings.ACCESS_IDS))


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """Отправляет приветственное сообщение и помощь по боту"""
    await message.answer(
        "Бот для учёта финансов\n\n"
        "Добавить расход: 250 такси\n"
        "Сегодняшняя статистика: /today\n"
        "За текущий месяц: /month\n"
        "Последние внесённые расходы: /expenses\n"
        "Категории трат: /categories")


@dp.message_handler(lambda message: message.text.startswith('/del'))
async def del_expense(message: types.Message):
    """Удаляет одну запись о расходе по её идентификатору"""
    expense_id = int(message.text[4:])
    await expenses.delete_expense(expense_id)
    answer_message = "Удалил"
    await message.answer(answer_message)


@dp.message_handler(commands=['categories'])
async def categories_list(message: types.Message):
    """Отправляет список категорий расходов"""
    async with async_session() as db:
        categories = await Category.get_all(db=db, selectinload_attr='aliases')
    answer_message = "Категории трат:\n\n* " +\
                     ("\n* ".join([c.name+' ('+", ".join([a.name for a in c.aliases])+')' for c in categories]))
    await message.answer(answer_message)


@dp.message_handler(commands=['today'])
async def today_statistics(message: types.Message):
    """Отправляет сегодняшнюю статистику трат"""
    answer_message = await expenses.get_today_statistics()
    await message.answer(answer_message)


@dp.message_handler(commands=['month'])
async def month_statistics(message: types.Message):
    """Отправляет статистику трат текущего месяца"""
    answer_message = await expenses.get_month_statistics()
    await message.answer(answer_message)


@dp.message_handler()
async def add_expense(message: types.Message):
    """Добавляет новый расход"""
    try:
        e = await expenses.add_expense(message.text)
    except exceptions.NotCorrectMessage as e:
        await message.answer(str(e))
        return
    answer_message = (
        f"Добавлены траты {e.amount} {settings.CURRENCY} на {e.category}.\n\n"
        f"{await expenses.get_today_statistics()}")
    await message.answer(answer_message)


if __name__ == '__main__':
    logger.info(f'Start Finance TG Bot with settings: {settings.dict()}')
    executor.start_polling(dp, skip_updates=True)
