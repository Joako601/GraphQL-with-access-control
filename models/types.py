from datetime import datetime
from decimal import Decimal as PyDecimal
from typing import TYPE_CHECKING, Annotated, NewType, Optional

import strawberry

from repositories import company_repository, role_repository, user_repository

if TYPE_CHECKING:
    from models.role_types import Role

# ==================================================
# SCALARS
# ==================================================

Time = strawberry.scalar(
    NewType("Time", datetime),
    serialize=lambda value: value.isoformat(),
    parse_value=lambda value: datetime.fromisoformat(value),
)


Decimal = strawberry.scalar(
    NewType("Decimal", PyDecimal),
    serialize=lambda value: str(value),
    parse_value=lambda value: PyDecimal(str(value)),
)


# ==================================================
# DÍA 1: COMPANY
# ==================================================

@strawberry.type
class Company:
    id: strawberry.ID
    name: str
    legal_name: Optional[str]
    tax_id: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    is_active: bool
    created_at: Time
    updated_at: Time


@strawberry.input
class CreateCompanyInput:
    name: str
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


@strawberry.input
class UpdateCompanyInput:
    id: strawberry.ID
    name: Optional[str] = None
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


# ==================================================
# DÍA 2: USER Y COMPANY_USER
# ==================================================

@strawberry.type
class User:
    id: strawberry.ID
    name: str
    email: str
    email_verified: bool
    is_active: bool
    created_at: Time
    updated_at: Time


@strawberry.type
class CompanyUser:
    id: strawberry.ID
    company_id: strawberry.ID
    user_id: strawberry.ID
    is_admin: bool
    is_active: bool
    joined_at: Time

    @strawberry.field
    def company(self) -> Company:
        return Company(**company_repository.obtener_empresa(self.company_id))

    @strawberry.field
    def user(self) -> User:
        return User(**user_repository.obtener_usuario(self.user_id))

    @strawberry.field
    def role(self) -> Optional[Annotated["Role", strawberry.lazy("models.role_types")]]:
        from models.role_types import Role

        asignacion = role_repository.obtener_rol_activo_de_membresia(self.id)
        return Role(**role_repository.obtener_rol(asignacion["role_id"])) if asignacion else None


@strawberry.input
class LoginInput:
    email: str
    password: str
    # Solo elige la membresía si la persona está en varias empresas; el token copia el companyId de esa fila.
    company_id: Optional[strawberry.ID] = None


@strawberry.type
class AuthUser:
    id: strawberry.ID
    name: str
    email: str


@strawberry.type
class AuthPayload:
    token: str
    token_type: str
    user: AuthUser


@strawberry.input
class CreateCompanyAdminInput:
    company_id: strawberry.ID
    name: str
    email: str
    password: str


@strawberry.input
class CreateCompanyUserInput:
    company_id: strawberry.ID
    name: str
    email: str
    password: str
    role_id: Optional[strawberry.ID] = None
