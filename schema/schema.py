from typing import List, Optional

import strawberry
from strawberry.tools import merge_types

from models.types import (
    AuthPayload,
    AuthUser,
    Company,
    CompanyUser,
    CreateCompanyAdminInput,
    CreateCompanyInput,
    CreateCompanyUserInput,
    Decimal,
    LoginInput,
    UpdateCompanyInput,
)
from repositories import company_repository
from schema.finance_schema import FinanceMutation, FinanceQuery
from schema.role_schema import RoleMutation, RoleQuery
from services import company_service, user_service
from services.auth import usuario_actual
from services.validators import parse_id


# ==================================================
# QUERIES
# ==================================================

@strawberry.type
class Query:

    @strawberry.field
    def companies(self, active_only: Optional[bool] = None) -> List[Company]:
        return [Company(**row) for row in company_service.listar_empresas(active_only)]

    @strawberry.field
    def company(self, id: strawberry.ID) -> Optional[Company]:
        row = company_repository.obtener_empresa(parse_id(id))
        return Company(**row) if row else None

    @strawberry.field
    def company_users(
        self, info: strawberry.Info, actor_company_user_id: strawberry.ID, company_id: strawberry.ID
    ) -> List[CompanyUser]:
        rows = user_service.listar_usuarios(company_id, actor_company_user_id, usuario_actual(info))
        return [CompanyUser(**row) for row in rows]


# ==================================================
# MUTATIONS
# ==================================================

@strawberry.type
class Mutation:

    # ---------- Día 1: empresas ----------

    @strawberry.mutation
    def create_company(self, input: CreateCompanyInput) -> Company:
        return Company(**company_service.crear_empresa(input))

    @strawberry.mutation
    def update_company(self, input: UpdateCompanyInput) -> Company:
        return Company(**company_service.actualizar_empresa(input))

    @strawberry.mutation
    def deactivate_company(self, id: strawberry.ID) -> Company:
        return Company(**company_service.desactivar_empresa(id))

    # ---------- Día 2: usuarios ----------

    @strawberry.mutation
    def login(self, input: LoginInput) -> AuthPayload:
        result = user_service.login(input)
        user = result["user"]
        return AuthPayload(
            token=result["token"],
            token_type=result["token_type"],
            user=AuthUser(id=user["id"], name=user["name"], email=user["email"]),
        )

    @strawberry.mutation
    def create_company_admin(self, input: CreateCompanyAdminInput) -> CompanyUser:
        return CompanyUser(**user_service.crear_admin(input))

    @strawberry.mutation
    def create_company_user(
        self, info: strawberry.Info, actor_company_user_id: strawberry.ID, input: CreateCompanyUserInput
    ) -> CompanyUser:
        return CompanyUser(**user_service.crear_usuario(input, actor_company_user_id, usuario_actual(info)))

    @strawberry.mutation
    def deactivate_company_user(
        self, info: strawberry.Info, actor_company_user_id: strawberry.ID, id: strawberry.ID
    ) -> CompanyUser:
        return CompanyUser(**user_service.desactivar_usuario(id, actor_company_user_id, usuario_actual(info)))


schema = strawberry.Schema(
    query=merge_types("Query", (Query, FinanceQuery, RoleQuery)),
    mutation=merge_types("Mutation", (Mutation, FinanceMutation, RoleMutation)),
    types=[Decimal],
)
