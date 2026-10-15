r"""Demostración real de la Unidad II, Actividad 4 (HTTP, PostgreSQL y GraphiQL).

Ejecutar desde la raíz: .venv\Scripts\python.exe pruebas/actividad4.py
Cada ejecución crea empresas y usuarios nuevos. No borra datos existentes.
Conserva las capturas, las consultas y las salidas SQL; muestra las comprobaciones
en la consola. El documento Word se entrega por separado.
"""
import argparse
import html
import json
import re
import subprocess
import time
import urllib.parse
import urllib.request
import unicodedata
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'evidencias_actividad4'
MATRIX = {
    'ADMINISTRADOR': ['company.users.read', 'company.users.write', 'accounts.read', 'accounts.write',
                      'concepts.read', 'concepts.write', 'transactions.read', 'transactions.write', 'roles.read', 'roles.write'],
    'CONTADOR': ['company.users.read', 'accounts.read', 'accounts.write', 'concepts.read', 'concepts.write',
                 'transactions.read', 'transactions.write', 'roles.read'],
    'CAPTURISTA': ['accounts.read', 'concepts.read', 'transactions.read', 'transactions.write'],
    'CONSULTA': ['company.users.read', 'accounts.read', 'concepts.read', 'transactions.read'],
}
RP = '''query PermisosDelRol($rol: ID!) {
  rolePermissions(roleId: $rol) {
    id
    isActive
    permission { code }
  }
}'''
ACCOUNT = '''mutation CrearCuenta($actor: ID!, $input: CreateAccountInput!) {
  createAccount(actorCompanyUserId: $actor, input: $input) {
    id
    name
    companyId
  }
}'''
TRANSACTION = '''mutation RegistrarMovimiento($actor: ID!, $input: CreateTransactionInput!) {
  createTransaction(actorCompanyUserId: $actor, input: $input) {
    id
    amount
    capturedByUser { name }
    account { name }
  }
}'''
ASSIGN = '''mutation AgregarPermiso($actor: ID!, $input: AssignPermissionToRoleInput!) {
  assignPermissionToRole(actorCompanyUserId: $actor, input: $input) {
    id
    isActive
    role { code }
    permission { code }
  }
}'''
REMOVE = '''mutation QuitarPermiso($actor: ID!, $rol: ID!, $permiso: ID!) {
  removePermissionFromRole(actorCompanyUserId: $actor, roleId: $rol, permissionId: $permiso)
}'''
ASSIGN_ROLE = '''mutation CambiarPuesto($actor: ID!, $input: AssignRoleInput!) {
  assignRole(actorCompanyUserId: $actor, input: $input) {
    id
    isActive
    role { code }
    companyUser { id user { name } }
  }
}'''
SELECT_MATRIX = '''SELECT r.code AS rol, p.code AS permiso, rp.is_active
FROM role_permissions rp
JOIN roles r ON r.id = rp.role_id
JOIN permissions p ON p.id = rp.permission_id
ORDER BY r.code, p.code;'''


class Demo:
    def __init__(self, api, browser):
        self.api, self.browser = api, browser
        self.steps, self.checks = [], []
        self.pending = set()
        self.suffix = datetime.now().strftime('%Y%m%d%H%M%S')
        self.password = 'Actividad4-demo-2026'
        self.people = {}
        self.phase = 'Preparación'
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / 'capturas').mkdir(exist_ok=True)

    def check(self, rule, condition, detail=None):
        self.checks.append({'regla': rule, 'correcto': bool(condition), 'detalle': detail})
        if not condition:
            raise AssertionError(rule + ': ' + str(detail))

    def cmd(self, args):
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', check=True)
        return result.stdout.strip()

    def sql(self, query, json_rows=False):
        if json_rows:
            query = 'SELECT COALESCE(json_agg(t), \'[]\'::json) FROM (' + query.rstrip(';') + ') t;'
        value = self.cmd(['docker', 'compose', 'exec', '-T', 'postgres', 'psql', '-X',
                          '-U', 'postgres', '-d', 'sistema_financiero', '-v', 'ON_ERROR_STOP=1',
                          '-tAc' if json_rows else '-c', query])
        return json.loads(value) if json_rows else value

    def http(self, query, variables=None, token=None):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        req = urllib.request.Request(self.api, json.dumps({'query': query, 'variables': variables or {}}).encode(), headers)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=30) as response:
            return json.load(response)

    def data(self, query, variables=None, token=None):
        result = self.http(query, variables, token)
        if result.get('errors'):
            raise RuntimeError(json.dumps(result, ensure_ascii=False))
        return result['data']

    def capture_graphql(self, query, variables, token, filename):
        context = self.browser.new_context(viewport={'width': 1500, 'height': 940}, device_scale_factor=1)
        page = context.new_page()
        # El JWT solo se envía al endpoint local, nunca a los CDN de GraphiQL.
        if token:
            page.route(re.compile(re.escape(self.api) + r'(?:\?.*)?$'),
                       lambda route: route.continue_(headers={**route.request.headers, 'authorization': 'Bearer ' + token}))
        params = urllib.parse.urlencode({'q': query, 'variables': json.dumps(variables, ensure_ascii=False, indent=2)},
                                        quote_via=urllib.parse.quote)
        page.goto(self.api + '?' + params, wait_until='networkidle', timeout=60000)
        button = page.locator('.graphiql-execute-button')
        button.wait_for(timeout=45000)
        with page.expect_response(lambda r: r.request.method == 'POST' and r.url == self.api, timeout=30000) as response:
            button.click()
        payload = response.value.json()
        page.wait_for_timeout(450)
        # GraphiQL 3 usa CodeMirror; se amplía el lienzo para conservar toda la respuesta.
        lines = max(len(json.dumps(payload, indent=2, ensure_ascii=False).splitlines()),
                    len(query.splitlines()) + len(json.dumps(variables, indent=2).splitlines()) + 10)
        page.set_viewport_size({'width': 1500, 'height': min(4400, max(940, lines * 23 + 210))})
        page.wait_for_timeout(350)
        page.screenshot(path=str(OUT / 'capturas' / filename), full_page=True)
        context.close()
        return payload

    def step(self, key, title, rule, query, variables=None, actor=None, error=None, inspect=None):
        variables = variables or {}
        token = self.people[actor]['token'] if actor else None
        key = re.sub(r'[^a-z0-9_]+', '_', unicodedata.normalize('NFKD', key).encode('ascii', 'ignore').decode().lower()).strip('_')
        filename = f'{len(self.steps)+1:02d}_{key}.png'
        payload = self.capture_graphql(query, variables, token, filename)
        messages = [e['message'] for e in payload.get('errors', [])]
        correct = any(error in m for m in messages) if error else not messages and payload.get('data') is not None
        if correct and inspect:
            correct = bool(inspect(payload['data']))
        if correct and query == ASSIGN and actor == 'Ana':
            self.pending.add((variables['input']['roleId'], variables['input']['permissionId']))
        if correct and query == REMOVE and actor == 'Ana':
            self.pending.discard((variables['rol'], variables['permiso']))
        self.steps.append({'clave': key, 'parte': self.phase, 'titulo': title, 'regla': rule,
                           'actor': actor, 'query': query, 'variables': variables, 'respuesta': payload,
                           'error_esperado': error, 'captura': 'capturas/' + filename, 'correcto': correct})
        self.check(title, correct, messages or None)
        print(f'OK {len(self.steps):02d}: {title}', flush=True)
        return payload.get('data')

    def sql_step(self, key, title, rule, query, condition):
        rows = self.sql(query, True)
        self.check(title, condition(rows), rows)
        text = self.sql(query)
        key = re.sub(r'[^a-z0-9_]+', '_', unicodedata.normalize('NFKD', key).encode('ascii', 'ignore').decode().lower()).strip('_')
        filename = f'{len(self.steps)+1:02d}_{key}.png'
        doc = '''<!doctype html><meta charset="utf-8"><style>
body{font:17px system-ui;margin:38px;background:#f4f6fa;color:#17243a}h1{font-size:28px}
pre{background:white;border:1px solid #cbd5e1;border-radius:10px;padding:22px;white-space:pre-wrap;font:16px Consolas,monospace;line-height:1.5}
p{line-height:1.5}small{color:#475569}</style>'''
        doc += f'<small>Unidad II · Actividad 4 · Salida real de PostgreSQL / psql</small><h1>{html.escape(title)}</h1>'
        doc += f'<p>{html.escape(rule)}</p><pre>{html.escape(query)}</pre><pre>{html.escape(text)}</pre>'
        doc += '<p>Transcripción de la salida del comando docker compose exec -T postgres psql. No es una captura de una terminal.</p>'
        context = self.browser.new_context(viewport={'width': 1400, 'height': 800})
        page = context.new_page()
        page.set_content(doc)
        page.screenshot(path=str(OUT / 'capturas' / filename), full_page=True)
        context.close()
        self.steps.append({'clave': key, 'parte': self.phase, 'titulo': title, 'regla': rule, 'sql': query,
                           'filas': rows, 'salida_psql': text, 'captura': 'capturas/' + filename, 'correcto': True})
        print(f'OK {len(self.steps):02d}: {title}', flush=True)
        return rows

    def login(self, email):
        return self.data('mutation($i: LoginInput!) { login(input:$i) { token } }',
                         {'i': {'email': email, 'password': self.password}})['login']['token']

    def setup(self):
        self.company = self.data('mutation($i:CreateCompanyInput!){createCompany(input:$i){id}}',
                                 {'i': {'name': 'Ingresos Actividad 4 ' + self.suffix}})['createCompany']['id']
        email = f'ana.{self.suffix}@actividad4.local'
        ana = self.data('''mutation($i:CreateCompanyAdminInput!) {
          createCompanyAdmin(input:$i) { id isAdmin role { code } user { name } }
        }''', {'i': {'companyId': self.company, 'name': 'Ana', 'email': email, 'password': self.password}})['createCompanyAdmin']
        self.people['Ana'] = {'id': ana['id'], 'email': email, 'rol_inicial': 'ADMINISTRADOR', 'token': self.login(email)}
        self.check('Ana nace con isAdmin=true y ADMINISTRADOR', ana['isAdmin'] and ana['role']['code']=='ADMINISTRADOR')
        self.roles = {r['code']: r['id'] for r in self.data('{ roles { id code } }')['roles']}
        self.permissions = {p['code']: p['id'] for p in self.data('{ permissions { id code } }')['permissions']}
        # Cada persona nueva nace como CONSULTA; Ana asigna después su puesto con assignRole.
        for name, role in [('Luis','CONTADOR'), ('María','CAPTURISTA'), ('José','CAPTURISTA'), ('Pedro','CONSULTA')]:
            key = {'María':'maria', 'José':'jose'}.get(name, name.lower())
            email = f'{key}.{self.suffix}@actividad4.local'
            person = self.data('''mutation($a:ID!,$i:CreateCompanyUserInput!) {
              createCompanyUser(actorCompanyUserId:$a,input:$i){id role{code}}
            }''', {'a': ana['id'], 'i': {'companyId': self.company, 'name': name, 'email': email,
                                       'password': self.password}}, self.people['Ana']['token'])['createCompanyUser']
            self.people[name] = {'id': person['id'], 'email': email, 'rol_inicial': role, 'token': self.login(email)}
            if role != 'CONSULTA':
                self.data(ASSIGN_ROLE, {'actor':ana['id'], 'input':{'companyUserId':person['id'], 'roleId':self.roles[role]}},
                          self.people['Ana']['token'])
        self.step('personas', 'Una empresa y los cinco puestos iniciales',
                  'Ana administra; Luis es contador; María y José son capturistas; Pedro comienza como consulta.',
                  '''query Personas($actor:ID!,$empresa:ID!){
  companyUsers(actorCompanyUserId:$actor,companyId:$empresa){
    id
    isAdmin
    user { name }
    role { code }
  }
}''', {'actor':ana['id'],'empresa':self.company}, 'Ana',
                  inspect=lambda d:len(d['companyUsers'])==5 and sum(x['isAdmin'] for x in d['companyUsers'])==1)
        self.account = self.data(ACCOUNT, self.account_vars('Ana', 'Cuenta operativa'), self.people['Ana']['token'])['createAccount']['id']
        self.concept = self.data('''mutation($a:ID!,$i:CreateConceptInput!){
          createConcept(actorCompanyUserId:$a,input:$i){id}}''',
          {'a':ana['id'],'i':{'companyId':self.company,'name':'Venta de mostrador','conceptType':'INCOME'}},
          self.people['Ana']['token'])['createConcept']['id']
        self.data('''mutation($a:ID!,$i:AssignConceptToAccountInput!){
          assignConceptToAccount(actorCompanyUserId:$a,input:$i){id}}''',
          {'a':ana['id'],'i':{'accountId':self.account,'conceptId':self.concept}},self.people['Ana']['token'])

    def account_vars(self, name, account_name):
        return {'actor':self.people[name]['id'], 'input':{'companyId':self.company, 'accountType':'CASH','name':account_name}}

    def count(self, table):
        assert table in ('accounts','transactions')
        return self.sql(f'SELECT COUNT(*) AS total FROM {table} WHERE company_id={int(self.company)}',True)[0]['total']

    def account_step(self, name, stage, accepted):
        before = self.count('accounts')
        title = f'{name}: createAccount ' + ('aceptado' if accepted else 'rechazado') + ' ' + stage
        self.step(f'cuenta_{name}_{stage}', title,
                  'El servidor consulta accounts.write del rol antes de insertar la cuenta.', ACCOUNT,
                  self.account_vars(name, f'Caja de {name} {stage}'), name,
                  error=None if accepted else 'no tiene el permiso accounts.write')
        after = self.count('accounts')
        self.check(title+' / filas SQL', after==before+int(accepted), {'antes':before,'despues':after})
        self.steps[-1]['verificacion_sql']={'tabla':'accounts','antes':before,'despues':after}

    def permission_vars(self, role, permission):
        return {'actor':self.people['Ana']['id'], 'input':{'roleId':self.roles[role], 'permissionId':self.permissions[permission]}}

    def matrix(self):
        result={}
        for role, rid in self.roles.items():
            result[role]=sorted(x['permission']['code'] for x in self.data(RP,{'rol':rid})['rolePermissions'])
        return result

    def run(self):
        self.setup()
        self.phase='Parte 1. Configuración inicial'
        self.step('roles','Los cuatro roles del catálogo','El catálogo conserva los cuatro puestos de la actividad 3.',
                  '{ roles { id code isActive } }',inspect=lambda d:set(r['code'] for r in d['roles'])==set(MATRIX) and all(r['isActive'] for r in d['roles']))
        self.step('permisos','Los diez permisos del catálogo','Ver y escribir son permisos separados.',
                  '{ permissions { id code isActive } }',inspect=lambda d:set(p['code'] for p in d['permissions'])==set(MATRIX['ADMINISTRADOR']) and all(p['isActive'] for p in d['permissions']))
        for role in MATRIX:
            self.step('inicial_'+role, 'Lista inicial de '+role,
                      'La lista activa coincide exactamente con la tabla del PDF.', RP, {'rol':self.roles[role]},
                      inspect=lambda d, role=role:sorted(x['permission']['code'] for x in d['rolePermissions'])==sorted(MATRIX[role]))
        initial=self.matrix()
        memberships=self.sql(f'SELECT * FROM company_user_roles WHERE company_user_id IN ({int(self.people["María"]["id"])},{int(self.people["José"]["id"])}) ORDER BY id',True)

        self.phase='Parte 2. Un permiso, dos personas'
        for name in ['María','José']: self.account_step(name,'antes',False)
        assigned=self.step('agregar_capturista','Ana agrega accounts.write a CAPTURISTA',
                            'Un cambio en el rol alcanza a los dos capturistas, sin editar sus membresías.',
                            ASSIGN,self.permission_vars('CAPTURISTA','accounts.write'),'Ana')['assignPermissionToRole']
        self.check('La pareja nueva está activa',assigned['isActive'])
        self.step('duplicado','La misma pareja activa no se duplica','assignPermissionToRole rechaza una pareja que ya está activa.',
                  ASSIGN,self.permission_vars('CAPTURISTA','accounts.write'),'Ana',error='ya tiene el permiso')
        for name in ['María','José']: self.account_step(name,'con permiso',True)
        self.check('María y José no se editaron',memberships==self.sql(f'SELECT * FROM company_user_roles WHERE company_user_id IN ({int(self.people["María"]["id"])},{int(self.people["José"]["id"])}) ORDER BY id',True))
        self.step('quitar_capturista','Ana quita accounts.write a CAPTURISTA',
                  'Quitar el permiso desactiva la pareja y conserva la fila.',REMOVE,
                  {'actor':self.people['Ana']['id'],'rol':self.roles['CAPTURISTA'],'permiso':self.permissions['accounts.write']},'Ana',
                  inspect=lambda d:d['removePermissionFromRole'] is True)
        pair_query=f'''SELECT rp.id, r.code AS rol, p.code AS permiso, rp.is_active FROM role_permissions rp
JOIN roles r ON r.id=rp.role_id JOIN permissions p ON p.id=rp.permission_id
WHERE r.code='CAPTURISTA' AND p.code='accounts.write';'''
        self.sql_step('pareja_inactiva','La misma pareja sigue guardada e inactiva',
                      'La fila conserva el id que devolvió la asignación; no se borró.',pair_query,
                      lambda rows:len(rows)==1 and str(rows[0]['id'])==assigned['id'] and not rows[0]['is_active'])
        for name in ['María','José']: self.account_step(name,'sin permiso',False)

        self.phase='Parte 3. Cambiar el puesto de Pedro'
        variables={'actor':self.people['Pedro']['id'],'input':{'accountId':self.account,'conceptId':self.concept,
                   'transactionType':'INCOME','amount':'1500.00','shortDescription':'Movimiento de Pedro'}}
        before=self.count('transactions')
        self.step('pedro_antes','Pedro no registra movimientos como CONSULTA',
                  'Sin transactions.write se rechaza la petición antes del INSERT.',TRANSACTION,variables,'Pedro',
                  error='no tiene el permiso transactions.write')
        after=self.count('transactions')
        self.check('El rechazo de Pedro no guarda movimientos',before==after,{'antes':before,'despues':after})
        self.steps[-1]['verificacion_sql']={'tabla':'transactions','antes':before,'despues':after}
        self.step('cambiar_pedro','Ana cambia a Pedro de CONSULTA a CAPTURISTA',
                  'assignRole cambia el puesto de una persona sin editar los permisos del rol anterior.',ASSIGN_ROLE,
                  {'actor':self.people['Ana']['id'],'input':{'companyUserId':self.people['Pedro']['id'],'roleId':self.roles['CAPTURISTA']}},'Ana')
        self.step('pedro_despues','Pedro registra el movimiento como CAPTURISTA',
                  'Se usa el mismo JWT: el servidor lee el rol actual desde la base.',TRANSACTION,variables,'Pedro')
        self.check('El movimiento autorizado sí se guardó',self.count('transactions')==before+1)
        self.sql_step('historial_pedro','Pedro tiene un solo rol activo y conserva su historial',
                      'CONSULTA queda inactivo y CAPTURISTA queda activo.',
                      f'''SELECT cur.id, r.code AS rol, cur.is_active FROM company_user_roles cur
JOIN roles r ON r.id=cur.role_id WHERE cur.company_user_id={int(self.people['Pedro']['id'])} ORDER BY cur.id;''',
                      lambda rows:len(rows)==2 and sum(r['is_active'] for r in rows)==1
                      and any(r['rol']=='CONSULTA' and not r['is_active'] for r in rows)
                      and any(r['rol']=='CAPTURISTA' and r['is_active'] for r in rows))
        for role in ['CONTADOR','CONSULTA']:
            self.step('sin_cambios_'+role,'La lista de '+role+' sigue igual',
                      'Cambiar el puesto de Pedro no cambia las listas de los demás roles.',RP,{'rol':self.roles[role]},
                      inspect=lambda d,role=role:sorted(x['permission']['code'] for x in d['rolePermissions'])==initial[role])
        self.account_step('Luis','tras cambio de Pedro',True)

        self.phase='Parte 4. Quién puede cambiar la lista'
        snapshot=self.sql('SELECT * FROM role_permissions ORDER BY id',True)
        variables=self.permission_vars('CONSULTA','concepts.write')
        variables['actor']=self.people['José']['id']
        self.step('jose_no_configura','José no puede dar concepts.write a CONSULTA',
                  'Solo quien tiene roles.write puede cambiar la lista de permisos.',ASSIGN,variables,'José',
                  error='no tiene el permiso roles.write')
        self.check('El rechazo de José no altera ninguna pareja',snapshot==self.sql('SELECT * FROM role_permissions ORDER BY id',True))
        self.sql_step('consulta_tras_rechazo','CONSULTA sigue sin permisos de escritura tras el intento de José',
                      'La petición rechazada no modifica la lista activa en PostgreSQL.',
                      '''SELECT p.code AS permiso FROM role_permissions rp JOIN roles r ON r.id=rp.role_id
JOIN permissions p ON p.id=rp.permission_id WHERE r.code='CONSULTA' AND rp.is_active ORDER BY p.code;''',
                      lambda rows:sorted(r['permiso'] for r in rows)==initial['CONSULTA'])
        self.step('ana_si_configura','Ana sí agrega concepts.write a CONSULTA',
                  'La misma acción tiene éxito con ADMINISTRADOR porque posee roles.write.',ASSIGN,
                  self.permission_vars('CONSULTA','concepts.write'),'Ana',inspect=lambda d:d['assignPermissionToRole']['isActive'])
        self.step('ana_restaura','Ana vuelve a quitar concepts.write de CONSULTA',
                  'La configuración final vuelve a la matriz original; se conserva la pareja inactiva.',REMOVE,
                  {'actor':self.people['Ana']['id'],'rol':self.roles['CONSULTA'],'permiso':self.permissions['concepts.write']},'Ana',
                  inspect=lambda d:d['removePermissionFromRole'] is True)
        self.check('La matriz final coincide con las cuatro listas iniciales',self.matrix()==initial)

        self.phase='Aislamiento entre empresas'
        other=self.data('mutation($i:CreateCompanyInput!){createCompany(input:$i){id}}',
                        {'i':{'name':'Empresa B Actividad 4 '+self.suffix}})['createCompany']['id']
        # Tiene permisos de escritura, pero su membresía sigue perteneciendo a la empresa A.
        before_other=self.sql(f'SELECT COUNT(*) AS total FROM accounts WHERE company_id={int(other)}',True)
        foreign=self.account_vars('Luis','Cuenta ajena'); foreign['input']['companyId']=other
        self.step('empresa_ajena','Luis no puede crear una cuenta en otra empresa',
                  'Tener accounts.write no permite escribir fuera de la empresa de la membresía.',ACCOUNT,foreign,'Luis',
                  error='no pertenece a esta empresa')
        self.check('La empresa B no recibe la cuenta',before_other==self.sql(f'SELECT COUNT(*) AS total FROM accounts WHERE company_id={int(other)}',True))
        self.step('actor_ajeno','José no puede usar la membresía de Ana',
                  'actorCompanyUserId debe pertenecer al usuario autenticado; escribir otro id no concede permisos.',
                  ACCOUNT,self.account_vars('Ana','Suplantación rechazada'),'José',error='no pertenece al usuario autenticado')
        self.step('lectura_ajena','María no puede leer las cuentas de otra empresa',
                  'accounts.read también se limita a la empresa de la membresía.',
                  '''query($actor:ID!,$empresa:ID!){accounts(actorCompanyUserId:$actor,companyId:$empresa){id name}}''',
                  {'actor':self.people['María']['id'],'empresa':other},'María',error='no pertenece a esta empresa')

        self.phase='Cierre y reinicio'
        rows=self.sql_step('matriz_final','SELECT final: 26 parejas activas y 2 inactivas',
                      'Las listas activas coinciden con el PDF: 10, 8, 4 y 4. Las dos parejas retiradas conservan su historial.',
                      SELECT_MATRIX,lambda rows:len(rows)==28 and sum(r['is_active'] for r in rows)==26
                      and {role:sorted(r['permiso'] for r in rows if r['rol']==role and r['is_active']) for role in MATRIX}==initial)
        (OUT/'role_permissions_final.sql').write_text(SELECT_MATRIX+'\n',encoding='utf-8')
        (OUT/'role_permissions_final.txt').write_text(self.sql(SELECT_MATRIX)+'\n',encoding='utf-8')
        (OUT/'role_permissions_final.csv').write_text(self.cmd(['docker','compose','exec','-T','postgres','psql','-X',
            '-U','postgres','-d','sistema_financiero','--csv','-c',SELECT_MATRIX])+'\n',encoding='utf-8')
        counts='''SELECT (SELECT COUNT(*) FROM roles) AS roles,
(SELECT COUNT(*) FROM permissions) AS permisos,
(SELECT COUNT(*) FROM role_permissions) AS parejas,
(SELECT COUNT(*) FROM role_permissions WHERE is_active) AS parejas_activas;'''
        before=self.sql(counts,True)
        catalog_before=self.sql('SELECT id, code FROM roles ORDER BY id',True)
        permissions_before=self.sql('SELECT id, code FROM permissions ORDER BY id',True)
        memberships_before=self.sql('SELECT * FROM company_user_roles ORDER BY id',True)
        self.cmd(['docker','compose','restart','api'])
        for _ in range(45):
            try:
                if self.http('{ roles { id } }').get('data'):break
            except Exception:pass
            time.sleep(1)
        else:raise RuntimeError('El servidor no volvió después del reinicio')
        after=self.sql_step('reinicio','Reinicio real: 4 roles, 10 permisos, 28 parejas',
                            'El seed no duplica catálogos, no reactiva las parejas retiradas y conserva las asignaciones.',
                            counts,lambda rows:rows==before and rows==[{'roles':4,'permisos':10,'parejas':28,'parejas_activas':26}])
        self.check('Se conservan los ids de los roles tras reiniciar',catalog_before==self.sql('SELECT id, code FROM roles ORDER BY id',True))
        self.check('Se conservan los ids de los permisos tras reiniciar',permissions_before==self.sql('SELECT id, code FROM permissions ORDER BY id',True))
        self.check('Se conservan las membresías y su historial tras reiniciar',memberships_before==self.sql('SELECT * FROM company_user_roles ORDER BY id',True))
        self.check('Matriz original conservada tras reiniciar',self.matrix()==initial)
        self.check('Las parejas inactivas se conservan tras reiniciar',rows==self.sql(SELECT_MATRIX,True))
        for name in ['María','José']: self.account_step(name,'tras reinicio',False)
        self.report()
        print(f'COMPLETADO: {len(self.steps)} capturas, {len(self.checks)} comprobaciones correctas.',flush=True)

    def report(self):
        operations=[]
        for step in self.steps:
            if 'query' in step:
                operations.append('# '+step['titulo']+'\n# Actor: '+str(step.get('actor') or 'catálogo público')+
                                  '\n# Variables: '+json.dumps(step['variables'],ensure_ascii=False)+'\n'+step['query'])
        (ROOT/'consultas.graphql').write_text('\n\n'.join(operations)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default='http://127.0.0.1:8004/graphql')
    parser.add_argument('--browser',default='chrome',choices=['chrome','msedge','chromium'])
    args=parser.parse_args()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.launch(channel=None if args.browser=='chromium' else args.browser,headless=True)
        demo=Demo(args.url,browser)
        try:
            demo.run()
        except Exception:
            # Si la red o una comprobación interrumpe la demostración, retirar solo
            # los permisos temporales concedidos por esta ejecución.
            for role, permission in list(demo.pending):
                demo.data(REMOVE, {'actor':demo.people['Ana']['id'], 'rol':role, 'permiso':permission},
                          demo.people['Ana']['token'])
            raise
        finally:
            browser.close()


if __name__=='__main__':main()
