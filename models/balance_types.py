from datetime import date
from typing import List

import strawberry

from models.types import Decimal

# Resultados calculados: no son tablas ni se aceptan como entrada.


@strawberry.type
class AccountBalance:
    account_id: strawberry.ID
    account_name: str
    is_active: bool
    opening_balance: Decimal
    total_income: Decimal
    total_expense: Decimal
    profit: Decimal
    closing_balance: Decimal
    is_in_red: bool


@strawberry.type
class GeneralBalance:
    company_id: strawberry.ID
    currency: str
    from_date: date
    to_date: date
    opening_balance: Decimal
    total_income: Decimal
    total_expense: Decimal
    profit: Decimal
    closing_balance: Decimal
    is_in_red: bool
    accounts_in_red: int
    accounts: List[AccountBalance]


def general_balance_from_dict(data):
    return GeneralBalance(**{**data, "accounts": [AccountBalance(**c) for c in data["accounts"]]})
