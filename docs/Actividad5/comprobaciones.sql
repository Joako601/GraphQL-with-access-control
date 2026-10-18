-- Este proyecto usa PostgreSQL (ver docker-compose.yml), no MySQL.
-- Estado inicial/final: ejecutar y conservar la salida completa.
SELECT r.code AS rol, p.code AS permiso, rp.id AS relacion_id,
       rp.is_active AS relacion_activa, p.is_active AS permiso_activo
FROM role_permissions rp
JOIN roles r ON r.id = rp.role_id
JOIN permissions p ON p.id = rp.permission_id
ORDER BY r.code, p.code;

-- Debe devolver cero filas.
SELECT role_id, permission_id, COUNT(*) AS repeticiones
FROM role_permissions
GROUP BY role_id, permission_id
HAVING COUNT(*) > 1;

-- Inventario por códigos, sin depender de IDs que varían entre instalaciones.
SELECT code, is_active FROM roles ORDER BY code;
SELECT code, is_active FROM permissions ORDER BY code;

-- E06 preparación temporal. Ejecutar una variante por vez y restaurar inmediatamente.
-- Rol inactivo: UPDATE roles SET is_active = FALSE WHERE code = 'CAPTURISTA';
-- Restauración: UPDATE roles SET is_active = TRUE WHERE code = 'CAPTURISTA';
-- Permiso inactivo: UPDATE permissions SET is_active = FALSE WHERE code = 'accounts.write';
-- Restauración: UPDATE permissions SET is_active = TRUE WHERE code = 'accounts.write';
-- Usar BEGIN/ROLLBACK si se realiza una prueba aislada; no dejar el catálogo alterado.

-- Obtener IDs reales del entorno para preparar JSON/GraphiQL.
SELECT cu.id AS actor_id, u.email
FROM company_users cu JOIN users u ON u.id = cu.user_id
ORDER BY cu.id;
SELECT id, code FROM roles ORDER BY code;
SELECT id, code FROM permissions ORDER BY code;
