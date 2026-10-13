import json,glob,os
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
cog=json.load(open('package/data/communes.json'))
com=json.load(open('/tmp/claude-0/t128/data/communes.json')); codes={x[6] for x in com}
vers={}
for c in cog:
    if c['type']=='commune-actuelle':
        for a in c.get('anciensCodes',[]): vers.setdefault(a,set()).add(c['code'])
    elif c['type'] in ('commune-deleguee','commune-associee') and c.get('chefLieu'):
        vers.setdefault(c['code'],set()).add(c['chefLieu'])
def geom(rings):
    # anneaux : exterieurs et trous melanges ; regle pair-impair
    g=None
    for r in rings:
        if len(r)<3: continue
        p=Polygon(r).buffer(0)
        g=p if g is None else g.symmetric_difference(p)
    return g
def anneaux(g):
    out=[]
    for p in (g.geoms if isinstance(g,MultiPolygon) else [g]):
        if p.is_empty: continue
        out.append([[round(x,4),round(y,4)] for x,y in p.exterior.coords[:-1]])
        for h in p.interiors: out.append([[round(x,4),round(y,4)] for x,y in h.coords[:-1]])
    return out
bilan=[]; total=0
for f in sorted(glob.glob('/mnt/user-data/uploads/tcg-rues-prototype/contours/*.json')):
    dep=os.path.basename(f)[:-5]
    C=json.load(open(f))
    groupes={}
    for k in list(C):
        if k in codes: continue
        t=vers.get(k,set())&codes
        if len(t)==1 and k not in t:
            groupes.setdefault(t.pop(),[]).append(k)
    for cible, olds in groupes.items():
        if cible[:2]!=k[:2] and cible not in C and not any(cible==x for x in C):
            pass
        pieces=[geom(C[o]) for o in olds]
        if cible in C: pieces.append(geom(C[cible]))
        u=unary_union([p for p in pieces if p is not None and not p.is_empty])
        u=u.buffer(0.0004, join_style=2).buffer(-0.0004, join_style=2).simplify(0.0008, preserve_topology=True)
        C[cible]=anneaux(u)
        for o in olds: del C[o]
        total+=len(olds); bilan.append((cible, olds))
    json.dump(C, open('/tmp/claude-0/contours-neufs/'+dep+'.json','w'), separators=(',',':'))
print('anciens contours rattaches', total, 'communes agrandies', len(bilan))
print([b for b in bilan if b[0]=='85146'])
