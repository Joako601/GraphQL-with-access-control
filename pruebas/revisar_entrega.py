"""Comprueba el Word y los PNG originales sin generar archivos ni usar la API.

Ejecutar desde la raíz: python pruebas/revisar_entrega.py
El documento Word debe estar junto a la carpeta del proyecto.
Esta revisión no vuelve a ejecutar las pruebas funcionales de la API.
"""
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path
from lxml import etree

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'docs/evidencias_actividad4'
DOC=ROOT.parent/'Evidencias_Unidad_II_Actividad_4_Equipo.docx'
TEAM=['Fernando Castro','Ariff Medina','Joaquin Uriona','Mateo Martin']
captures=sorted((DATA/'capturas').glob('*.png'))
assert len(captures)==35, 'Se necesitan las 35 capturas originales.'
assert [p.name.split('_',1)[0] for p in captures]==[f'{n:02d}' for n in range(1,36)], \
    'La numeración de las capturas debe ser del 01 al 35.'
expected=Counter(hashlib.sha256(p.read_bytes()).hexdigest() for p in captures)
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
with zipfile.ZipFile(DOC) as z:
    assert z.testzip() is None
    media=[n for n in z.namelist() if n.startswith('word/media/')]
    actual={n:hashlib.sha256(z.read(n)).hexdigest() for n in media}
    # Word deduplica PNG identicos; las 35 evidencias incluyen 33 imagenes unicas.
    assert set(expected)==set(actual.values()) and len(media)==len(expected)
    xml=etree.fromstring(z.read('word/document.xml'))
    relationships=etree.fromstring(z.read('word/_rels/document.xml.rels'))
    targets={item.get('Id'):item.get('Target') for item in relationships
             if item.get('TargetMode')!='External'}
    images=xml.xpath('//a:blip',namespaces=ns)
    assert len(images)==35
    embedded=[]
    for item in images:
        target=targets.get(item.get('{'+ns['r']+'}embed'))
        assert target, 'Hay una imagen sin incorporar al documento.'
        name=target.lstrip('/') if target.startswith('/') else 'word/'+target
        assert name in actual, 'No se encuentra una imagen incorporada.'
        embedded.append(actual[name])
    assert Counter(embedded)==expected, 'Faltan capturas o hay repeticiones distintas a los originales.'
    assert not xml.xpath('//a:srcRect',namespaces=ns)
    text=' '.join(xml.xpath('//w:t/text()',namespaces=ns))
    for number in range(1,36):assert f'Evidencia {number}.' in text
    for name in TEAM:assert name in text
    for section in xml.xpath('//w:sectPr/w:pgSz',namespaces=ns):
        assert int(section.get('{'+ns['w']+'}w'))<int(section.get('{'+ns['w']+'}h'))
    assert 'Gimer Amilcar Cervera Evia' in text
    assert 'Alumno' not in text
    assert 'Consulta SQL final' in text
report={'capturas_originales_incorporadas':35,'capturas_completas_sin_recortar':35,'equipo':TEAM,
        'formato_referencia':'PDF de evidencias de Unidad II Actividad 3','orientacion':'vertical',
        'alcance':'Documento y capturas; no se ejecutaron las pruebas de la API.',
        'integridad_docx':'correcta',
        'imagenes_identicas_a_los_originales':True}
print(json.dumps(report,ensure_ascii=False))
