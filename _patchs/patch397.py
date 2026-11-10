# patch397 (10/11/2026) : les bâtiments et la garnison sur les cartes des communes (Oshannir, 9/11),
# dans la place libre de la carte : cartes du Combat (ce que le joueur voit déjà sur la carte de France)
# (les cartes de ma collection, 4 par ligne sur téléphone, n'ont pas la place).
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'
# les pastilles
rep(A, """let BATIMENTS_CARTE = new Map();   // code -> { fonderie: { moi, pret }, forteresse: { moi, pret } }""",
"""let BATIMENTS_CARTE = new Map();   // code -> { fonderie: { moi, pret }, forteresse: { moi, pret } }
// patch397 : bâtiments et garnison sur les cartes ; GN_VUES = communes vues en garnison (Combat)
const GN_VUES = new Set();
const MBT_NOM = { forteresse: 'Forteresse', fonderie: 'Fonderie', banque: 'Banque', centre: 'Centre de recherche', radar: 'Radar' };
function btPucesHtml(code){
  code = String(code);
  const bt = BATIMENTS_CARTE.get(code) || {}, out = [];
  const g = typeof garnisonsMoi !== 'undefined' ? garnisonsMoi.get(code) : null;
  if(g) out.push(`<span class="mbt mbt-g" title="Ta garnison : ${Number(g.energie) || 0} / 10">${ICONE_BOUCLIER}<b>Garnison ${Number(g.energie) || 0}/10</b></span>`);
  else if(GN_VUES.has(code)) out.push(`<span class="mbt mbt-g" title="En garnison : une victoire sur deux annulée">${ICONE_BOUCLIER}<b>Garnison</b></span>`);
  const ico = { forteresse: ICONE_FORTERESSE, fonderie: ICONE_FONDERIE, banque: ICONE_BANQUE, centre: ICONE_CENTRE, radar: ICONE_RADAR };
  for(const t of ['forteresse', 'fonderie', 'banque', 'centre', 'radar']){
    if(!bt[t]) continue;
    out.push(`<span class="mbt${bt[t].moi ? ' moi' : ''}${bt[t].pret ? '' : ' chantier'}" title="${MBT_NOM[t]}${bt[t].moi ? ' (à toi)' : ''}${bt[t].pret ? '' : ', en construction'}">${ico[t]}<b>${t === 'centre' ? 'Centre' : MBT_NOM[t]}</b></span>`);
  }
  return out.join('');
}
function majMiniBt(){
  for(const el of document.querySelectorAll('.mini-bt[data-bt]')){
    const h = btPucesHtml(el.dataset.bt);
    if(el._h !== h){ el.innerHTML = h; el._h = h; }
  }
}""")
# miniTerra : la place libre, quand on la demande (e.bt)
rep(A, """        ${e.rank ? `<span class="mini-num">n° ${Number(e.rank).toLocaleString('fr-FR')}<span class="mini-total"> / ${Number(e.tierSize).toLocaleString('fr-FR')}</span></span>` : ''}
        <span class="mini-rarete">${e.tier.label}${e.auroreS1""",
"""        ${e.rank ? `<span class="mini-num">n° ${Number(e.rank).toLocaleString('fr-FR')}<span class="mini-total"> / ${Number(e.tierSize).toLocaleString('fr-FR')}</span></span>` : ''}
        ${e.bt ? `<div class="mini-bt" data-bt="${echapperTexte(e.code)}">${btPucesHtml(e.code)}</div>` : ''}
        <span class="mini-rarete">${e.tier.label}${e.auroreS1""")
# les cartes du Combat
rep(A, """      aurore: au ? 1 : 0, skin: sk && skinConnu(sk) ? sk : undefined });
    let bouton;""", """      aurore: au ? 1 : 0, skin: sk && skinConnu(sk) ? sk : undefined, bt: true });   // patch397
    let bouton;""")
# les garnisons des cibles affichées : demandées avec les chances
rep(A, """  const voulue = intensiteChoisie;
  chancesEnVol = true;
  try{
    const { data, error } = await sb.rpc('apercu_attaques',""",
"""  const voulue = intensiteChoisie;
  chancesEnVol = true;
  if(SAISON2) sb.rpc('garnisons_visibles', { p_codes: codes }).then(({ data, error }) => {   // patch397
    if(error || !Array.isArray(data)) return;
    for(const r of data) GN_VUES.add(String(r.commune_code));
    majMiniBt();
  }, () => {});
  try{
    const { data, error } = await sb.rpc('apercu_attaques',""")
# rafraîchir quand les bâtiments ou mes garnisons arrivent
rep(A, """    BATIMENTS_CARTE = carte;
    renderBatimentsBloc();""", """    BATIMENTS_CARTE = carte;
    majMiniBt();   // patch397
    renderBatimentsBloc();""")
rep(A, """  renderGarnisons();
  if(typeof canvasActif === 'function' && canvasActif()) demanderDessin();   // patch395 : les boucliers de la carte""",
"""  renderGarnisons();
  if(typeof canvasActif === 'function' && canvasActif()) demanderDessin();   // patch395 : les boucliers de la carte
  majMiniBt();   // patch397""")
rep('style.css', "/* patch396 : le fil de la roue */",
"""/* patch397 : bâtiments et garnison sur les cartes */
.mini-bt{ display:flex; flex-wrap:wrap; align-items:center; gap:3px; margin-top:auto; padding-top:4px; }
.mini-bt:empty{ display:none; }
.mini-bt:not(:empty) + .mini-rarete{ margin-top:4px; }
.mbt{ display:inline-flex; align-items:center; gap:3px; height:19px; margin:0; padding:0 6px 0 4px; box-sizing:border-box; max-width:100%;
  border-radius:6px; background:#2A1A0C; color:#FFB347; box-shadow:inset 0 0 0 1.2px rgba(255,179,71,.55); }
.mbt svg{ width:12px; height:12px; flex:none; }
.mbt b{ font-size:.6rem; font-weight:800; line-height:1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.mbt.moi{ color:#FFD35A; box-shadow:inset 0 0 0 1.5px #F0B429; }
.mbt.chantier{ opacity:.55; }
.mbt.mbt-g{ background:#0C3024; color:#2BD48B; box-shadow:inset 0 0 0 1.2px rgba(43,212,139,.65); }
/* patch396 : le fil de la roue */""")
print('patch397 ok')
