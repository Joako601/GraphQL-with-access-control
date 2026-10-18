from typing import Optional
from enum import Enum

import strawberry

from models.types import CompanyUser
from repositories import role_repository, user_repository


@strawberry.enum
class PermissionResource(Enum):
    COMPANY_USERS = "COMPANY_USERS"
    ACCOUNTS = "ACCOUNTS"
    CONCEPTS = "CONCEPTS"
    TRANSACTIONS = "TRANSACTIONS"
    ROLES = "ROLES"


@strawberry.input
class SetRolePermissionsInput:
    role_id: strawberry.ID
    permission_ids: list[strawberry.ID]


@strawberry.type
class Role:
    id: strawberry.ID
    code: str
    name: str
    description: Optional[str]
    is_active: bool


@strawberry.input
class CreateRoleInput:
    code: str
    name: str
    description: Optional[str] = None


@strawberry.type
class Permission:
    id: strawberry.ID
    code: str
    name: str
    description: Optional[str]
    is_active: bool


@strawberry.input
class CreatePermissionInput:
    code: str
    name: str
    description: Optional[str] = None


@strawberry.type
class RolePermission:
    id: strawberry.ID
    role_id: strawberry.Private[int]
    permission_id: strawberry.Private[int]
    is_active: bool

    @strawberry.field
    def role(self) -> Role:
        return Role(**role_repository.obtener_rol(self.role_id))

    @strawberry.field
    def permission(self) -> Permission:
        return Permission(**role_repository.obtener_permiso(self.permission_id))


@strawberry.input
class AssignPermissionToRoleInput:
    role_id: strawberry.ID
    permission_id: strawberry.ID


@strawberry.type
class CompanyUserRole:
    id: strawberry.ID
    company_user_id: strawberry.Private[int]
    role_id: strawberry.Private[int]
    is_active: bool

    @strawberry.field
    def company_user(self) -> CompanyUser:
        return CompanyUser(**user_repository.obtener_company_user(self.company_user_id))

    @strawberry.field
    def role(self) -> Role:
        return Role(**role_repository.obtener_rol(self.role_id))


@strawberry.input
class AssignRoleInput:
    company_user_id: strawberry.ID
    role_id: strawberry.ID


@strawberry.type
class RolePermissionPlan:
    role: Role
    current: list[Permission]
    to_activate: list[Permission]
    to_deactivate: list[Permission]
    unchanged: list[Permission]
    final_count: int


@strawberry.type
class RolePermissionUpdate:
    role: Role
    activated: list[Permission]
    deactivated: list[Permission]
    unchanged: list[Permission]
    final_count: int
    changed: bool
