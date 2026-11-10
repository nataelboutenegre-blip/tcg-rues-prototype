
// ---------- patch407 : le paquet Terra suisse (saison 3, s3-8) ----------
// Éteint tant que SUISSE vaut false (patch330, ?suisse=test pour essayer) : le jeu d'aujourd'hui ne change pas.
// Fonctions déclarées (et pas des const) : elles servent dans des gabarits plus haut dans le fichier.
var tpPaquetPaye = null;   // pays du paquet payé, le temps de l'ouvrir
function estSuisseCode(code){ return /^CH\d/.test(String(code || '')); }
function chCroix(){ return '<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M13 5h6v8h8v6h-8v8h-6v-8H5v-6h8z" fill="#fff"/></svg>'; }
function chBadge(mini){ return `<span class="ch-badge${mini ? ' ch-mini' : ''}" title="Commune suisse">${chCroix()}${mini ? '' : '<b>Suisse</b>'}</span>`; }
function tpDrapeau(pays){
  return pays === 'CH'
    ? '<svg class="tp-drap tp-drap-ch" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="4" fill="#DA291C"/><path d="M13 6h6v7h7v6h-7v7h-6v-7H6v-6h7z" fill="#fff"/></svg>'
    : '<svg class="tp-drap" viewBox="0 0 3 2" aria-hidden="true"><rect width="1" height="2" fill="#2B5BD7"/><rect x="1" width="1" height="2" fill="#fff"/><rect x="2" width="1" height="2" fill="#E5484D"/></svg>';
}
function tpLire(cle){ try{ return localStorage.getItem(cle); }catch(e){ return null; } }
function tpEcrire(cle, v){ try{ localStorage.setItem(cle, v); }catch(e){} }
function tpPays(){ return SUISSE && tpLire('tf-terra-pays') === 'CH' ? 'CH' : 'FR'; }
function tcPays(){ return SUISSE && tpLire('tf-coll-pays') === 'CH' ? 'CH' : 'FR'; }
function tpNouveauVu(){ return tpLire('tf-terra-ch-vu') === '1'; }
// les arguments de terra_ouvrir_paquet : p_pays seulement pour la Suisse (un serveur sans s3-8 reste servi pour la France)
function tpArgs(args){
  const p = enTerra() ? tpPays() : 'FR';
  tpPaquetPaye = p;
  if(p !== 'CH') return args;
  tpEcrire('tf-terra-ch-vu', '1');
  return Object.assign({}, args, { p_pays: 'CH' });
}
function tpHabiller(pack, pays){
  if(!pack || !SUISSE || pays !== 'CH') return;
  pack.classList.add('paquet-ch');
  const et = pack.querySelector('.paquet-etiquette');
  if(et) et.innerHTML = tpDrapeau('CH') + '<span class="paquet-titre">Paquet Suisse</span>';
  const bd = pack.querySelector('.paquet-bande');
  if(bd) bd.textContent = '5 communes de Suisse';
}
function tpSelecteurHtml(pays, coll){
  const at = coll ? 'data-tcp' : 'data-tpp';
  return `<div class="tp-pays${coll ? ' tp-coll-pays' : ''}" role="group" aria-label="${coll ? 'Quel pays' : 'Quel paquet'}">`
    + `<button type="button" ${at}="FR" class="${pays === 'FR' ? 'on' : ''}" aria-pressed="${pays === 'FR'}">${tpDrapeau('FR')}France</button>`
    + `<button type="button" ${at}="CH" class="tp-b-ch${pays === 'CH' ? ' on' : ''}" aria-pressed="${pays === 'CH'}">${tpDrapeau('CH')}Suisse${coll || tpNouveauVu() ? '' : '<small>Nouveau</small>'}</button></div>`;
}
// Tirage : le choix au-dessus des boutons (Terra seulement), appelé à chaque renderPackStatus
function tpRendre(){
  const panel = document.getElementById('panel-tirage');
  if(!panel) return;
  let z = document.getElementById('tpPays');
  const sub = panel.querySelector('.sub-long'), court = panel.querySelector('.sub-court .que-terra');
  if(!SUISSE || !enTerra()){
    if(z) z.remove();
    if(sub && sub.dataset.tpAvant){ sub.textContent = sub.dataset.tpAvant; delete sub.dataset.tpAvant; }
    if(court && court.dataset.tpAvant){ court.textContent = court.dataset.tpAvant; delete court.dataset.tpAvant; }
    return;
  }
  if(sub && !sub.dataset.tpAvant){ sub.dataset.tpAvant = sub.textContent; sub.textContent = 'Chaque carte tirée est une vraie commune, de France ou de Suisse, à sa vraie position géographique. Elle n’appartient qu’à toi tant que tu la gardes. Clique sur le paquet pour le déchirer.'; }
  if(court && !court.dataset.tpAvant){ court.dataset.tpAvant = court.textContent; court.textContent = 'Chaque carte est une vraie commune de France ou de Suisse.'; }
  const btns = panel.querySelector('.pack-buttons');
  if(!btns) return;
  if(!z){ z = document.createElement('div'); z.id = 'tpPays'; btns.parentNode.insertBefore(z, btns); }
  const p = tpPays(), etat = p + (tpNouveauVu() ? 'v' : '');
  if(z.dataset.etat === etat) return;
  z.dataset.etat = etat;
  z.innerHTML = tpSelecteurHtml(p, false)
    + `<p class="tp-note">${p === 'CH' ? '5 vraies communes suisses. ' : ''}Mêmes jetons et même prix pour les deux paquets ; les raretés tombent aussi souvent dans les deux.</p>`;
}
document.addEventListener('click', (ev) => {
  const b = ev.target.closest('[data-tpp]');
  if(!b) return;
  tpEcrire('tf-terra-pays', b.dataset.tpp === 'CH' ? 'CH' : 'FR');
  tpRendre();
  const zone = document.getElementById('packZone');
  if(zone && !paquetEnCours && zone.querySelector('.paquet[data-pret]')){ afficherPaquetPret('gratuit'); renderPackStatus(); }
});

// Collection : le pays choisi
function tcVueCollection(){
  if(!SUISSE) return terraCollection;
  const ch = tcPays() === 'CH';
  return new Map([...terraCollection].filter(([, e]) => estSuisseCode(e.code) === ch));
}
function tcChoisirPays(p){
  tpEcrire('tf-coll-pays', p === 'CH' ? 'CH' : 'FR');
  terraFiltre = 'tous'; terraLimite = 120;
  renderCollectionTerra();
}
function tcTotauxSuisse(){
  const t = { legendaire: 27, epique: 218, rare: 652, peucommun: 953, commun: 260 };   // s3-5 : 2 110 communes
  for(const e of terraCollection.values()) if(estSuisseCode(e.code) && e.tierSize) t[e.tier.id] = Number(e.tierSize);
  const r = {};
  for(const k in t) r[k] = { total: t[k] };
  return r;
}
function tcTotalSuisse(){ return Object.values(tcTotauxSuisse()).reduce((s, l) => s + l.total, 0); }
function tcDoublonsVue(vue){ let n = 0; for(const e of vue.values()) n += Math.max(0, libresTerra(e)); return n; }
function tcCompteurHtml(totalFrance){
  let ch = 0;
  for(const e of terraCollection.values()) if(estSuisseCode(e.code)) ch++;
  if(tcPays() === 'CH')
    return `<span class="coll-compteur"><b>${fmtNombre(ch)}</b> / ${fmtNombre(tcTotalSuisse())} communes suisses <span class="om-compteur">· <b>${fmtNombre(collectionMetro() + collectionOutremer().n)}</b> en France</span></span>`;
  return compteurCollectionHtml(totalFrance).replace(/<\/span>$/, ` <span class="om-compteur">· <b>${fmtNombre(ch)}</b> / ${fmtNombre(tcTotalSuisse())} en Suisse</span></span>`);
}
