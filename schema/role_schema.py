from typing import List, Optional

import strawberry

from models.role_types import (
    AssignPermissionToRoleInput,
    AssignRoleInput,
    CompanyUserRole,
    CreatePermissionInput,
    CreateRoleInput,
    Permission,
    Role,
    RolePermission,
    PermissionResource,
    SetRolePermissionsInput,
    RolePermissionPlan,
    RolePermissionUpdate,
)
from services import role_service
from services.auth import usuario_actual
from services.validators import AppError


@strawberry.type
class RoleQuery:

    @strawberry.field
    def roles(self, active_only: Optional[bool] = None) -> List[Role]:
        return [Role(**row) for row in role_service.listar_roles(active_only)]

    @strawberry.field
    def role(self, id: strawberry.ID) -> Optional[Role]:
        try:
            return Role(**role_service.obtener_rol_o_error(id))
        except AppError:
            return None

    @strawberry.field
    def permissions(self, active_only: Optional[bool] = None) -> List[Permission]:
        return [Permission(**row) for row in role_service.listar_permisos(active_only)]

    @strawberry.field
    def permission_catalog(
        self, info: strawberry.Info, actor_company_user_id: strawberry.ID,
        resource: Optional[PermissionResource] = None,
    ) -> List[Permission]:
        return [Permission(**row) for row in role_service.catalogo_permisos(
            resource, actor_company_user_id, usuario_actual(info)
        )]

    @strawberry.field
    def preview_role_permissions(
        self, info: strawberry.Info, input: SetRolePermissionsInput,
        actor_company_user_id: strawberry.ID,
    ) -> Optional[RolePermissionPlan]:
        plan = role_service.previsualizar_permisos_rol(input, actor_company_user_id, usuario_actual(info))
        return RolePermissionPlan(
            role=Role(**plan["role"]),
            current=[Permission(**row) for row in plan["current"]],
            to_activate=[Permission(**row) for row in plan["to_activate"]],
            to_deactivate=[Permission(**row) for row in plan["to_deactivate"]],
            unchanged=[Permission(**row) for row in plan["unchanged"]],
            final_count=plan["final_count"],
        )

    @strawberry.field
    def role_permissions(self, role_id: strawberry.ID) -> List[RolePermission]:
        return [RolePermission(**row) for row in role_service.listar_permisos_de_rol(role_id)]


@strawberry.type
class RoleMutation:

    @strawberry.mutation
    def set_role_permissions(
        self, info: strawberry.Info, input: SetRolePermissionsInput,
        actor_company_user_id: strawberry.ID,
    ) -> Optional[RolePermissionUpdate]:
        result = role_service.establecer_permisos_rol(input, actor_company_user_id, usuario_actual(info))
        return RolePermissionUpdate(
            role=Role(**result["role"]),
            activated=[Permission(**row) for row in result["activated"]],
            deactivated=[Permission(**row) for row in result["deactivated"]],
            unchanged=[Permission(**row) for row in result["unchanged"]],
            final_count=result["final_count"],
            changed=result["changed"],
        )

    @strawberry.mutation
    def create_role(
        self, info: strawberry.Info, actor_company_user_id: strawberry.ID, input: CreateRoleInput
    ) -> Role:
        return Role(**role_service.crear_rol(input, actor_company_user_id, usuario_actual(info)))

    @strawberry.mutation
    def deactivate_role(
        self, info: strawberry.Info, actor_company_user_id: strawberry.ID, id: strawberry.ID
    ) -> Role:
        return Role(**role_service.desactivar_rol(id, actor_company_user_id, usuario_actual(info)))

    @strawberry.mutation
    def create_permission(
        self, info: strawberry.Info, actor_company_user_id: strawberry.ID, input: CreatePermissionInput
    ) -> Permission:
        return Permission(**role_service.crear_permiso(input, actor_company_user_id, usuario_actual(info)))

    @strawberry.mutation
    def assign_permission_to_role(
        self, info: strawberry.Info, actor_company_user_id: strawberry.ID, input: AssignPermissionToRoleInput
    ) -> RolePermission:
        row = role_service.asignar_permiso_a_rol(input, actor_company_user_id, usuario_actual(info))
        return RolePermission(**row)

    @strawberry.mutation
    def remove_permission_from_role(
        self,
        info: strawberry.Info,
        actor_company_user_id: strawberry.ID,
        role_id: strawberry.ID,
        permission_id: strawberry.ID,
    ) -> bool:
        return role_service.quitar_permiso_de_rol(
            role_id, permission_id, actor_company_user_id, usuario_actual(info)
        )

    @strawberry.mutation
    def assign_role(
        self, info: strawberry.Info, actor_company_user_id: strawberry.ID, input: AssignRoleInput
    ) -> CompanyUserRole:
        return CompanyUserRole(**role_service.asignar_rol(input, actor_company_user_id, usuario_actual(info)))
