
// ---------- patch405 : le siège (saison 3, s3-7) ----------
// Allumé par le serveur (siege_actif) ; « ?siege=test » l'allume dans l'interface seulement (banc, aperçu).
var SIEGE = false, sgLu = false;
var SG = { code: null, ap: null, n: 5, envoi: false, dernier: null, err: '' };
var sgMenaces = [], sgMes = [];
const SG_TEST = (() => {
  try{
    if(/[?&]siege=test\b/.test(location.search)) sessionStorage.setItem('tf-siege-test', '1');
    return sessionStorage.getItem('tf-siege-test') === '1';
  }catch(e){ return false; }
})();
async function sgChargerActif(){
  sgLu = true;
  let actif = false;
  try{ const { data, error } = await sb.rpc('siege_actif'); actif = !error && data === true; }catch(e){ actif = false; }
  SIEGE = actif || SG_TEST;
  document.body.classList.toggle('siege-on', SIEGE);
  if(!SIEGE) return;
  const sub = document.querySelector('#panel-defense > .sub');
  if(sub) sub.textContent = 'Quand un joueur assiège une de tes communes, renforce-la : chaque énergie fait reculer sa jauge, avec 20 % de bonus à domicile. Une garnison ou un bâtiment rend le siège long.';
  loadMenaces();
  sgChargerMes();
}
const sgNb = (x) => Math.round(Number(x) || 0).toLocaleString('fr-FR');
const sgTier = (id) => TIERS.find(t => t.id === id) || TIERS[TIERS.length - 1];
function sgDuree(min){
  const m = Math.round(Number(min) || 0);
  if(m < 60) return m + ' min';
  const h = Math.floor(m / 60), r = m % 60;
  return h + ' h' + (r ? ' ' + String(r).padStart(2, '0') : '');
}
function sgEnergie(){ return energieEtat ? Math.floor(Number(energieEtat.energie) || 0) : null; }
function sgBarre(degats, res, petit){
  const p = res > 0 ? Math.max(0, Math.min(100, 100 * degats / res)) : 0;
  return `<div class="sg-barre${petit ? ' petit' : ''}" role="img" aria-label="Jauge du siège : ${sgNb(degats)} sur ${sgNb(res)}"><i class="sg-rempli${p >= 66 ? ' chaud' : ''}" style="width:${p.toFixed(1)}%"></i></div>`;
}
function sgVoileEl(){ return document.getElementById('sgVoile'); }
async function ouvrirSiege(code){
  let v = sgVoileEl();
  if(!v){
    v = document.createElement('div');
    v.className = 'pc-voile sg-voile'; v.id = 'sgVoile'; v.hidden = true;
    v.innerHTML = '<div class="pc-boite sg-boite" id="sgBoite" role="dialog" aria-modal="true" aria-label="Le siège"></div>';
    v.addEventListener('click', sgClic);
    document.body.appendChild(v);
  }
  if(typeof fermerPanneau === 'function') try{ fermerPanneau(); }catch(e){}
  SG = { code, ap: null, n: 5, envoi: false, dernier: null, err: '' };
  sgRendre();
  v.hidden = false;
  requestAnimationFrame(() => v.classList.add('ouvert'));
  if(energieEtat === null || energieEtat === undefined) majEnergie();
  await sgCharger(true);
}
function sgFermer(){
  const v = sgVoileEl();
  if(!v || v.hidden) return;
  v.classList.remove('ouvert');
  setTimeout(() => { v.hidden = true; }, 180);
  SG.code = null;
}
async function sgCharger(choisirN){
  const code = SG.code;
  const { data, error } = await sb.rpc('siege_apercu', { p_code: code });
  if(SG.code !== code) return;
  if(error){ SG.err = messageLisible(error.message); sgRendre(); return; }
  SG.ap = data || null; SG.err = '';
  if(choisirN && SG.ap) SG.n = sgSuggestion();
  sgRendre();
}
function sgReste(){
  const a = SG.ap; if(!a) return 0;
  const s = a.siege;
  const res = Number(s ? s.resistance : a.resistance) || 0, deg = Number(s ? s.degats : 0) || 0;
  const bcl = Number(s ? s.bouclier : a.bouclier) || 0;
  const mult = Number(a.mult) || 1;
  return Math.max(1, Math.ceil(Math.max(0, res - deg + bcl) / (10 * mult)));
}
function sgSuggestion(){
  const a = SG.ap; if(!a) return 5;
  const e = sgEnergie(), neuf = !a.siege;
  const max = Math.max(1, Math.min(Number(a.vague_max) || 60, e === null ? 99 : e - (neuf ? Number(a.pose) || 2 : 0)));
  return Math.max(1, Math.min(sgReste(), max));
}
function sgRendre(){
  const b = document.getElementById('sgBoite');
  if(!b) return;
  const a = SG.ap, code = SG.code;
  const o = othersMap.get(code) || {};
  const tier = sgTier(a ? a.tier : (o.tier && o.tier.id));
  const nom = echapperTexte(o.nom || (a && a.nom) || code);
  const dept = o.dept || '';
  const proprio = echapperTexte((a && a.proprio_pseudo) || o.pseudo || 'un joueur');
  const tete = `<div class="pc-poignee"></div>
    <div class="sg-k"><i class="sg-rar" style="--c:${tier.color}"></i>${tier.label}</div>
    <div class="pc-titre sg-nom">${nom}</div>
    <p class="pc-txt sg-sous">${dept ? echapperTexte(DEPT_NAMES[dept] || dept) + ' (' + echapperTexte(dept) + ') · ' : ''}tenue par <b>${proprio}</b></p>`;
  if(SG.err && !a){ b.innerHTML = tete + `<p class="pc-txt">${echapperTexte(SG.err)}</p><div class="pc-sec"><button type="button" data-sg="fermer">Fermer</button></div>`; return; }
  if(!a){ b.innerHTML = tete + '<p class="pc-txt">Préparation du siège…</p>'; return; }
  const s = a.siege && !a.siege.resultat ? a.siege : null;
  const res = Number(s ? s.resistance : a.resistance) || 0;
  const mult = Number(a.mult) || 1;
  const bcl = Number(s ? s.bouclier : a.bouclier) || 0;
  const long = s ? !!s.long : !!a.long;
  const dureeLong = Number(a.duree_long_min) || 60;
  const rythmeE = res > 0 ? (res / (dureeLong / 60)) / (10 * mult) : 0;
  const e = sgEnergie();
  const pose = s ? 0 : (Number(a.pose) || 2);
  const n = Math.max(1, Math.min(Number(a.vague_max) || 60, SG.n));
  const cout = n + pose;
  const manque = e !== null && cout > e;
  const multPct = Math.round((mult - 1) * 100);
  const proches = Number(a.proches) || 0;
  const procheTxt = proches <= 0 ? 'aucune à moins de 20 km' : `<b>${proches}</b> à moins de 20 km`;
  const multTxt = multPct ? `<b class="${multPct > 0 ? 'sg-plus' : 'sg-moins'}">${multPct > 0 ? '+' : '−'}${Math.abs(multPct)} % de dégâts</b>` : 'dégâts normaux';
  // les trois chiffres
  const etat = long
    ? `<b class="sg-long">Long</b><span>${s && s.rythme_h ? '≈ ' + (Math.round(rythmeE * 10) / 10).toString().replace('.', ',') + ' ⚡ par heure au plus' : sgDuree(dureeLong) + ' au plus tôt'}</span>`
    : `<b class="sg-eclair">Éclair</b><span>${a.eclair_min ? 'au moins ' + sgDuree(a.eclair_min) : 'tant que ' + proprio + ' ne défend pas'}</span>`;
  const chiffres = `<div class="pc-chiffres sg-chiffres">
      <div><b>${sgNb(res)}</b><span>points de résistance</span></div>
      <div>${etat}</div>
      <div><b>≈ ${sgReste()}</b><span>énergie ${s ? 'pour finir' : 'en tout'}</span></div></div>`;
  // la jauge du siège en cours
  let jauge = '';
  if(s){
    const att = Number(s.attente) || 0;
    const tombe = s.tombe_le ? new Date(s.tombe_le).getTime() - Date.now() : 0;
    jauge = `<div class="sg-jauge">
        ${bcl > 0 ? `<div class="sg-bcl"><span>Bouclier de la garnison</span><b>${sgNb(bcl)} points à casser d'abord</b></div>` : ''}
        ${sgBarre(Number(s.degats) || 0, res)}
        <div class="sg-jl"><span><b>${sgNb(s.degats)}</b> / ${sgNb(res)}</span><span>${att > 0 ? `<b>${att} ⚡</b> en attente, elles partent toutes seules` : s.defendu ? `${proprio} a renforcé` : 'pas encore défendue'}</span></div>
        ${tombe > 0 ? `<p class="sg-tombe">Sans nouvelle vague, le siège tombe dans ${formatDuree(tombe)}.</p>` : ''}
      </div>`;
  }
  const lignes = `<div class="sg-lignes">
      <div class="sg-l"><span>Tes communes proches</span><span>${procheTxt} · ${multTxt}</span></div>
      <div class="sg-l"><span>Garnison</span><span>${bcl > 0 ? `bouclier de <b>${sgNb(bcl)}</b> points` : 'aucune'}</span></div>
      <div class="sg-l"><span>Bâtiment</span><span>${a.forteresse ? 'Forteresse : <b>résistance × 1,5</b>' : 'aucun'}</span></div>
      ${long ? '' : `<div class="sg-l"><span>S'il renforce</span><span>siège long : <b>${sgDuree(dureeLong)}</b> au plus tôt</span></div>`}
    </div>`;
  // le choix de l'énergie
  const choix = `<div class="sg-energie">
      <span class="sg-el">Énergie de la vague</span>
      <div class="sg-pas"><button type="button" data-sg-n="-1" aria-label="Une de moins"${n <= 1 ? ' disabled' : ''}>−</button><b>${n}</b><button type="button" data-sg-n="1" aria-label="Une de plus">+</button></div>
      <div class="sg-vite">${[5, 10, 20].map(x => `<button type="button" data-sg-v="${x}"${x === n ? ' class="on"' : ''}>${x}</button>`).join('')}<button type="button" data-sg-v="fin"${n === sgReste() ? ' class="on"' : ''}>Juste assez</button></div>
      ${e !== null ? `<small>Tu as <b>${e} ⚡</b></small>` : ''}
    </div>`;
  const bloque = a.bouclier_jusqua ? `Protégée par un bouclier · ${formatDuree(new Date(a.bouclier_jusqua).getTime() - Date.now())}`
    : (!s && a.immunite_jusqua) ? `Vient de changer de main · ${formatDuree(new Date(a.immunite_jusqua).getTime() - Date.now())}`
    : (!s && long && Number(a.longs) >= Number(a.places)) ? `Tes ${a.places} sièges longs sont pris`
    : '';
  const bouton = bloque ? `<button type="button" class="pc-go" disabled>${bloque}</button>`
    : `<button type="button" class="pc-go" data-sg="go"${SG.envoi || manque ? ' disabled' : ''}>${SG.envoi ? 'Un instant…' : manque ? `Il te faut ${cout} ⚡` : s ? `Envoyer la vague · ${n} ⚡` : `Poser le siège · ${cout} ⚡`}</button>`;
  const avert = s ? '' : `<p class="sg-note"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 8a6 6 0 1112 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10 21h4"/></svg><span>${proprio} est prévenu dès que tu poses le siège (${pose} ⚡). Il peut renforcer, ou laisser filer ${nom}.</span></p>`;
  const autres = Number(a.autres) > 0 ? `<p class="sg-course">⚔️ ${a.autres > 1 ? a.autres + ' autres joueurs assiègent' : 'Un autre joueur assiège'} aussi ${nom} : le premier qui remplit sa jauge la prend.</p>` : '';
  const places = `<p class="sg-places">Sièges longs : <b>${sgNb(a.longs)} / ${sgNb(a.places)}</b> · les sièges éclair ne comptent pas</p>`;
  const retour = SG.dernier ? `<p class="sg-retour" role="status">${SG.dernier}</p>` : '';
  const sec = `<div class="pc-sec">${s ? '<button type="button" data-sg="abandon">Abandonner le siège</button>' : '<span></span>'}<button type="button" data-sg="fermer">Fermer</button></div>`;
  b.innerHTML = tete + chiffres + jauge + retour + lignes + avert + autres + choix + bouton + places + (SG.err ? `<p class="sg-err">${echapperTexte(SG.err)}</p>` : '') + sec;
}
async function sgClic(ev){
  const v = sgVoileEl();
  if(ev.target === v){ sgFermer(); return; }
  const t = ev.target.closest('[data-sg],[data-sg-n],[data-sg-v]');
  if(!t || t.disabled) return;
  if(t.dataset.sgN){ SG.n = Math.max(1, SG.n + Number(t.dataset.sgN)); sgRendre(); return; }
  if(t.dataset.sgV){ SG.n = t.dataset.sgV === 'fin' ? sgReste() : Number(t.dataset.sgV); sgRendre(); return; }
  const act = t.dataset.sg;
  if(act === 'fermer'){ sgFermer(); return; }
  if(act === 'abandon'){
    if(!confirm('Abandonner ce siège ? L\'énergie en attente te revient, le reste est perdu.')) return;
    const { error } = await sb.rpc('siege_abandonner', { p_code: SG.code });
    if(error){ SG.err = messageLisible(error.message); sgRendre(); return; }
    notifier({ type: 'info', titre: 'Siège abandonné' });
    majEnergie(); sgChargerMes(); sgFermer();
    return;
  }
  if(act === 'go') await sgEnvoyer();
}
async function sgEnvoyer(){
  if(SG.envoi || !SG.ap) return;
  const code = SG.code, avant = SG.ap.siege ? Number(SG.ap.siege.degats) || 0 : 0;
  SG.envoi = true; SG.err = ''; sgRendre();
  const { data, error } = await sb.rpc('siege_vague', { p_code: code, p_energie: Math.max(1, SG.n) });
  SG.envoi = false;
  if(SG.code !== code) return;
  if(error){ SG.err = messageLisible(error.message); sgRendre(); return; }
  const s = data || {};
  majEnergie();
  sgChargerMes();
  if(s.resultat === 'conquise'){
    sgFermer();
    const o = othersMap.get(code);
    notifier({ type: 'succes', titre: `${o ? o.nom : 'La commune'} est à toi !`, texte: 'Ton siège a rempli la jauge.' });
    try{ await Promise.all([loadMyCollection(), loadOthersPossessions()]); renderMapOverlay(); }catch(e){}
    return;
  }
  const gagne = Math.max(0, (Number(s.degats) || 0) - avant);
  SG.dernier = gagne > 0 ? `+${sgNb(gagne)} points sur la jauge${Number(s.attente) > 0 ? ` · ${s.attente} ⚡ en attente` : ''}`
    : Number(s.attente) > 0 ? `Siège long : tes ${s.attente} ⚡ attendent leur tour, elles partiront toutes seules.` : 'La vague s\'est brisée sur le bouclier.';
  SG.ap.siege = s;
  await sgCharger(false);
}

// Défendre : les sièges contre moi
async function loadMenacesSiege(){
  const { data, error } = await sb.rpc('sieges_contre_moi_v2');
  if(error){ console.error(error); return; }
  sgMenaces = Array.isArray(data) ? data : [];
  renderMenacesSiege();
  if(typeof mfoRendre === 'function') mfoRendre();
}
function sgLaisses(){ try{ return new Set(JSON.parse(localStorage.getItem('tf-siege-laisses') || '[]')); }catch(e){ return new Set(); } }
function renderMenacesSiege(){
  const laisses = sgLaisses();
  const vus = sgMenaces.filter(m => !laisses.has(m.id));
  const nb = vus.length;
  const badge = document.getElementById('combatBadge');
  if(badge){ badge.hidden = nb === 0; badge.textContent = nb; majBadgePlus(); badge.title = nb > 1 ? `${nb} communes assiégées` : 'Une commune assiégée'; }
  document.querySelectorAll('[data-badge-defense]').forEach(x => { x.hidden = nb === 0; x.textContent = nb; });
  const bloc = document.getElementById('combatMenaces');
  const liste = document.getElementById('combatMenacesListe');
  if(!bloc || !liste) return;
  bloc.hidden = sgMenaces.length === 0;
  const h2 = bloc.querySelector('h2'); if(h2) h2.textContent = 'Tes communes assiégées';
  if(bloc.hidden){ liste.innerHTML = ''; return; }
  liste.innerHTML = sgMenaces.map(m => {
    const tier = sgTier(m.tier), res = Number(m.resistance) || 0, deg = Number(m.degats) || 0;
    const tombe = m.tombe_le ? new Date(m.tombe_le).getTime() - Date.now() : 0;
    const laisse = laisses.has(m.id);
    const p = res ? Math.round(100 * deg / res) : 0;
    const etat = m.long ? `<b class="sg-long">Siège long</b> · au plus ${sgNb(m.rythme_h)} points par heure` : `<b class="sg-eclair">Siège éclair</b> · elle peut tomber d'un coup`;
    return `<div class="sg-def${laisse ? ' laisse' : ''}${p >= 66 ? ' chaud' : ''}">
      <div class="sg-def-h"><i class="sg-rar" style="--c:${tier.color}"></i><button type="button" class="sg-def-nom" data-voir-carte="${echapperTexte(m.commune)}">${echapperTexte(m.nom)}</button>${badgeDept(m.dept)}<span class="sg-def-qui">assiégée par <b>${echapperTexte(m.attaquant_pseudo || 'un joueur')}</b></span></div>
      ${Number(m.bouclier) > 0 ? `<div class="sg-bcl"><span>Ta garnison</span><b>${sgNb(m.bouclier)} points de bouclier</b></div>` : ''}
      ${sgBarre(deg, res)}
      <div class="sg-jl"><span><b>${sgNb(deg)}</b> / ${sgNb(res)} · ${p} %</span><span>${etat}</span></div>
      ${tombe > 0 ? `<p class="sg-tombe">Sans nouvelle vague, son siège tombe dans ${formatDuree(tombe)}${m.defendu || Number(m.bouclier) > 0 ? ' : défense réussie pour toi' : ''}.</p>` : ''}
      <div class="sg-def-a">
        <span class="sg-renf-l">Renforcer</span>${[2, 5, 10].map(x => `<button type="button" class="sg-renf" data-sg-renf="${x}" data-code="${echapperTexte(m.commune)}" data-att="${echapperTexte(m.attaquant)}">${x} ⚡</button>`).join('')}
      </div>
      <div class="sg-def-b">
        ${Number(m.garnison) > 0 ? '' : `<button type="button" class="sg-gn" data-sg-gn="${echapperTexte(m.commune)}">Garnison · 5 ⚡</button>`}
        <button type="button" class="sg-laisser" data-sg-laisser="${m.id}">${laisse ? 'Suivre à nouveau' : 'Laisser filer'}</button>
      </div></div>`;
  }).join('');
}
document.addEventListener('click', async (ev) => {
  const t = ev.target.closest('[data-sg-renf],[data-sg-gn],[data-sg-laisser],[data-sg-ouvrir]');
  if(!t || t.disabled) return;
  if(t.dataset.sgOuvrir){ ouvrirSiege(t.dataset.sgOuvrir); return; }
  if(t.dataset.sgLaisser){
    const s = sgLaisses(), id = Number(t.dataset.sgLaisser);
    if(s.has(id)) s.delete(id); else s.add(id);
    try{ localStorage.setItem('tf-siege-laisses', JSON.stringify([...s].slice(-60))); }catch(e){}
    renderMenacesSiege();
    return;
  }
  if(t.dataset.sgGn){
    t.disabled = true;
    await garnisonAction(t.dataset.sgGn, 5);
    await loadMenacesSiege();
    return;
  }
  if(t.dataset.sgRenf){
    t.disabled = true;
    const { data, error } = await sb.rpc('siege_renforcer', { p_code: t.dataset.code, p_attaquant: t.dataset.att, p_energie: Number(t.dataset.sgRenf) });
    if(error){ notifier({ type: 'erreur', titre: 'Renfort', texte: messageLisible(error.message) }); t.disabled = false; return; }
    const m = sgMenaces.find(x => x.commune === t.dataset.code && x.attaquant === t.dataset.att);
    const recul = m && data ? Math.max(0, (Number(m.degats) || 0) - (Number(data.degats) || 0)) : 0;
    notifier({ type: 'succes', titre: 'Renfort envoyé', texte: recul > 0 ? `La jauge recule de ${sgNb(recul)} points. Le siège est long maintenant.` : 'Le siège est long maintenant.' });
    majEnergie();
    await loadMenacesSiege();
  }
});

// Attaquer : mes sièges en cours
async function sgChargerMes(){
  if(!SIEGE) return;
  const { data, error } = await sb.rpc('mes_sieges');
  if(error) return;
  sgMes = Array.isArray(data) ? data : [];
  renderMesSieges();
  if(typeof mfoRendre === 'function') mfoRendre();
}
function renderMesSieges(){
  const grid = document.getElementById('combatGrid');
  if(!grid) return;
  let el = document.getElementById('sgMesSieges');
  if(!el){ el = document.createElement('div'); el.id = 'sgMesSieges'; el.className = 'sg-mes'; grid.parentNode.insertBefore(el, grid); }
  el.hidden = !SIEGE || !sgMes.length;
  if(el.hidden){ el.innerHTML = ''; return; }
  const longs = sgMes.filter(s => s.long).length;
  el.innerHTML = `<h2>Mes sièges <small>${longs} long${longs > 1 ? 's' : ''} · ${sgMes.length - longs} éclair</small></h2>` + sgMes.map(s => {
    const tier = sgTier(s.tier), res = Number(s.resistance) || 0, deg = Number(s.degats) || 0;
    return `<button type="button" class="sg-mes-l" data-sg-ouvrir="${echapperTexte(s.commune)}">
      <span class="sg-mes-t"><i class="sg-rar" style="--c:${tier.color}"></i><b>${echapperTexte(s.nom || s.commune)}</b><small>${echapperTexte(s.proprio_pseudo || '')}${s.long ? ' · long' : ' · éclair'}${Number(s.attente) > 0 ? ` · ${s.attente} ⚡ en attente` : ''}</small></span>
      ${sgBarre(deg, res, true)}<span class="sg-mes-p">${res ? Math.round(100 * deg / res) : 0} %</span></button>`;
  }).join('');
}

// Mon front : « À défendre maintenant » et « Mes sièges » à partir des sièges
function sgMfoDanger(){
  const laisses = sgLaisses();
  const l = sgMenaces.filter(m => !laisses.has(m.id))
    .sort((a, b) => (Number(b.degats) / Math.max(1, Number(b.resistance))) - (Number(a.degats) / Math.max(1, Number(a.resistance))));
  if(!l.length) return `<div class="mfo-t mfo-calme"><i>✓</i><span>Aucune de tes communes n'est assiégée.</span></div>`;
  return `<div class="mfo-t mfo-alerte"><div class="mfo-h"><span>⚠ À défendre maintenant</span><button type="button" class="mfo-lien" data-mfo="defendre">Tout voir${l.length > 3 ? ` (${l.length})` : ''} ›</button></div>`
    + l.slice(0, 3).map(m => {
      const p = Number(m.resistance) ? Math.round(100 * Number(m.degats) / Number(m.resistance)) : 0;
      return `<div class="mfo-l"><div><b>${echapperTexte(m.nom || m.commune)}</b> · ${sgTier(m.tier).label.toLowerCase()}<small>${echapperTexte(m.attaquant_pseudo || 'un joueur')} · jauge à ${p} % · ${m.long ? 'siège long' : 'siège éclair'}</small>${sgBarre(Number(m.degats) || 0, Number(m.resistance) || 0, true)}</div>`
        + `<button type="button" class="mfo-btn mfo-rouge" data-mfo="defendre">Renforcer</button></div>`;
    }).join('') + '</div>';
}
function sgMfoAttaques(){
  const l = sgMes;
  const longs = l.filter(s => s.long).length;
  return `<div class="mfo-t"><div class="mfo-h"><span>⚔ Mes sièges${l.length ? ` · ${longs} long${longs > 1 ? 's' : ''}` : ''}</span><button type="button" class="mfo-lien" data-mfo="attaquer">Assiéger ›</button></div>`
    + (l.length ? l.slice(0, 4).map(s => {
      const p = Number(s.resistance) ? Math.round(100 * Number(s.degats) / Number(s.resistance)) : 0;
      return `<div class="mfo-l"><div><b>${echapperTexte(s.nom || s.commune)}</b><small>${p} % · ${s.long ? 'long' : 'éclair'}${Number(s.attente) > 0 ? ` · ${s.attente} ⚡ en attente` : ''}</small>${sgBarre(Number(s.degats) || 0, Number(s.resistance) || 0, true)}</div>`
        + `<button type="button" class="mfo-btn mfo-rouge" data-sg-ouvrir="${echapperTexte(s.commune)}">Continuer</button></div>`;
    }).join('') + (l.length > 4 ? `<p class="mfo-p">+ ${l.length - 4} autre${l.length - 4 > 1 ? 's' : ''} dans Attaquer</p>` : '')
      : '<p class="mfo-p">Aucun siège en cours. <button type="button" class="mfo-lien" data-mfo="attaquer">Choisir une cible ›</button></p>') + '</div>';
}
