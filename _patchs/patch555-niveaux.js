
// ---------- patch555 (s3-87) : améliorer les bâtiments (niveaux 2 et 3) ----------
// Une ligne sous chaque bâtiment de QG › Bâtiments (points de niveau, gain du niveau suivant, « Améliorer · prix »),
// puis une fenêtre de confirmation. Les niveaux viennent de mes_batiments_niveaux() ; l'achat de batiment_ameliorer().
var BT_NIV = null, btNivEnVol = false;
async function btNivCharger(){
  try{
    const { data, error } = await sb.rpc('mes_batiments_niveaux');
    BT_NIV = error ? null : data;
  }catch(e){ BT_NIV = null; }
  try{ renderBatimentsBloc(); }catch(e){}
}
function btNiv(type, code){
  if(!BT_NIV || !BT_NIV.ouvertes) return null;
  const R = (BT_NIV.regles || {})[type];
  const e = (BT_NIV.liste || []).find(x => x.type === type && String(x.code) === String(code));
  if(!R || !e) return null;
  const n = Math.max(1, Math.min(3, Number(e.niveau) || 1));
  return { ...e, n, R, val: R.val[n - 1], suiv: n < 3 ? R.val[n] : null, prix: n < 3 ? R.prix[n - 1] : null };
}
const BTN_NOMS = { fonderie: 'la Fonderie', banque: 'la Banque', radar: 'le Radar', artillerie: 'l’Artillerie', forteresse: 'la Forteresse' };
function btNivGain(type, e){
  if(type === 'fonderie') return `réserve <b>+${e.suiv - e.val}</b>`;
  if(type === 'banque') return `réserve <b>${e.suiv}</b>`;
  if(type === 'radar') return `voit à <b>${e.suiv} km</b>`;
  if(type === 'artillerie') return `portée <b>${e.suiv} km</b>`;
  return `appui à <b>${e.suiv} km</b>`;
}
function btNivUnite(type){
  return { fonderie: 'réserve en plus', banque: 'réserve', radar: 'km de vue', artillerie: 'km de portée', forteresse: 'km d’appui' }[type] || '';
}
function btNivHeure(iso){ const d = new Date(iso); return `${d.getHours()} h ${String(d.getMinutes()).padStart(2, '0')}`; }
function btNivPied(type, code){
  const e = btNiv(type, code);
  if(!e || !e.actif) return '';
  const pts = `<span class="bn-pts" aria-label="Niveau ${e.n} sur 3">${[1, 2, 3].map(i => `<i class="${i <= e.n ? 'p' : ''}"></i>`).join('')}</span>`;
  if(e.vise) return `<div class="bn-pied">${pts}<div class="bn-tx">Niveau ${e.vise} prêt à <b>${btNivHeure(e.pret_le)}</b></div><em class="bn-cours">⏳ Chantier</em></div>`;
  if(e.n >= 3) return `<div class="bn-pied">${pts}<div class="bn-tx">Niveau maximum</div><em class="bn-max">✓ Max</em></div>`;
  return `<div class="bn-pied">${pts}<div class="bn-tx">Niv. ${e.n + 1} : ${btNivGain(type, e)}</div>
    <button type="button" class="bn-am" data-bt-amelio="${type}|${echapperTexte(code)}">Améliorer · ${e.prix} ${ICONE_LINGOT}</button></div>`;
}
let btNivIcones = null;
function btNivTypeDe(ligne){
  if(ligne.classList.contains('banque') || ligne.classList.contains('bq-haut')) return 'banque';
  const ic = ligne.querySelector('.btl-ic');
  if(!ic) return null;
  if(ic.classList.contains('rd-ic')) return 'radar';
  if(!btNivIcones){
    btNivIcones = {};
    const t = document.createElement('span');
    for(const [k, v] of [['fonderie', ICONE_FONDERIE], ['forteresse', ICONE_FORTERESSE], ['radar', ICONE_RADAR], ['artillerie', typeof ICONE_ARTILLERIE !== 'undefined' ? ICONE_ARTILLERIE : ''], ['banque', ICONE_BANQUE]]){ t.innerHTML = v; btNivIcones[k] = t.innerHTML; }
  }
  const h = ic.innerHTML;
  return Object.keys(btNivIcones).find(k => btNivIcones[k] && btNivIcones[k] === h) || null;
}
function btNivDecorer(){
  if(!BT_NIV || !BT_NIV.ouvertes) return;
  document.querySelectorAll('#batimentsBloc .btl, #batimentsBloc .bq-haut, #panel-batiments .btl, #panel-batiments .bq-haut').forEach(l => {
    if(l.dataset.bn) return;
    l.dataset.bn = '1';
    const nom = l.querySelector('.btl-nom[data-voir-carte]');
    const type = btNivTypeDe(l);
    if(!nom || !type) return;
    const code = nom.dataset.voirCarte, e = btNiv(type, code);
    if(!e) return;
    if(e.n >= 2) nom.insertAdjacentHTML('beforeend', `<span class="bn-badge">Niv. ${e.n}</span>`);
    const pied = btNivPied(type, code);
    if(!pied) return;
    if(l.classList.contains('bq-haut')) l.insertAdjacentHTML('afterend', pied.replace('class="bn-pied"', 'class="bn-pied bn-banque"'));
    else { l.classList.add('bn-niv'); l.insertAdjacentHTML('beforeend', pied); }
  });
}
{
  const f = window.renderBatimentsBloc;
  if(typeof f === 'function') window.renderBatimentsBloc = function(){ const r = f.apply(this, arguments); try{ btNivDecorer(); }catch(e){} return r; };
}
function btNivFermer(){ document.getElementById('bnFeuille')?.remove(); }
function btNivOuvrir(type, code){
  const e = btNiv(type, code);
  if(!e || e.n >= 3 || e.vise) return;
  const b = (BATIMENTS && [BATIMENTS.banque, BATIMENTS.radar, BATIMENTS.artillerie, ...(BATIMENTS.fonderies || []), ...(typeof mesForteresses === 'function' ? mesForteresses() : [])]
    .find(x => x && String(x.code) === String(code))) || {};
  const nom = b.nom ? `${b.nom}${b.dept ? ` (${b.dept})` : ''}` : code;
  const fmt = (v) => type === 'fonderie' ? '+' + v : String(v);
  const a = Math.floor(lingotsActuels()), manque = Math.max(0, e.prix - a);
  const h = Number(BT_NIV.heures) || 6, pts = Number(BT_NIV.points) || 20;
  btNivFermer();
  document.body.insertAdjacentHTML('beforeend', `<div class="bn-fond" id="bnFeuille"><div class="bn-voile" data-bn-x></div>
    <div class="bn-f" role="dialog" aria-modal="true" aria-labelledby="bnTitre"><span class="bn-po" aria-hidden="true"></span>
      <button type="button" class="bn-x" data-bn-x aria-label="Fermer">✕</button>
      <h3 id="bnTitre">Améliorer ${BTN_NOMS[type] || 'le bâtiment'}</h3><p class="bn-sous">${echapperTexte(nom)}</p>
      <div class="bn-trois">${[1, 2, 3].map(i => `<div class="${i === e.n ? 'act' : i === e.n + 1 ? 'vise' : ''}">Niveau ${i}<b>${fmt(e.R.val[i - 1])}</b>${btNivUnite(type)}</div>`).join('')}</div>
      <ul>
        <li>Coût : <b>${e.prix} lingots</b> (tu en as ${a}).</li>
        <li><b>${h} h de chantier</b> : ${type === 'fonderie' ? 'elle continue de produire' : 'il continue de fonctionner à son niveau actuel'} pendant les travaux.</li>
        <li>Si la commune est prise, ${BTN_NOMS[type] || 'le bâtiment'} est perdu${type === 'radar' ? '' : 'e'} <b>avec ses niveaux</b>.</li>
        <li>+${pts} au classement par niveau.</li>
      </ul>
      <button type="button" class="bn-go" data-bn-go="${type}|${echapperTexte(code)}" ${manque ? 'disabled' : ''}>${manque ? `Il te manque ${manque} lingot${manque > 1 ? 's' : ''}` : `Améliorer · ${e.prix} ${ICONE_LINGOT}`}</button>
    </div></div>`);
  requestAnimationFrame(() => document.getElementById('bnFeuille')?.classList.add('ouvert'));
}
document.addEventListener('click', async (ev) => {
  const am = ev.target.closest('[data-bt-amelio]');
  if(am){ const [t, ...c] = am.dataset.btAmelio.split('|'); btNivOuvrir(t, c.join('|')); return; }
  if(ev.target.closest('[data-bn-x]')){ btNivFermer(); return; }
  const go = ev.target.closest('[data-bn-go]');
  if(go && !btNivEnVol){
    const [t, ...c] = go.dataset.bnGo.split('|');
    btNivEnVol = true; go.disabled = true;
    const { data, error } = await sb.rpc('batiment_ameliorer', { p_code: c.join('|'), p_type: t });
    btNivEnVol = false;
    if(error){ go.disabled = false; notifier({ type: 'erreur', titre: 'Amélioration', texte: messageLisible(error.message) }); return; }
    btNivFermer();
    notifier({ type: 'succes', titre: 'Amélioration lancée', texte: `Niveau ${data && data.niveau} prêt à ${btNivHeure(data && data.pret_le)}.` });
    try{ await chargerBatiments(); }catch(e){}
  }
});
document.addEventListener('keydown', (e) => { if(e.key === 'Escape') btNivFermer(); });
