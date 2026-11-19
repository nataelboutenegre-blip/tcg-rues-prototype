# patch465 : les cartes v2 (« piste A », choisie par Nataël le 19/11 pour le 22).
# Grande photo, nom posé sur la photo, plaque du département, rareté en pastille, cadres « matières ».
# CSS seulement (+ un interrupteur) : s'allume avec l'habillage de la saison 3 (html.topo, 22/11 10 h 01),
# s'éteint SEUL avec config_jeu 'interface'.cartes = 0 (classe html.sans-cartes).
# Ne touche pas aux cartes qui ont déjà leur propre habillage : skins, Aurore, atelier, brillantes,
# éclat, hantées (elles gardent leur aspect d'aujourd'hui).
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'

def rep(f, a, b):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if b in t: print(f'{f} : déjà fait'); return
    assert t.count(a) == 1, (f, t.count(a), a[:60])
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

rep('app.js',
"      document.documentElement.classList.toggle('sans-vitrine', o.vitrine !== undefined && o.vitrine !== null && Number(o.vitrine) === 0);   // patch438\n",
"      document.documentElement.classList.toggle('sans-vitrine', o.vitrine !== undefined && o.vitrine !== null && Number(o.vitrine) === 0);   // patch438\n"
"      document.documentElement.classList.toggle('sans-cartes', o.cartes !== undefined && o.cartes !== null && Number(o.cartes) === 0);   // patch465 : les cartes v2\n")

# la grande carte (révélation) n'avait jamais de photo : on la pose (fichier = code + '.jpg' pour toutes
# les communes qui ont une photo, vérifié le 19/11 ; sinon l'image échoue et le dessin reste). Cachée
# hors cartes v2 : une image en display:none et loading="lazy" n'est pas téléchargée. Pas la classe
# art-photo : les règles « :has(.art-photo) » changeraient l'ancienne carte même éteinte.
rep('app.js', "${carteArtSvg(draw.code, draw.tier.id)}${bxg.art}",
    "${carteArtSvg(draw.code, draw.tier.id)}${draw.aurore ? '' : `<img class=\"cv2-photo\" src=\"${echapperTexte(urlPhoto(draw.code + '.jpg'))}\" alt=\"\" loading=\"lazy\" decoding=\"async\" data-onfail=\"1\">`}${bxg.art}")   # patch465

# la portée : habillage S3 allumé, cartes v2 pas coupées, carte sans habillage à elle
M = "html.topo:not(.sans-cartes) .mini:not(.skin):not(.aurore):not(.atl):not(.bri):not(.ecl):not(.hnt)"
C = "html.topo:not(.sans-cartes) .card:not(.skin):not(.aurore):not(.atl):not(.bri):not(.ecl):not(.hnt)"
CADRES = {
    'commun': '#AEB7C5',
    'peucommun': '#22A06B',
    'rare': 'linear-gradient(135deg, #A9CBFF, #2F7CF6 32%, #1B4FB0 58%, #8FB8FF 82%, #2F7CF6)',
    'epique': 'linear-gradient(135deg, #D3BBFF, #9B5CF6 26%, #5CC2F6 50%, #F2A6E4 72%, #9B5CF6)',
    'legendaire': 'linear-gradient(135deg, #FFF1B8, #F0B429 32%, #B7791F 58%, #FCE38A 82%, #F0B429)',
}
POINTS = {'commun': 'var(--c-commun)', 'peucommun': 'var(--c-peucommun)', 'rare': 'var(--c-rare)', 'epique': 'var(--c-epique)', 'legendaire': 'var(--c-legendaire)'}
VOILE = 'linear-gradient(180deg, rgba(9,18,34,0) 40%, rgba(9,18,34,.84) 100%)'
COURBES = 'repeating-radial-gradient(ellipse at 88% 130%, transparent 0 11px, rgba(19,35,59,.055) 11px 12px)'

css = ["\n/* ---------- patch465 : cartes v2 (piste A), saison 3 ---------- */", ".carte-art > .cv2-photo{ display:none; }"]
# --- la petite carte (listes, collection, Combat, fiche agrandie) ---
for t, bg in CADRES.items():
    css.append(f"{M}.{t}{{ background:{bg}; }}")
css += [
    f"{M}{{ padding:3px; }}",
    f"{M}.commun, {M}.peucommun{{ padding:2px; }}",
    f"{M} .mini-int{{ position:relative; border-radius:8px; }}",
    f"{M} .mini-art{{ aspect-ratio:auto; flex:0 0 auto; height:64%; margin:0; border-radius:0; }}",
    f"{M} .mini-art::after{{ content:''; position:absolute; inset:0; z-index:2; pointer-events:none; background:{VOILE}; }}",
    f"{M} .art-voile{{ display:none; }}",
    # le département : une plaque en haut à droite, sous la pastille ×N / PERDUE / siège s'il y en a une
    f"{M} .mini-dept{{ top:4px; right:4px; bottom:auto; padding:2px 4px 1px; border-radius:4px; background:var(--papier); color:var(--encre); text-shadow:none; font-size:.74rem; line-height:1; box-shadow:0 1px 4px rgba(0,0,0,.3); }}",
    f"{M} .mini-int:has(> .mini-ex, > .mini-perdue) .mini-dept, {M} .mini-art:has(.mini-siege) .mini-dept{{ top:26px; }}",
    # le nom, sur la photo (la photo fait 64 % de la hauteur : le bas de la carte en fait 36 %)
    f"{M} .mini-nom{{ position:absolute; left:6px; right:6px; bottom:calc(36% + 4px); z-index:3; color:#fff; text-shadow:0 1px 3px rgba(0,0,0,.45); -webkit-hyphens:auto; hyphens:auto; }}",
    f"{M}.legendaire .mini-nom{{ color:#FCE38A; }}",
    f"{M} .mini-infos{{ padding:5px 6px 4px; justify-content:center; gap:3px; background:{COURBES}; }}",
    f"{M} .mini-rarete{{ order:-1; margin-top:0; display:flex; align-items:center; gap:4px; color:var(--encre); font-size:.6rem; font-weight:600; }}",
    f"{M} .mini-rarete::before{{ content:''; width:6px; height:6px; border-radius:50%; flex:none; }}",
]
for t, c in POINTS.items():
    css.append(f"{M}.{t} .mini-rarete::before{{ background:{c}; }}")
css += [
    f"{M} .mini-num{{ margin-top:0; color:#55606E; }}",
    f"{M.replace(' .mini', ' .c3d .mini', 1)} .mini-total{{ display:inline; }}",   # la fiche agrandie a la place pour « / 302 »
    f"{M} .mini-bt{{ margin-top:0; padding-top:1px; }}",
    f"{M} .mini-bt:not(:empty) + .mini-rarete{{ margin-top:0; }}",
]
# --- la grande carte (révélation des paquets) ---
for t, bg in CADRES.items():
    css.append(f"{C}.{t} .carte-cadre{{ background:{bg}; }}")
css += [
    f"{C} .carte-cadre{{ padding:5px; }}",
    f"{C}.commun .carte-cadre, {C}.peucommun .carte-cadre{{ padding:4px; }}",
    f"{C}.legendaire .carte-cadre{{ padding:6px; }}",
    f"{C} .carte-int{{ position:relative; border-radius:10px; background:{COURBES}, var(--papier); }}",
    f"{C} .carte-art{{ height:62%; margin:0; border-radius:0; flex:none; }}",
    f"{C} .carte-art::after{{ content:''; position:absolute; inset:0; z-index:2; pointer-events:none; background:{VOILE}; }}",
    f"{C} .art-voile{{ display:none; }}",
    f"{C} .carte-art > .cv2-photo{{ display:block; position:absolute; inset:0; width:100%; height:100%; object-fit:cover; border:0; z-index:1; }}",
    f"{C} .carte-dept{{ top:8px; right:8px; bottom:auto; padding:4px 7px 3px; border-radius:6px; background:var(--papier); color:var(--encre); text-shadow:none; font-size:1.15rem; line-height:1; box-shadow:0 2px 6px rgba(0,0,0,.3); }}",
    # le nom et le département sur la photo (la photo fait 62 % : le bas en fait 38 %)
    f"{C} .carte-nom{{ position:absolute; left:11px; right:11px; bottom:calc(38% + 25px); z-index:3; color:#fff; text-shadow:0 1px 4px rgba(0,0,0,.45); -webkit-hyphens:auto; hyphens:auto; }}",
    f"{C}.legendaire .carte-nom{{ color:#FCE38A; }}",
    f"{C} .carte-departement{{ position:absolute; left:11px; right:11px; bottom:calc(38% + 9px); z-index:3; margin:0; color:#E3EAF3; }}",
    f"{C} .carte-infos{{ padding:10px 11px 0; }}",
    f"{C} .carte-stats{{ margin:0; border-top:0; padding-top:0; gap:18px; }}",
    f"{C} .carte-stats span{{ color:#55606E; }}",
    f"{C} .carte-stats b{{ font-size:1.3rem; }}",
    # la rareté passe en bas, en pastille ; le numéro est déjà dans « Rang »
    f"{C} .carte-haut{{ order:4; padding:0 11px 8px; }}",
    f"{C} .carte-lisere{{ order:5; }}",
    f"{C} .carte-num{{ display:none; }}",
    f"{C} .carte-rarete{{ display:flex; align-items:center; gap:5px; padding:0; background:none !important; color:var(--encre) !important; text-transform:uppercase; letter-spacing:.1em; font-size:.62rem; }}",
    f"{C} .carte-rarete::before{{ content:''; width:8px; height:8px; border-radius:50%; flex:none; }}",
]
for t, c in POINTS.items():
    css.append(f"{C}.{t} .carte-rarete::before{{ background:{c}; }}")
css += [
    "@media (max-width: 600px){",
    f"  {M} .mini-rarete{{ font-size:.54rem; gap:3px; }}",
    f"  {M} .mini-rarete::before{{ width:5px; height:5px; }}",
    f"  {C} .carte-stats b{{ font-size:1.1rem; }}",
    f"  {C} .carte-dept{{ font-size:1rem; }}",
    f"  {C} .carte-nom{{ bottom:calc(38% + 22px); }}",
    "}",
]
p = os.path.join(R, 'style.css'); t = open(p, encoding='utf-8').read()
if 'patch465 : cartes v2' in t: print('style.css : déjà fait')
else:
    open(p, 'a', encoding='utf-8').write('\n'.join(css) + '\n'); print('style.css : ok')
