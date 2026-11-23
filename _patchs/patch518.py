# patch518 : Attaquer — le « ≈ N ⚡ » de chaque cible devient le vrai chiffre (s3-60 siege_estimer), avec une ligne
# qui dit pourquoi (tes dégâts −10 %, rempart +25 %, Forteresse…). Avant : 8 / 8 / 9 / 15 / 27 fixes par rareté.
# Les chiffres arrivent par lots de 60 cartes affichées, gardés 2 min. En attendant, l'ancien chiffre s'affiche.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

rep('app.js', """      const sgEst = { commun: 8, peucommun: 8, rare: 9, epique: 15, legendaire: 27 }[tier ? tier.id : 'commun'] || 8;
      bouton = `<button class="cible-attaquer ca-att" data-action="assieger" data-code="${c.commune_code}">Assiéger <span class="ca-pastille"><b>≈ ${sgEst} ⚡</b></span></button>`;""",
"""      const sgEst = { commun: 8, peucommun: 8, rare: 9, epique: 15, legendaire: 27 }[tier ? tier.id : 'commun'] || 8;
      const vrai = sgEstLu(c.commune_code);   // patch518 : le vrai chiffre, s'il est arrivé
      bouton = `<button class="cible-attaquer ca-att" data-action="assieger" data-code="${c.commune_code}">${vrai && vrai.en_cours ? 'Continuer' : 'Assiéger'} <span class="ca-pastille" data-sg-est="${c.commune_code}"><b>≈ ${vrai ? vrai.e : sgEst} ⚡</b></span></button>`
        + `<p class="ca-est" data-sg-pq="${c.commune_code}">${vrai ? sgEstPourquoi(vrai) : ''}</p>`;""")
rep('app.js', "  combatAffichees = cibles;\n  afficherParLots(grid, cibles, carteCible, signature);",
              "  combatAffichees = cibles;\n  afficherParLots(grid, cibles, carteCible, signature);\n  sgEstSuivre(grid);   // patch518")
rep('app.js', "function afficherParLots(grid, elements, fabriquer, signature, lot){",
"""// patch518 : l'énergie qu'il faut vraiment pour chaque cible d'Attaquer (siege_estimer, s3-60)
const SG_EST = new Map();   // code -> { e, res, mult, rempart, en_cours, le }
function sgEstLu(code){ const v = SG_EST.get(String(code)); return v && Date.now() - v.le < 120000 ? v : null; }
function sgEstPourquoi(v){
  const m = Math.round((Number(v.mult) - 1) * 100), rp = Math.round((Number(v.rempart) - 1) * 100);
  const L = [];
  if(m) L.push(`<span class="${m > 0 ? 'p' : 'm'}">tes dégâts ${m > 0 ? '+' : '−'}${Math.abs(m)} %</span>`);
  if(rp > 0) L.push(`<span class="m">rempart +${rp} %</span>`);
  if(v.en_cours) L.push('<span>siège en cours</span>');
  return L.join(' · ');
}
let sgEstMinuteur = null;
function sgEstSuivre(grid){
  if(!grid || typeof SIEGE === 'undefined' || !SIEGE) return;
  if(!grid._sgEstObs && 'MutationObserver' in window){
    grid._sgEstObs = new MutationObserver(() => { clearTimeout(sgEstMinuteur); sgEstMinuteur = setTimeout(() => sgEstCharger(grid), 250); });
    grid._sgEstObs.observe(grid, { childList: true });
  }
  clearTimeout(sgEstMinuteur); sgEstMinuteur = setTimeout(() => sgEstCharger(grid), 250);
}
async function sgEstCharger(grid){
  const codes = [...new Set([...grid.querySelectorAll('[data-sg-est]')].map(e => e.dataset.sgEst).filter(c => !sgEstLu(c)))];
  for(let i = 0; i < codes.length; i += 60){
    const { data, error } = await sb.rpc('siege_estimer', { p_codes: codes.slice(i, i + 60) });
    if(error) return;   // fonction absente : on garde l'ancien chiffre
    const le = Date.now();
    for(const [k, v] of Object.entries(data || {})) SG_EST.set(String(k), { ...v, le });
    for(const k of Object.keys(data || {})){
      const v = SG_EST.get(String(k));
      grid.querySelectorAll(`[data-sg-est="${CSS.escape(k)}"]`).forEach(e => { e.innerHTML = `<b>≈ ${v.e} ⚡</b>`; e.title = `Résistance ${v.res}, environ ${v.e} ⚡ pour la prendre`; });
      grid.querySelectorAll(`[data-sg-pq="${CSS.escape(k)}"]`).forEach(e => { e.innerHTML = sgEstPourquoi(v); });
    }
  }
}
function afficherParLots(grid, elements, fabriquer, signature, lot){""")
# après un siège, le chiffre de cette commune doit être recalculé
rep('app.js', "function sgCalcHtml(a){", "function sgCalcHtml(a){\n  if(typeof SG !== 'undefined' && SG && SG.code) SG_EST.delete(String(SG.code));   // patch518 : recalculé au retour dans Attaquer")
rep('style.css', ".ca-note{ margin:-4px 2px 0; font-size:.68rem; color:#F7B267; }",
""".ca-note{ margin:-4px 2px 0; font-size:.68rem; color:#F7B267; }
.ca-est{ margin:-4px 2px 0; font-size:.68rem; color:var(--brume); min-height:0; }   /* patch518 */
.ca-est:empty{ display:none; }
.ca-est .m{ color:#FF8A8F; } .ca-est .p{ color:#3DD68C; }""")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
if d[0].get('date') != '2026-11-23': d.insert(0, {'date': '2026-11-23', 'nouveautes': []})
e = d[0]; e.setdefault('nouveautes', [])
l = "⚡ Attaquer : le « ≈ N ⚡ » de chaque cible est maintenant le vrai chiffre pour toi (tes communes autour, rempart, Forteresse, garnison, siège déjà commencé), avec une ligne qui dit ce qui le fait monter ou baisser."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
