# patch522 : Attaquer — en saison 3, « ⭐ Meilleures chances » devient « ⚡ Moins d'énergie » (idée de H34VEN, 23/11).
# Le tri des chances lisait encore les dés de la saison 2. Maintenant : siege_estimer (s3-60) sur les cibles, par lots de 60
# (3 lots à la fois), les moins chères d'abord. Au-delà de 600 cibles, on trie les 600 plus proches (≈ 4 s), le reste suit.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

rep('app.js', "    if(codes.length > TRI_MAX && triChances){\n      const dk = (c) => (c._distKm == null ? 1e9 : c._distKm);\n      const parDist = cibles.slice().sort((a, b) => dk(a) - dk(b));\n      reste = parDist.slice(TRI_MAX);\n      cibles = parDist.slice(0, TRI_MAX);",
              "    if(codes.length > triMaxActif() && triChances){   // patch522\n      const dk = (c) => (c._distKm == null ? 1e9 : c._distKm);\n      const parDist = cibles.slice().sort((a, b) => dk(a) - dk(b));\n      reste = parDist.slice(triMaxActif());\n      cibles = parDist.slice(0, triMaxActif());")
rep('app.js', "    if(codes.length > TRI_MAX){\n      if(triChances) triMajBoutons(true);",
              "    if(codes.length > triMaxActif()){\n      if(triChances) triMajBoutons(true);")
rep('app.js', "      const pret = chancesPour === intensiteChoisie && codes.every(k => chancesCibles.has(k) || chancesInconnues.has(k));\n      if(!pret){\n        grid.innerHTML = `<p class=\"collection-empty\" id=\"triProgres\">Calcul des chances… 0 / ${codes.length.toLocaleString('fr-FR')}</p>`;\n        chargerChancesListe(codes);\n        return;\n      }\n      const ch = (c) => { const v = chancesCibles.get(c.commune_code); return v ? v.chances : -1; };",
              "      const pret = SIEGE ? codes.every(k => sgEstLu(k)) : chancesPour === intensiteChoisie && codes.every(k => chancesCibles.has(k) || chancesInconnues.has(k));   // patch522\n      if(!pret){\n        grid.innerHTML = `<p class=\"collection-empty\" id=\"triProgres\">${SIEGE ? 'Calcul de l’énergie' : 'Calcul des chances'}… 0 / ${codes.length.toLocaleString('fr-FR')}</p>`;\n        if(SIEGE) sgEstListe(codes); else chargerChancesListe(codes);\n        return;\n      }\n      const ch = SIEGE ? (c) => { const v = sgEstLu(c.commune_code); return v && v.e < 9999 ? -v.e : -1e6; }   // patch522 : les moins chères d'abord\n        : (c) => { const v = chancesCibles.get(c.commune_code); return v ? v.chances : -1; };")
rep('app.js', "function triMajBoutons(trop, total){\n  document.querySelectorAll('#combatTri [data-tri]').forEach(b => {",
"""function triMaxActif(){ return SIEGE ? 600 : TRI_MAX; }   // patch522 : siege_estimer coûte plus cher que les chances
// patch522 : l'énergie de toute une liste, par lots de 60 (3 à la fois), puis on retrie
async function sgEstListe(codes){
  const jeton = {}; triJeton = jeton;
  const manque = codes.filter(k => !sgEstLu(k)), total = codes.length;
  let faits = total - manque.length;
  const lots = []; for(let i = 0; i < manque.length; i += 60) lots.push(manque.slice(i, i + 60));
  for(let i = 0; i < lots.length; i += 3){
    if(triJeton !== jeton) return;
    const p = document.getElementById('triProgres');
    if(p) p.textContent = `Calcul de l’énergie… ${faits.toLocaleString('fr-FR')} / ${total.toLocaleString('fr-FR')}`;
    const rs = await Promise.all(lots.slice(i, i + 3).map(l => sb.rpc('siege_estimer', { p_codes: l }).then(r => ({ l, r }), e => ({ l, r: { error: e } }))));
    if(triJeton !== jeton) return;
    const le = Date.now();
    for(const { l, r } of rs){
      if(r.error){ console.warn('TERRAFRONT tri par énergie indisponible', r.error); triJeton = null; triChances = false;
        notifier({ type: 'erreur', titre: 'Tri impossible', texte: 'L’énergie n’a pas pu être calculée. Réessaie dans un instant.' }); renderCombatGrid(); return; }
      for(const [k, v] of Object.entries(r.data || {})) SG_EST.set(String(k), { ...v, le });
      for(const k of l) if(!SG_EST.has(String(k)) || !sgEstLu(k)) SG_EST.set(String(k), { e: 9999, le });   // pas assiégeable : à la fin
      faits += l.length;
    }
  }
  if(triJeton === jeton){ triJeton = null; renderCombatGrid(); }
}
function triMajBoutons(trop, total){
  const bc = document.querySelector('#combatTri [data-tri="chances"]');   // patch522
  if(bc && SIEGE && bc.textContent !== '⚡ Moins d’énergie') bc.textContent = '⚡ Moins d’énergie';
  document.querySelectorAll('#combatTri [data-tri]').forEach(b => {""")
rep('app.js', "n.textContent = trop ? `Trié parmi les ${TRI_MAX.toLocaleString('fr-FR')} cibles",
              "n.textContent = trop ? `Trié parmi les ${triMaxActif().toLocaleString('fr-FR')} cibles")
rep('style.css', ".siege-on .intensite-bloc, .siege-on #combatTri, .siege-on #reveilDefense{ display:none; }",
                 ".siege-on .intensite-bloc, .siege-on #reveilDefense{ display:none; }   /* patch522 : le tri revient (Moins d'énergie) */")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
if d[0].get('date') != '2026-11-23': d.insert(0, {'date': '2026-11-23', 'nouveautes': []})
e = d[0]; e.setdefault('nouveautes', [])
l = "⚡ Attaquer : le tri « Moins d'énergie » remplace « Meilleures chances » et met en premier les cibles qui te coûtent le moins (parmi les 600 plus proches de ton territoire). Idée de H34VEN."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
