# patch514 : calque « Vue départements » (idée d'Arkhannou, 23/11) : la carte reste par départements même en zoomant
# (utile pour l'Île-de-France). Éteint par défaut, retenu comme les autres calques. Toucher un département ouvre sa fiche.
# Le cartouche « Petite couronne » ne s'affiche que dézoomé, comme avant.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

# le calque, éteint par défaut
rep('app.js', "raretes: true, passage: false, clans: false, batiments: true, motifs: true, couleur: 'joueurs', clanVue: 'contour' };",
              "raretes: true, passage: false, clans: false, batiments: true, motifs: true, figer: false, couleur: 'joueurs', clanVue: 'contour' };   // patch514 : figer")
rep('app.js', "function clanPlein(){",
"""// patch514 : la carte par départements, dézoomée ou figée par le calque « Vue départements »
function zoomDepts(){ return mapZoom < SEUIL_CONTOURS || CALQUES.figer === true; }
function clanPlein(){""")
rep('app.js', """    ordre.push('motifs');
  }
  zone.innerHTML = ordre.map(id =>""",
"""    ordre.push('motifs');
  }
  NOMS.figer = 'Vue départements';   // patch514
  ICONES.figer = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"><path d="M3 4h7v7H3zM3 14h7v7H3zM14 4h7v7h-7z"/><rect x="14" y="15.5" width="7" height="5.5" rx="1"/><path d="M15.6 15.5v-1.6a1.9 1.9 0 0 1 3.8 0v1.6"/></svg>';
  ordre.push('figer');
  zone.innerHTML = ordre.map(id =>""")
# les endroits où la carte choisit entre départements et communes
rep('app.js', "    if(mapZoom >= SEUIL_CONTOURS) renderMapOverlay();", "    if(!zoomDepts()) renderMapOverlay();   // patch514")
rep('app.js', "    const visible = mapZoom < SEUIL_CONTOURS || mapZoom >= (ZOOM_MINI[e.tier.id] || 1);",
              "    const visible = zoomDepts() || mapZoom >= (ZOOM_MINI[e.tier.id] || 1);   // patch514")
rep('app.js', "  if(!CALQUES.communes) return mapZoom < SEUIL_CONTOURS ? 'depts' : 'contours';",
              "  if(!CALQUES.communes) return zoomDepts() ? 'depts' : 'contours';   // patch514")
rep('app.js', "  if(mapZoom < SEUIL_CONTOURS){\n    if(!CONTOURS_DEPTS) chargerDepartements();",
              "  if(zoomDepts()){   // patch514\n    if(!CONTOURS_DEPTS) chargerDepartements();")
rep('app.js', "  if(mapZoom >= SEUIL_CONTOURS){\n    const deps = departementsVisibles(liste);",
              "  if(!zoomDepts()){   // patch514\n    const deps = departementsVisibles(liste);")
rep('app.js', "  const rarCouleur = SAISON2 && CALQUES.couleur === 'raretes' && mapZoom >= SEUIL_CONTOURS;   // patch294",
              "  const rarCouleur = SAISON2 && CALQUES.couleur === 'raretes' && !zoomDepts();   // patch294, patch514")
rep('app.js', "  return mapZoom < SEUIL_CONTOURS && CONTOURS_DEPTS && typeof CONTOURS_DEPTS === 'object';",
              "  return zoomDepts() && CONTOURS_DEPTS && typeof CONTOURS_DEPTS === 'object';   // patch514")
rep('app.js', "  const voir = !!(el.dataset.pret && vueDepartements());",
              "  const voir = !!(el.dataset.pret && vueDepartements() && mapZoom < SEUIL_CONTOURS);   // patch514 : pas en vue figée de près")
# l'ancien affichage SVG (?svg)
rep('app.js', "    const visibleAuZoom = mapZoom < SEUIL_CONTOURS || mapZoom >= (ZOOM_MINI[e.tier.id] || 1);",
              "    const visibleAuZoom = zoomDepts() || mapZoom >= (ZOOM_MINI[e.tier.id] || 1);   // patch514")
rep('app.js', "  if(mapZoom < SEUIL_CONTOURS && liste.length > 0){", "  if(zoomDepts() && liste.length > 0){   // patch514")
rep('app.js', "  const avecContours = mapZoom >= SEUIL_CONTOURS && liste.length > 0;", "  const avecContours = !zoomDepts() && liste.length > 0;   // patch514")

p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
if d[0].get('date') != '2026-11-23': d.insert(0, {'date': '2026-11-23', 'nouveautes': []})
e = d[0]; e.setdefault('nouveautes', [])
l = "🗺️ Territoire : nouveau calque « Vue départements ». Allumé, la carte reste découpée par départements même en zoomant (pratique pour l'Île-de-France) ; toucher un département ouvre sa fiche. Idée d'Arkhannou."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
