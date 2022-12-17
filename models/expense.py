from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, select, Date, cast, Float
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship

from core.db import Base
from core.exceptions import GetFromDatabaseException, NotCorrectMessage
from models.base import BaseOrmMixin
from schemas.expense import ExpenseSchema


class Expense(Base, BaseOrmMixin):
    __tablename__ = "expense"

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    created = Column(DateTime, nullable=False)
    category_id = Column(Integer, ForeignKey('category.id', ondelete='CASCADE'), nullable=False)

    @classmethod
    async def get_statistics(cls, db: AsyncSession, period: str):
        if period == 'month':
            deadline = datetime.utcnow().replace(day=1).date()
        else:
            deadline = datetime.utcnow().date()

        query = select(
            Category.name, cls.amount, cls.created
        ).join(Category).where(cast(cls.created, Date) >= deadline).order_by(cls.category_id)

        try:
            expenses = await db.execute(query)
            expenses = expenses.all()
        except SQLAlchemyError as ex:
            await db.rollback()
            raise GetFromDatabaseException(f'Error get {cls.__name__} from finance database :: {ex}')
        return [ExpenseSchema.from_db(e) for e in expenses]


class Aliase(Base, BaseOrmMixin):
    __tablename__ = "aliases"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    category_id = Column(Integer, ForeignKey('category.id', ondelete='CASCADE'), nullable=False)


class Category(Base, BaseOrmMixin):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    expenses = relationship('Expense', cascade='all, delete, save-update, merge, delete-orphan')
    aliases = relationship('Aliase', cascade='all, delete, save-update, merge, delete-orphan')

    @classmethod
    async def get_category_id(cls, db: AsyncSession, category_name: str):
        category = await cls.by_name(db=db, name=category_name)
        if category:
            return category.id
        alias = await Aliase.by_name(db=db, name=category_name)
        if not alias:
            raise NotCorrectMessage(f"Категории с именем '{category_name}' не существует")
        return alias.category_id


class Budget(Base, BaseOrmMixin):
    __tablename__ = "budget"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    daily_limit = Column(Float, nullable=False)

    @classmethod
    async def get(cls, db: AsyncSession):
        budget = await db.execute(select(cls))
        budget = budget.first()
        if not budget:
            return
        (budget,) = budget
        return budget
