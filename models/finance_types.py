from enum import Enum
from typing import Optional

import strawberry

from models.types import Company, Decimal, Time, User
from repositories import account_repository, company_repository, concept_repository, user_repository

# ==================================================
# ENUMS
# ==================================================


@strawberry.enum
class AccountType(Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"
    CASH = "CASH"
    SAVINGS = "SAVINGS"
    INVESTMENT = "INVESTMENT"
    WALLET = "WALLET"
    OTHER = "OTHER"


@strawberry.enum
class ConceptType(Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


@strawberry.enum
class TransactionType(Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


# ==================================================
# DÍA 1: ACCOUNT
# ==================================================

@strawberry.type
class Account:
    id: strawberry.ID
    company_id: strawberry.ID
    account_type: AccountType
    name: str
    bank_name: Optional[str]
    account_number: Optional[str]
    clabe: Optional[str]
    card_last_digits: Optional[str]
    short_description: Optional[str]
    long_description: Optional[str]
    is_active: bool
    created_at: Time
    updated_at: Time

    @strawberry.field
    def company(self) -> Company:
        return Company(**company_repository.obtener_empresa(self.company_id))


def account_from_row(row):
    return Account(**{**row, "account_type": AccountType(row["account_type"])})


@strawberry.input
class CreateAccountInput:
    company_id: strawberry.ID
    account_type: AccountType
    name: str
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    clabe: Optional[str] = None
    card_last_digits: Optional[str] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None


# ==================================================
# DÍA 1: CONCEPT
# ==================================================

@strawberry.type
class Concept:
    id: strawberry.ID
    company_id: strawberry.ID
    concept_type: ConceptType
    name: str
    short_description: Optional[str]
    long_description: Optional[str]
    is_active: bool
    created_at: Time
    updated_at: Time


def concept_from_row(row):
    return Concept(**{**row, "concept_type": ConceptType(row["concept_type"])})


@strawberry.input
class CreateConceptInput:
    company_id: strawberry.ID
    concept_type: ConceptType
    name: str
    short_description: Optional[str] = None
    long_description: Optional[str] = None


# ==================================================
# DÍA 1: ACCOUNT_CONCEPT (relación N:M)
# ==================================================

@strawberry.type
class AccountConcept:
    id: strawberry.ID
    account_id: strawberry.ID
    concept_id: strawberry.ID
    is_active: bool
    created_at: Time

    @strawberry.field
    def account(self) -> Account:
        return account_from_row(account_repository.obtener_cuenta(self.account_id))

    @strawberry.field
    def concept(self) -> Concept:
        return concept_from_row(concept_repository.obtener_concepto(self.concept_id))


@strawberry.input
class AssignConceptToAccountInput:
    account_id: strawberry.ID
    concept_id: strawberry.ID


# ==================================================
# DÍA 2: TRANSACTION
# ==================================================

@strawberry.type
class Transaction:
    id: strawberry.ID
    account_id: strawberry.ID
    concept_id: strawberry.ID
    transaction_type: TransactionType
    amount: Decimal
    transaction_date: Time
    captured_at: Time
    captured_by: strawberry.ID
    short_description: Optional[str]
    long_description: Optional[str]
    is_active: bool
    created_at: Time
    updated_at: Time

    @strawberry.field
    def account(self) -> Account:
        return account_from_row(account_repository.obtener_cuenta(self.account_id))

    @strawberry.field
    def concept(self) -> Concept:
        return concept_from_row(concept_repository.obtener_concepto(self.concept_id))

    @strawberry.field
    def captured_by_user(self) -> User:
        return User(**user_repository.obtener_usuario(self.captured_by))


TRANSACTION_FIELDS = (
    "id", "account_id", "concept_id", "transaction_type", "amount", "transaction_date",
    "captured_at", "captured_by", "short_description", "long_description", "is_active",
    "created_at", "updated_at",
)


def transaction_from_row(row):
    datos = {campo: row[campo] for campo in TRANSACTION_FIELDS}
    datos["transaction_type"] = TransactionType(row["transaction_type"])
    return Transaction(**datos)


@strawberry.input
class CreateTransactionInput:
    account_id: strawberry.ID
    concept_id: strawberry.ID
    transaction_type: TransactionType
    amount: Decimal
    transaction_date: Optional[Time] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None


# Balance = SUM(INCOME) - SUM(EXPENSE) de los movimientos activos de una cuenta
@strawberry.type
class AccountBalance:
    account_id: strawberry.ID
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    transaction_count: int

    @strawberry.field
    def account(self) -> Account:
        return account_from_row(account_repository.obtener_cuenta(self.account_id))
