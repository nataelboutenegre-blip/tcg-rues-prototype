import json, re
from fontTools.svgLib.path import parse_path
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
import pathops
ic = json.load(open('/tmp/gi/package/icons.json'))['icons']
def d_de(n): return re.search(r' d="([^"]+)"', ic[n]['body']).group(1)
def vers_pathops(d, t=(1,0,0,1,0,0)):
    p = pathops.Path(); pen = p.getPen(); parse_path(d, TransformPen(pen, t)); return p
def vers_d(p, marge=4):
    # 512 -> 100 avec une petite marge, arrondi à 0,1
    s = (100 - 2 * marge) / 512
    pen = SVGPathPen(None, ntos=lambda v: ('%.1f' % v).rstrip('0').rstrip('.'))
    p.draw(TransformPen(pen, (s, 0, 0, s, marge, marge)))
    return pen.getCommands()
def simple(n):
    p = vers_pathops(d_de(n)); p.simplify(fix_winding=True); return p
def bicephale():
    aigle = vers_pathops(d_de('eagle-emblem'))
    aigle.simplify(fix_winding=True)
    droite = pathops.Path(); pn = droite.getPen()
    pn.moveTo((256, -10)); pn.lineTo((600, -10)); pn.lineTo((600, 600)); pn.lineTo((256, 600)); pn.closePath()
    moitie = pathops.op(aigle, droite, pathops.PathOp.INTERSECTION)
    miroir = pathops.Path(); moitie.draw(TransformPen(miroir.getPen(), (-1, 0, 0, 1, 512, 0)))
    return pathops.op(moitie, miroir, pathops.PathOp.UNION)
CHOIX = [('lion', 'Lion', 'lion'), ('aigle', 'Aigle', 'eagle-emblem'), ('aigle2', 'Aigle à deux têtes', None),
         ('griffon', 'Griffon', 'griffin-symbol'), ('dragon', 'Dragon', 'wyvern'), ('sanglier', 'Sanglier', 'boar'),
         ('ours', 'Ours', 'bear-head'), ('loup', 'Loup', 'wolf-head'), ('cerf', 'Cerf', 'deer'), ('dauphin', 'Dauphin', 'dolphin'),
         ('coq', 'Coq', 'rooster'), ('cygne', 'Cygne', 'swan'), ('corbeau', 'Corbeau', 'raven'), ('licorne', 'Licorne', 'unicorn'),
         ('salamandre', 'Salamandre', 'salamander'), ('abeille', 'Abeille', 'bee'), ('pegase', 'Pégase', 'pegasus')]
out = []
for i, nom, src in CHOIX:
    p = bicephale() if src is None else simple(src)
    out.append({'id': i, 'nom': nom, 'cat': 'Animaux', 'pack': None, 'type': 'forme', 'd': vers_d(p), 'src': src or 'eagle-emblem (miroir)'})
json.dump(out, open('/tmp/anim/animaux.json', 'w'), ensure_ascii=False)
for o in out: print(o['id'], len(o['d']))
cells = ''.join(f'<div style="display:inline-block;width:130px;text-align:center;font:12px sans-serif;margin:4px"><svg viewBox="0 0 100 100" width="110" height="110" style="background:#1E5A44"><path fill="#F0B429" d="{o["d"]}"/></svg><br>{o["nom"]}</div>' for o in out)
open('/tmp/anim/planche.html', 'w').write('<html><body style="background:#0B1424;color:#ddd;width:1000px">' + cells + '</body></html>')
