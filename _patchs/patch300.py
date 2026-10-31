# patch300 : lingots gagnés en combattant (1/11) — va avec _sql/s2-72-lingots-combat.sql (déjà lancé)
# Aperçu validé le 1/11 (« c'est parfait ») : https://claude.ai/artifact/Hxg8s8juJjNauYwWhbDPKm
# 1. Fin d'assaut (conquête) : « +2 lingots · 6 / 10 aujourd'hui par les combats »,
#    ou « Plafond du jour atteint (10 / 10 lingots) », ou « Réserve pleine : pas de lingot cette fois ».
# 2. Défense réussie : « +1 lingot (7 / 10 aujourd'hui). » à la fin de la notification.
# 3. Défendre › Bâtiments : cadre « Combats : +6 aujourd'hui · 6 / 10 » sous la réserve,
#    et la règle commence par « Les lingots viennent des Fonderies et des combats ».
# Lit lingots_combat_moi() ; si la fonction manque ou si lingots_combat_ouvert vaut 0, rien ne s'affiche.
import json, pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

# ---------------------------------------------------------------- app.js
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch300' not in s

# état + lecture
s = rep(s, "async function chargerBatiments(){\n  if(!SAISON2) return;\n",
"""// patch300 : les lingots gagnés en combattant (s2-72)
let LINGOTS_COMBAT = null;
const ICONE_COMBAT_LG = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 17.5 3 6V3h3l11.5 11.5M13 19l6-6M16 16l4 4M19 21l2-2"/></svg>';
async function chargerLingotsCombat(){
  try{
    const { data, error } = await sb.rpc('lingots_combat_moi');
    LINGOTS_COMBAT = !error && data && data.ouvert ? data : null;
  }catch(e){ LINGOTS_COMBAT = null; }
  return LINGOTS_COMBAT;
}
// ce que la dernière victoire a rapporté : écart avec avant le combat, sinon le dernier gain s'il est tout frais
function lingotsCombatGain(avant, apres, source){
  if(!apres) return 0;
  if(avant && Number(apres.aujourdhui) >= Number(avant.aujourdhui)) return Number(apres.aujourdhui) - Number(avant.aujourdhui);
  const d = apres.dernier;
  return d && d.source === source && Math.abs(Date.now() - Date.parse(d.le)) < 180000 ? Number(d.quantite) || 0 : 0;
}
function lingotsCombatHtml(){
  const L = LINGOTS_COMBAT; if(!L) return '';
  const n = Number(L.aujourdhui) || 0, p = Number(L.plafond) || 10;
  return `<div class="bt-combat"><div class="btc-haut">${ICONE_COMBAT_LG}<span>Combats : <b>+${n}</b> aujourd’hui</span><em>${n} / ${p}</em></div>
      <div class="btc-barre"><i style="width:${Math.min(100, Math.round(100 * n / p))}%"></i></div>
      <div class="btc-regle">+${L.conquete} par commune conquise, +${L.defense} par défense réussie, ${p} au plus par jour (remis à zéro à minuit).</div></div>`;
}
async function chargerBatiments(){
  if(!SAISON2) return;
  chargerLingotsCombat().then(() => renderBatimentsBloc());   // patch300
""")

# bloc Bâtiments : le cadre sous la réserve + la règle
s = rep(s, """      <span class="btr-prod">${F ? (btProdTotale() > 0 ? `+${btProdTotale()} par jour<br>${pr ? 'prochain dans ' + formatDuree(pr) : 'réserve pleine'}` : 'Fonderie<br>en construction') : 'Pas encore<br>de Fonderie'}</span></div>
""", """      <span class="btr-prod">${F ? (btProdTotale() > 0 ? `+${btProdTotale()} par jour<br>${pr ? 'prochain dans ' + formatDuree(pr) : 'réserve pleine'}` : 'Fonderie<br>en construction') : 'Pas encore<br>de Fonderie'}</span></div>
    ${lingotsCombatHtml()}
""")
s = rep(s, """    <p class="btl-regle">Les lingots ne servent qu’aux bâtiments : ils ne s’échangent pas,""",
           """    <p class="btl-regle">${LINGOTS_COMBAT ? 'Les lingots viennent des Fonderies et des combats. Ils ne servent qu’aux bâtiments : ils' : 'Les lingots ne servent qu’aux bâtiments : ils'} ne s’échangent pas,""")

# fin d'assaut : la ligne des lingots
s = rep(s, "  const soldeAvant = packStatusCache ? Number(packStatusCache.solde) : null;\n  if(SAISON2) setTimeout(majEnergie, 300);\n",
           "  const soldeAvant = packStatusCache ? Number(packStatusCache.solde) : null;\n  const lcAvant = LINGOTS_COMBAT ? Object.assign({}, LINGOTS_COMBAT) : null;   // patch300\n  if(SAISON2) setTimeout(majEnergie, 300);\n")
s = rep(s, """        + (SAISON2 && (BATIMENTS_CARTE.get(String(cible.code)) || {}).centre ? `<span class="as-mon as-bt">${ICONE_CENTRE}Centre de recherche détruit : sa bombe est perdue</span>` : '');   // patch260
""", """        + (SAISON2 && (BATIMENTS_CARTE.get(String(cible.code)) || {}).centre ? `<span class="as-mon as-bt">${ICONE_CENTRE}Centre de recherche détruit : sa bombe est perdue</span>` : '')   // patch260
        + (SAISON2 ? '<span class="as-mon as-lg" hidden></span>' : '');   // patch300
      if(SAISON2) chargerLingotsCombat().then((L) => {   // patch300 : ce que la conquête a rapporté en lingots
        const el = fen.querySelector('.as-lg');
        if(!el || !L) return;
        const g = lingotsCombatGain(lcAvant, L, 'conquete'), n = Number(L.aujourdhui) || 0, p = Number(L.plafond) || 10;
        let t = '';
        if(g > 0) t = `<span><b>+${g} lingot${g > 1 ? 's' : ''}</b> <small>· ${n} / ${p} aujourd’hui par les combats</small></span>`;
        else if(n >= p) t = `<span>Plafond du jour atteint (${p} / ${p} lingots)</span>`;
        else if(BATIMENTS && lingotsActuels() >= (Number(BATIMENTS.max) || 30)) t = '<span>Réserve pleine : pas de lingot cette fois</span>';
        if(!t) return;
        el.innerHTML = ICONE_LINGOT + t;
        el.classList.toggle('plein', g <= 0);
        el.hidden = false;
        renderBatimentsBloc();
      });
""")

# défense réussie : une phrase en plus
s = rep(s, """    const r = data && data[0];
    if(r && r.reussie){
      notifier({
        type: 'victoire',
        titre: `Défense réussie à ${btn.dataset.nom}`,
        texte: (r.victoires_restantes > 0 ? `L'attaquant perd une victoire (plus que ${r.victoires_restantes} sur 3).` : 'L\\'attaquant perd sa victoire : son attaque repart de zéro.')
          + (recharge > 0 ? ` +${recharge} énergie dans la garnison.` : ''),""",
"""    const r = data && data[0];
    let lgTexte = '';   // patch300 : ce que la défense a rapporté en lingots
    if(r && r.reussie && SAISON2){
      const lcAvant = LINGOTS_COMBAT ? Object.assign({}, LINGOTS_COMBAT) : null;
      const L = await chargerLingotsCombat();
      if(L){
        const g = lingotsCombatGain(lcAvant, L, 'defense'), n = Number(L.aujourdhui) || 0, p = Number(L.plafond) || 10;
        lgTexte = g > 0 ? ` +${g} lingot${g > 1 ? 's' : ''} (${n} / ${p} aujourd’hui).` : n >= p ? ` Plafond du jour atteint (${p} / ${p} lingots).` : '';
        renderBatimentsBloc();
      }
    }
    if(r && r.reussie){
      notifier({
        type: 'victoire',
        titre: `Défense réussie à ${btn.dataset.nom}`,
        texte: (r.victoires_restantes > 0 ? `L'attaquant perd une victoire (plus que ${r.victoires_restantes} sur 3).` : 'L\\'attaquant perd sa victoire : son attaque repart de zéro.')
          + (recharge > 0 ? ` +${recharge} énergie dans la garnison.` : '') + lgTexte,""")
f.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------- style.css
f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch300' not in s
s = rep(s, ".as-mon.as-bt svg{ color:#FFB27A; }\n", """.as-mon.as-bt svg{ color:#FFB27A; }
/* patch300 : lingots gagnés en combattant */
.as-mon.as-lg{ color:#FFE7A8; }
.as-mon.as-lg b{ color:#FFE08A; }
.as-mon.as-lg small{ color:#B9A08C; font-size:.78rem; }
.as-mon.as-lg.plein{ color:#B9A08C; }
.bt-combat{ margin-top:8px; padding:10px 12px; border-radius:12px; background:rgba(232,131,58,.07); border:1px dashed rgba(232,131,58,.35); }
.btc-haut{ display:flex; align-items:center; gap:7px; font-size:.8rem; color:#FFD9B8; }
.btc-haut svg{ width:15px; height:15px; color:#FFB27A; flex:none; }
.btc-haut b{ color:#fff; font-weight:700; }
.btc-haut em{ margin-left:auto; font-style:normal; color:#fff; font-weight:700; }
.btc-barre{ height:5px; border-radius:3px; background:rgba(255,255,255,.08); margin:8px 0 6px; overflow:hidden; }
.btc-barre i{ display:block; height:100%; border-radius:3px; background:linear-gradient(90deg,#F0B429,#FFE08A); }
.btc-regle{ font-size:.72rem; color:#B9A08C; line-height:1.4; }
""")
f.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------- index.html (règles)
f = pathlib.Path('index.html'); s = f.read_text(encoding='utf-8')
assert 'patch300' not in s
s = rep(s, "Une <b>2e Fonderie</b> coûte 30 lingots : 10 lingots de plus par jour, réserve jusqu'à 45.",
           "Une <b>2e Fonderie</b> coûte 30 lingots : 10 lingots de plus par jour, réserve jusqu'à 45. Les <b>combats</b> en rapportent aussi : <b>+2</b> par commune conquise, <b>+1</b> par défense réussie, <b>10 au plus par jour</b> (seules les victoires qui comptent pour le score).<!-- patch300 -->")
f.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------- nouveautés
f = pathlib.Path('data/nouveautes.json'); d = json.loads(f.read_text(encoding='utf-8'))
e = next((x for x in d if x['date'] == '2026-11-01'), None)
if e is None:
    e = {'date': '2026-11-01', 'nouveautes': [], 'correctifs': []}
    d.insert(0, e)
e['nouveautes'].insert(0, '⚔ Front : les combats rapportent des lingots (+2 par conquête, +1 par défense réussie, 10 au plus par jour)')
f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch300 appliqué')
