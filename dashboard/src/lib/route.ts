// Navegación por hash (#/admin/usuarios): una sola aplicación, sin servidor de rutas ni dependencia nueva.
// Recargar la página conserva la sección.

export type AdminModule = 'usuarios' | 'cuentas' | 'conceptos' | 'roles'
export type Route = { section: 'financiero' } | { section: 'admin'; module: AdminModule }

export const ADMIN_MODULES: readonly AdminModule[] = ['usuarios', 'cuentas', 'conceptos', 'roles']

export function parseRoute(hash: string): Route {
  const [section, module] = hash.replace(/^#\/?/, '').split('/')
  if (section === 'admin') {
    return { section: 'admin', module: ADMIN_MODULES.find((m) => m === module) ?? 'usuarios' }
  }
  return { section: 'financiero' }
}

export function routeHref(route: Route): string {
  return route.section === 'admin' ? `#/admin/${route.module}` : '#/financiero'
}
