
// ---------- patch458 : clans S3 — défense alliée, classement des 5 meilleurs, objectif de la semaine (s3-28) ----------
// Tout dépend du serveur (config_jeu 'clans_s3' : defense_allie, classement_top5, objectif). Éteint → rien ne change.
var CL_TOP5 = false;
function clModeMaj(rows){
  if(!Array.isArray(rows) || !rows.length) return;
  CL_TOP5 = rows.some(r => r && r.mode === 'top5');
  document.body.classList.toggle('top5-on', CL_TOP5);
}
function clScoreUnite(){ return CL_TOP5 ? 'points' : '/ membre'; }
function clScoreUniteLong(actifs){ return CL_TOP5 ? 'points' : (actifs ? 'par membre actif' : 'par membre'); }
function clNoteClassement(){
  return CL_TOP5 ? 'Les communes du Front des 5 meilleurs membres actifs (jeu ouvert dans les 7 derniers jours), additionnées : une recrue ne fait jamais baisser son clan.'
    : 'Moyenne de communes du Front par membre actif (jeu ouvert dans les 7 derniers jours) : un gros clan n\'a pas d\'avantage.';
}
const CL_CALC_CLANS_TOP5 = `<p class="cl-calc-txt">On additionne les communes du Front des <b>5 meilleurs membres actifs</b> du clan (jeu ouvert dans les 7 derniers jours). Une recrue ne fait jamais baisser le score : au pire elle ne compte pas, au mieux elle prend la place du 5e. Un membre absent ne compte pas. Un clan est classé à partir de <b>3 membres</b>.</p>`;
function clScoreClan(membres, act){
  return (membres || []).filter(m => !act || membreActif(act.get(m.id))).map(m => Number(m.communes) || 0)
    .sort((a, b) => b - a).slice(0, 5).reduce((s, n) => s + n, 0);
}

// ---- 1. Défense alliée : Défendre › « Ton clan est assiégé » et Mon front
var SGA = { liste: [], ouvert: false };
async function sgaCharger(){
  if(typeof SIEGE === 'undefined' || !SIEGE || !CLANS) return;
  const [r, o] = await Promise.all([sb.rpc('clan_sieges_allies'), sb.rpc('defense_allie_ouverte')]);
  if(r.error) return;   // serveur pas encore lancé : rien
  SGA.liste = Array.isArray(r.data) ? r.data : [];
  document.body.classList.toggle('allie-on', !o.error && o.data === true);
  sgaRendre();
  try{ if(typeof mfoRendre === 'function') mfoRendre(); }catch(e){}
}
function sgaReste(m){ return Math.max(0, (Number(m.allie_max) || 60) - (Number(m.mon_renfort) || 0)); }
function sgaRendre(){
  const ref = document.getElementById('combatMenaces');
  if(!ref) return;
  let el = document.getElementById('combatAllies');
  if(!el){ el = document.createElement('div'); el.id = 'combatAllies'; el.className = 'menaces sga'; ref.after(el); }
  el.hidden = !SGA.liste.length;
  if(el.hidden){ el.innerHTML = ''; return; }
  const max = Number(SGA.liste[0].allie_max) || 60;
  el.innerHTML = `<h2>Ton clan est assiégé</h2>
    <p class="sga-note">Renforce la commune d’un membre : chaque énergie fait reculer la jauge de l’attaquant (× 1 pour toi, × 1,2 pour le propriétaire). Au plus <b>${max} ⚡</b> par siège pour toi ; la défense réussie compte pour lui.</p>`
    + SGA.liste.map(m => {
      const tier = sgTier(m.tier), res = Number(m.resistance) || 0, deg = Number(m.degats) || 0;
      const p = res ? Math.round(100 * deg / res) : 0, reste = sgaReste(m), mon = Number(m.mon_renfort) || 0, tous = Number(m.allies) || 0;
      const etat = m.long ? `<b class="sg-long">Siège long</b>` : `<b class="sg-eclair">Siège éclair</b> · elle peut tomber d'un coup`;
      const vals = [5, 10, 20].filter(x => x <= reste);
      if(reste > 0 && !vals.includes(reste) && reste < 20) vals.push(reste);
      return `<div class="sg-def sga-c${p >= 66 ? ' chaud' : ''}">
        <div class="sg-def-h"><i class="sg-rar" style="--c:${tier.color}"></i><button type="button" class="sg-def-nom" data-voir-carte="${echapperTexte(m.commune)}">${echapperTexte(m.nom)}</button>${badgeDept(m.dept)}<span class="sg-def-qui">à <b>${echapperTexte(m.proprio_pseudo || 'un membre')}</b> · assiégée par <b>${echapperTexte(m.attaquant_pseudo || 'un joueur')}</b></span></div>
        ${Number(m.bouclier) > 0 ? `<div class="sg-bcl"><span>Sa garnison</span><b>${sgNb(m.bouclier)} points de bouclier</b></div>` : ''}
        ${sgBarre(deg, res)}
        <div class="sg-jl"><span><b>${sgNb(deg)}</b> / ${sgNb(res)} · ${p} %</span><span>${etat}</span></div>
        <div class="sga-aide"><span>Ton aide <b>${mon}</b> / ${Number(m.allie_max) || 60} ⚡</span>${tous > mon ? `<span>Tout le clan : <b>${tous}</b> ⚡</span>` : ''}</div>
        <div class="sg-def-a">${reste > 0 ? `<span class="sg-renf-l">Renforcer</span>${vals.map(x => `<button type="button" class="sg-renf" data-sga-renf="${x}" data-code="${echapperTexte(m.commune)}" data-att="${echapperTexte(m.attaquant)}">${x} ⚡</button>`).join('')}`
          : '<span class="sga-max">✓ Tu as mis le maximum sur ce siège.</span>'}</div></div>`;
    }).join('');
}
function sgaMfo(){
  if(!SGA.liste.length) return '';
  const l = SGA.liste;
  return `<div class="mfo-t mfo-alerte sga-mfo"><div class="mfo-h"><span>🛡️ Ton clan a besoin d’aide</span><button type="button" class="mfo-lien" data-mfo="defendre">Tout voir${l.length > 2 ? ` (${l.length})` : ''} ›</button></div>`
    + l.slice(0, 2).map(m => {
      const p = Number(m.resistance) ? Math.round(100 * Number(m.degats) / Number(m.resistance)) : 0;
      return `<div class="mfo-l"><div><b>${echapperTexte(m.nom || m.commune)}</b> · à ${echapperTexte(m.proprio_pseudo || 'un membre')}<small>${echapperTexte(m.attaquant_pseudo || 'un joueur')} · jauge à ${p} % · ton aide ${Number(m.mon_renfort) || 0} / ${Number(m.allie_max) || 60}</small></div>`
        + `${sgaReste(m) > 0 ? '<button type="button" class="mfo-btn mfo-rouge" data-mfo="defendre">Aider</button>' : '<span class="mfo-ok">✓</span>'}</div>`;
    }).join('') + '</div>';
}
document.addEventListener('click', async (ev) => {
  const t = ev.target.closest('[data-sga-renf]');
  if(!t || t.disabled) return;
  t.disabled = true;
  const m = SGA.liste.find(x => x.commune === t.dataset.code && x.attaquant === t.dataset.att);
  const { data, error } = await sb.rpc('siege_renforcer', { p_code: t.dataset.code, p_attaquant: t.dataset.att, p_energie: Number(t.dataset.sgaRenf) });
  if(error){ notifier({ type: 'erreur', titre: 'Renfort', texte: messageLisible(error.message) }); t.disabled = false; return; }
  const recul = m && data ? Math.max(0, (Number(m.degats) || 0) - (Number(data.degats) || 0)) : 0;
  notifier({ type: 'succes', titre: 'Renfort envoyé', texte: `${recul > 0 ? `La jauge recule de ${sgNb(recul)} points. ` : ''}${echapperTexte((m && m.proprio_pseudo) || 'Ton allié')} est prévenu.` });
  if(typeof majEnergie === 'function') majEnergie();
  await sgaCharger();
});

// ---- 3. Objectif de clan de la semaine : onglet Clan et Mon front
var OBJ = { etat: null, lu: 0, charge: null };
async function objCharger(force){
  if(!SAISON2 || !CLANS) return;
  if(OBJ.charge) return OBJ.charge;
  if(!force && Date.now() - OBJ.lu < 60e3) return;
  OBJ.charge = (async () => {
    try{
      const { data, error } = await sb.rpc('clan_objectif_etat');
      if(!error){ OBJ.etat = data; OBJ.lu = Date.now(); document.body.classList.toggle('objectif-on', !!(data && data.ouvert)); objRendre(); }
    }catch(e){}
    finally{ OBJ.charge = null; }
  })();
  return OBJ.charge;
}
function objOk(){ const e = OBJ.etat; return !!(e && e.ouvert && e.clan && e.cette); }
const OBJ_NOMS = ['Bronze', 'Argent', 'Or'];
function objGainTxt(p){ return [p.lingots ? `+${p.lingots} ${ICONE_LINGOT}` : '', p.energie ? `+${p.energie} ⚡` : ''].filter(Boolean).join(' '); }
function objDispo(s){
  if(!s || !s.participe) return null;
  const l = (s.paliers || []).filter(p => p.atteint && !p.ramasse);
  if(!l.length) return null;
  return { semaine: s.semaine, lingots: l.reduce((a, p) => a + (p.lingots || 0), 0), energie: l.reduce((a, p) => a + (p.energie || 0), 0) };
}
function objDispoTxt(d){ return [d.lingots ? `+${d.lingots} ${ICONE_LINGOT}` : '', d.energie ? `+${d.energie} ⚡` : ''].filter(Boolean).join(' '); }
function objRendre(){
  try{ if(typeof s3MajClan === 'function') s3MajClan(); }catch(e){}
  try{ if(typeof mfoRendre === 'function') mfoRendre(); }catch(e){}
}
function objHtml(){
  if(!objOk()) return '';
  const S = OBJ.etat.cette, P = S.paliers || [], top = P.length ? P[P.length - 1].seuil : 1;
  const pct = Math.min(100, 100 * S.prises / Math.max(1, top));
  const fin = Math.max(0, new Date(S.fin).getTime() - Date.now());
  const d = objDispo(S), dl = objDispo(OBJ.etat.derniere);
  const prochain = P.find(p => !p.atteint);
  const lignes = P.map((p, i) => `<div class="cob-pal${p.atteint ? ' ok' : ''}"><span class="cob-med m${i + 1}">${OBJ_NOMS[i] || 'Palier ' + (i + 1)}</span>
      <span class="cob-seuil"><b>${p.seuil}</b> commune${p.seuil > 1 ? 's' : ''}</span><span class="cob-gain">${objGainTxt(p)}</span>
      <span class="cob-etat">${p.ramasse ? '✓ ramassé' : p.atteint ? (S.participe ? 'à ramasser' : 'atteint') : ''}</span></div>`).join('');
  const membres = (S.membres || []).filter(m => m.prises || m.renforts);
  return `<div class="s3-carte cob"><h3><span class="cob-ic">🏁</span>Objectif de la semaine <small>fin dimanche à minuit · encore ${formatDuree(fin)}</small></h3>
    <p class="cob-n"><b>${S.prises}</b> commune${S.prises > 1 ? 's' : ''} prise${S.prises > 1 ? 's' : ''} par le clan${prochain ? ` · encore <b>${Math.max(0, prochain.seuil - S.prises)}</b> pour ${(OBJ_NOMS[prochain.n - 1] || 'le palier').toLowerCase()}` : ' · tous les paliers atteints'}</p>
    <div class="cob-piste"><i style="width:${pct}%"></i>${P.map((p, i) => `<span class="cob-cran${p.atteint ? ' ok' : ''}" style="left:${Math.min(100, 100 * p.seuil / Math.max(1, top))}%"></span>`).join('')}</div>
    ${lignes}
    ${d ? `<button type="button" class="bq-btn cob-ramasser" data-obj="ramasser" data-sem="${d.semaine}">Ramasser ma part · ${objDispoTxt(d)}</button>` : ''}
    ${S.participe ? '' : '<p class="cob-p">Ta part arrive dès que tu prends une commune ou que tu renforces un allié cette semaine.</p>'}
    ${dl ? `<div class="cob-avant"><span>Semaine dernière : ${OBJ.etat.derniere.prises} prises</span><button type="button" class="s3o-mini" data-obj="ramasser" data-sem="${dl.semaine}">Ramasser · ${objDispoTxt(dl)}</button></div>` : ''}
    ${membres.length ? `<p class="clan-note cob-qui">${membres.map(m => `${m.moi ? '<b>' : ''}${echapperHtml(m.pseudo || '?')}${m.moi ? '</b>' : ''} ${m.prises}${m.renforts ? ` <small>+ ${m.renforts} ⚡ d’aide</small>` : ''}`).join(' · ')}</p>` : ''}
    <p class="clan-note">Communes prises par les membres du lundi au dimanche. Seuils fixés le lundi : ${(P.map(p => p.seuil)).join(', ')} pour ${S.actifs} membres actifs. Chaque membre qui a pris une commune ou aidé un allié ramasse sa part ; il a jusqu’à la fin de la semaine suivante.</p></div>`;
}
function objMfo(){
  if(!objOk()) return '';
  const S = OBJ.etat.cette, d = objDispo(S) || objDispo(OBJ.etat.derniere);
  if(d) return `<div class="mfo-rc cob-rc"><span>🏁 Objectif du clan : palier atteint</span><button type="button" class="mfo-btn mfo-or" data-obj="ramasser" data-sem="${d.semaine}">Ramasser ${objDispoTxt(d)}</button></div>`;
  const prochain = (S.paliers || []).find(p => !p.atteint);
  if(!prochain) return `<div class="mfo-rc cob-rc"><span>🏁 Objectif du clan : or atteint ✓</span></div>`;
  return `<div class="mfo-rc cob-rc"><span>🏁 Objectif du clan : <b>${S.prises}</b> / ${prochain.seuil} pour ${(OBJ_NOMS[prochain.n - 1] || 'le palier').toLowerCase()}</span><button type="button" class="mfo-btn mfo-sec" data-s3="vers-clan">Voir ›</button></div>`;
}
document.addEventListener('click', async (ev) => {
  const b = ev.target.closest('[data-obj]');
  if(!b || b.disabled) return;
  b.disabled = true;
  const { data, error } = await sb.rpc('clan_objectif_ramasser', { p_semaine: b.dataset.sem });
  if(error){ notifier({ type: 'erreur', titre: 'Objectif du clan', texte: messageLisible(error.message) }); b.disabled = false; return; }
  OBJ.etat = data; OBJ.lu = Date.now();
  const l = Number(data.gagne_lingots) || 0, e = Number(data.gagne_energie) || 0, ep = Number(data.energie_prevue) || 0;
  notifier({ type: 'succes', titre: 'Objectif du clan', texte: `${[l ? `+${l} lingots` : '', e ? `+${e} énergie` : ''].filter(Boolean).join(' et ') || 'Ramassé'}${ep > e ? ' (réserve d’énergie au maximum)' : ''}.` });
  if(typeof majEnergie === 'function') majEnergie();
  try{ if(typeof chargerBatiments === 'function') chargerBatiments(); }catch(e2){}
  objRendre();
});
setInterval(() => { if(document.visibilityState === 'visible'){ objCharger(); } }, 120e3);
