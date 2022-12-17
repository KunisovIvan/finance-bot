from datetime import datetime
from typing import Tuple

from pydantic import BaseModel


class MessageSchema(BaseModel):
    amount: float
    category_text: str


class ExpenseSchema(BaseModel):
    id: int = None
    amount: float
    category: str
    created: datetime = None

    @classmethod
    def from_db(cls, expense: Tuple[int, str, float, datetime]):
        expense_id, category, amount, created = expense
        return cls(id=expense_id, category=category, amount=amount, created=created)

