from datetime import date
from typing import List, Optional

import strawberry

from models.balance_types import AccountBalance, GeneralBalance, general_balance_from_dict
from models.finance_types import (
    Account,
    AccountConcept,
    AccountType,
    AssignConceptToAccountInput,
    Concept,
    ConceptType,
    CreateAccountInput,
    CreateConceptInput,
    CreateTransactionInput,
    Transaction,
    TransactionType,
    account_from_row,
    concept_from_row,
    transaction_from_row,
)
from services import (
    account_concept_service,
    account_service,
    balance_service,
    concept_service,
    transaction_service,
)
from services.auth import leer_actor


# ==================================================
# QUERIES
# ==================================================

@strawberry.type
class FinanceQuery:

    # ---------- Día 1: cuentas y conceptos ----------

    @strawberry.field
    def accounts(
        self,
        info: strawberry.Info,
        company_id: strawberry.ID,
        account_type: Optional[AccountType] = None,
        active_only: Optional[bool] = None,
    ) -> List[Account]:
        rows = account_service.listar_cuentas(
            company_id, account_type, active_only, leer_actor(info)
        )
        return [account_from_row(row) for row in rows]

    @strawberry.field
    def concepts(
        self,
        info: strawberry.Info,
        company_id: strawberry.ID,
        concept_type: Optional[ConceptType] = None,
        active_only: Optional[bool] = None,
    ) -> List[Concept]:
        rows = concept_service.listar_conceptos(
            company_id, concept_type, active_only, leer_actor(info)
        )
        return [concept_from_row(row) for row in rows]

    @strawberry.field
    def account_concepts(
        self,
        info: strawberry.Info,
        account_id: strawberry.ID,
        active_only: Optional[bool] = True,
    ) -> List[AccountConcept]:
        rows = account_concept_service.listar_conceptos_de_cuenta(
            account_id, active_only, leer_actor(info)
        )
        return [AccountConcept(**row) for row in rows]

    # ---------- Día 2: movimientos ----------

    @strawberry.field
    def transactions(
        self,
        info: strawberry.Info,
        account_id: Optional[strawberry.ID] = None,
        transaction_type: Optional[TransactionType] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Transaction]:
        rows = transaction_service.listar_movimientos(
            account_id, transaction_type, limit, offset, leer_actor(info)
        )
        return [transaction_from_row(row) for row in rows]

    # ---------- Actividad 7: balances ----------

    @strawberry.field
    def account_balance(
        self, info: strawberry.Info, account_id: strawberry.ID, from_date: date, to_date: date
    ) -> AccountBalance:
        actor = leer_actor(info)
        return AccountBalance(**balance_service.balance_de_cuenta(account_id, from_date, to_date, actor))

    @strawberry.field
    def general_balance(self, info: strawberry.Info, from_date: date, to_date: date) -> GeneralBalance:
        actor = leer_actor(info)
        return general_balance_from_dict(balance_service.balance_general(from_date, to_date, actor))


# ==================================================
# MUTATIONS
# ==================================================

@strawberry.type
class FinanceMutation:

    # ---------- Día 1: cuentas, conceptos y conceptos por cuenta ----------

    @strawberry.mutation
    def create_account(self, info: strawberry.Info, input: CreateAccountInput) -> Account:
        return account_from_row(account_service.crear_cuenta(input, leer_actor(info)))

    @strawberry.mutation
    def create_concept(self, info: strawberry.Info, input: CreateConceptInput) -> Concept:
        return concept_from_row(concept_service.crear_concepto(input, leer_actor(info)))

    @strawberry.mutation
    def assign_concept_to_account(
        self, info: strawberry.Info, input: AssignConceptToAccountInput
    ) -> AccountConcept:
        row = account_concept_service.asignar_concepto(input, leer_actor(info))
        return AccountConcept(**row)

    @strawberry.mutation
    def remove_concept_from_account(
        self,
        info: strawberry.Info,
        account_id: strawberry.ID,
        concept_id: strawberry.ID,
    ) -> bool:
        return account_concept_service.retirar_concepto(
            account_id, concept_id, leer_actor(info)
        )

    # ---------- Día 2: movimientos ----------

    @strawberry.mutation
    def create_transaction(
        self, info: strawberry.Info, input: CreateTransactionInput
    ) -> Transaction:
        row = transaction_service.crear_movimiento(input, leer_actor(info))
        return transaction_from_row(row)

    @strawberry.mutation
    def delete_transaction(self, info: strawberry.Info, id: strawberry.ID) -> Transaction:
        row = transaction_service.eliminar_movimiento(id, leer_actor(info))
        return transaction_from_row(row)
