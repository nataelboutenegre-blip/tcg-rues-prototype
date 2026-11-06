# patch361 (6/11/2026) : deux idées d'Oshannir.
#
# 1. QG : la pastille rouge du menu ne disait pas pourquoi. En ouvrant le QG,
#    un encadré « Pourquoi la pastille » liste les raisons (Commune du jour à
#    jouer, résultats de Radar / Rafale, défis reçus) et une pastille marque
#    le jeu concerné. Les résultats passent « vus » à l'ouverture (comme
#    avant) : l'encadré garde les raisons pendant toute la visite.
# 2. Combat › Attaquer : plusieurs raretés à la fois (ex. Légendaire +
#    Épique). « Toutes » remet à zéro ; décocher la dernière revient à
#    « Toutes ».
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch361' not in s, 'patch361 déjà appliqué'

# ---------- 1. QG : pourquoi la pastille ----------
s = rep(s, "async function ouvrirQG(){\n  if(radarModeEntr) clearInterval(radarChrono);\n  majBoutonEntr();\n  renderQG();",
"""// patch361 : les raisons de la pastille du QG, notées avant que les résultats passent « vus »
let qgRaisons = null;
function qgRaisonsCalculer(){
  const l = [];
  const cdj = document.getElementById('cdjBadge');
  if(cdj && !cdj.hidden) l.push({ jeu: 'qgCdj', n: 1, txt: 'La <b>Commune du jour</b> n’est pas encore jouée' });
  const pl = (n, un, plus) => `${n} ${n > 1 ? plus : un}`;
  const rv = radarEtat ? Number(radarEtat.non_vus || 0) : 0;
  const rd = radarEtat && Array.isArray(radarEtat.defis_recus) ? radarEtat.defis_recus.length : 0;
  const fv = rafaleEtat ? Number(rafaleEtat.non_vus || 0) : 0;
  const fd = rafaleEtat && Array.isArray(rafaleEtat.defis_recus) ? rafaleEtat.defis_recus.length : 0;
  if(rv) l.push({ jeu: 'qgRadar', n: rv, txt: `<b>Radar</b> : ${pl(rv, 'nouveau résultat de duel', 'nouveaux résultats de duels')} (dans « Derniers duels »)` });
  if(rd) l.push({ jeu: 'qgRadar', n: rd, defi: true, txt: `<b>Radar</b> : ${pl(rd, 'défi reçu', 'défis reçus')}` });
  if(fv) l.push({ jeu: 'qgRafale', n: fv, txt: `<b>Rafale</b> : ${pl(fv, 'nouveau résultat de duel', 'nouveaux résultats de duels')} (dans « Derniers duels »)` });
  if(fd) l.push({ jeu: 'qgRafale', n: fd, defi: true, txt: `<b>Rafale</b> : ${pl(fd, 'défi reçu', 'défis reçus')}` });
  return l;
}
function qgRaisonsAfficher(){
  let bloc = document.getElementById('qgRaisons');
  const panel = document.getElementById('panel-qg');
  if(!bloc && panel){
    bloc = document.createElement('div');
    bloc.id = 'qgRaisons'; bloc.className = 'qg-raisons';
    const sub = panel.querySelector('.sub');
    if(sub) sub.after(bloc); else panel.prepend(bloc);
  }
  document.querySelectorAll('.qg-carte .qg-pastille').forEach(x => x.remove());
  if(!bloc) return;
  const l = qgRaisons || [];
  bloc.hidden = !l.length;
  if(!l.length){ bloc.innerHTML = ''; return; }
  bloc.innerHTML = `<b class="qg-raisons-t">Pourquoi la pastille</b><ul>${l.map(r => `<li>${r.txt}</li>`).join('')}</ul>`;
  for(const id of new Set(l.map(r => r.jeu))){
    const h = document.querySelector(`#${id} .qg-titre h2`);
    if(h) h.insertAdjacentHTML('beforeend', '<i class="qg-pastille" aria-hidden="true"></i>');
  }
}

async function ouvrirQG(){
  if(radarModeEntr) clearInterval(radarChrono);
  majBoutonEntr();
  qgRaisons = qgRaisonsCalculer(); qgRaisonsAfficher();   // patch361 : ce qu'on sait déjà
  renderQG();""")
s = rep(s, "  await Promise.all([chargerRadar(), chargerRafale()]);\n  renderQG();\n  // les resultats affiches sont vus : la pastille s'eteint\n",
           "  await Promise.all([chargerRadar(), chargerRafale()]);\n  renderQG();\n"
           "  { const n = qgRaisonsCalculer(); if(n.length) qgRaisons = n; qgRaisonsAfficher(); renderQG(); }   // patch361 : avec les états à jour, avant « vus »\n"
           "  // les resultats affiches sont vus : la pastille s'eteint\n")

# ---------- 2. Combat : plusieurs raretés ----------
s = rep(s, "const tiersCombat = () => ['rare', 'epique', 'legendaire'].concat([...combatBasCharges]);\nfunction combatBasVoulus(){\n  if(COMBAT_TIERS_BAS.indexOf(combatFilterTier) >= 0) return [combatFilterTier];",
           "const tiersCombat = () => ['rare', 'epique', 'legendaire'].concat([...combatBasCharges]);\n"
           "// patch361 : plusieurs raretés à la fois, « legendaire,epique » ; 'tous' = aucune restriction\n"
           "const combatTiersChoisis = () => combatFilterTier === 'tous' ? null : new Set(combatFilterTier.split(','));\n"
           "function combatBasVoulus(){\n"
           "  { const ch = combatTiersChoisis(); if(ch) return COMBAT_TIERS_BAS.filter(t => ch.has(t)); }   // patch361")
s = rep(s, "  if(combatFilterTier !== 'tous'){\n    cibles = cibles.filter(c => c.communes.tier === combatFilterTier);\n  }",
           "  if(combatFilterTier !== 'tous'){\n    const ch = combatTiersChoisis();   // patch361\n    cibles = cibles.filter(c => ch.has(c.communes.tier));\n  }")
s = rep(s, "  document.querySelectorAll('#combatFilters .filter-pill').forEach(p => p.classList.remove('active'));\n  pill.classList.add('active');\n  combatFilterTier = pill.dataset.tier;\n  renderCombatGrid();",
"""  // patch361 : un clic ajoute ou retire une rareté ; « Toutes » remet à zéro
  const t = pill.dataset.tier;
  let ch = combatTiersChoisis() || new Set();
  if(t === 'tous') ch = new Set();
  else if(ch.has(t)) ch.delete(t); else ch.add(t);
  const ordre = ['legendaire', 'epique', 'rare', 'peucommun', 'commun'];
  combatFilterTier = ch.size ? ordre.filter(x => ch.has(x)).join(',') : 'tous';
  document.querySelectorAll('#combatFilters .filter-pill').forEach(p => {
    const on = combatFilterTier === 'tous' ? p.dataset.tier === 'tous' : ch.has(p.dataset.tier);
    p.classList.toggle('active', on); p.setAttribute('aria-pressed', on ? 'true' : 'false');
  });
  renderCombatGrid();""")
# sur téléphone, la pastille de chaque tuile compte aussi la Commune du jour et les résultats à voir
s = rep(s, "    const n = defis(j.id);\n    return `<button type=\"button\" class=\"qg-choix-jeu\"",
           "    const n = defis(j.id) + (qgRaisons || []).filter(r => r.jeu === j.carte && !r.defi).reduce((a, r) => a + (r.n || 0), 0);   // patch361\n    return `<button type=\"button\" class=\"qg-choix-jeu\"")
s = rep(s, "${n ? `<i class=\"qg-choix-pastille\" aria-label=\"${n} défi${n > 1 ? 's' : ''}\">${n}</i>` : ''}",
           "${n ? `<i class=\"qg-choix-pastille\" aria-label=\"${n} à voir\">${n}</i>` : ''}")
F.write_text(s, encoding='utf-8')

C = pathlib.Path('style.css'); c = C.read_text(encoding='utf-8')
assert 'patch361' not in c
c += """
/* patch361 : QG, pourquoi la pastille */
.qg-raisons{ max-width:860px; margin:0 0 14px; padding:10px 14px; border-radius:12px; font-size:.88rem; color:#DCE6F2;
  background:rgba(229,72,77,.08); border:1px solid rgba(229,72,77,.35); }
.qg-raisons[hidden]{ display:none; }
.qg-raisons-t{ display:flex; align-items:center; gap:8px; font-size:.9rem; color:#fff; }
.qg-raisons-t::before{ content:''; width:9px; height:9px; border-radius:50%; background:#E5484D; flex:none; }
.qg-raisons ul{ margin:6px 0 0; padding-left:18px; }
.qg-raisons li{ margin:2px 0; }
.qg-pastille{ display:inline-block; width:9px; height:9px; margin-left:8px; border-radius:50%; background:#E5484D; vertical-align:3px;
  box-shadow:0 0 0 3px rgba(229,72,77,.2); }
"""
C.write_text(c, encoding='utf-8')
print('patch361 appliqué')
