from datetime import datetime
from typing import List

from pydantic import BaseModel

from models import Category, Expense


class MessageSchema(BaseModel):
    amount: float
    category_text: str


class ExpenseSchema(BaseModel):
    id: int = None
    amount: float
    created: datetime = None
    category_name: str = None

    @classmethod
    def from_db(cls, e: Expense):
        return cls(id=e.id, amount=e.amount, created=e.created)


class CategorySchema(BaseModel):
    id: int
    name: str
    expenses: List[ExpenseSchema] = []

    @classmethod
    def from_db(cls, c: Category):
        return cls(
            id=c.id,
            name=c.name,
            expenses=[ExpenseSchema.from_db(e) for e in c.expenses]
        )
