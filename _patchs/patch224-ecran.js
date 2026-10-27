// patch224 : notifications par département
function ncDepDe(code){ const e = collectionMap.get(code) || othersMap.get(code); return e && e.dept ? String(e.dept) : ''; }
const ncDepNom = (d) => `${DEPT_NAMES[d] || d} (${d})`;
function ncResumeDep(p){
  const pl = (n, m) => `<b>${n} ${m}${n > 1 ? 's' : ''}</b>`;
  const a = p.alerte_dep.length, sd = p.sourdine_dep.length, sc = p.sourdine.length;
  if(!a && !sd && !sc) return '🔕 Sourdine et alertes par département';
  return (a ? `⚡ ${pl(a, 'département')} dès la 1re attaque` : '') + (a && (sd || sc) ? '<br>' : '')
    + (sd || sc ? `🔕 ${[sd ? pl(sd, 'département') : '', sc ? pl(sc, 'commune') : ''].filter(Boolean).join(' · ')} en sourdine` : '');
}
function ncMuetChoix(code){
  const e = collectionMap.get(code) || othersMap.get(code), d = ncDepDe(code);
  return `<div class="nc-muet-choix"><p>Ne plus être prévenu des attaques…</p>
    <button type="button" data-nc-muet-ok="${echapperTexte(code)}"><b>à ${echapperTexte(e ? e.nom : code)}</b><small>Seulement cette commune</small></button>
    ${d ? `<button type="button" data-nc-muet-dep="${echapperTexte(d)}"><b>dans tout le département</b><small>${echapperTexte(ncDepNom(d))} : toutes mes communes</small></button>` : ''}</div>`;
}
function ncDepProps(){
  const p = ncPrefs();
  const norm = (x) => String(x).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[-']/g, ' ');
  const q = norm((NC.depQ || '').trim());
  if(!q) return '';
  const cle = NC.depListe === 'alerte' ? 'alerte_dep' : 'sourdine_dep';
  const l = Object.keys(DEPT_NAMES).filter(d => d !== '975' && (d.toLowerCase().startsWith(q) || norm(DEPT_NAMES[d]).includes(q))).slice(0, 6);
  if(!l.length) return '<div class="nc-s-props"><div class="nc-s-prop"><span>Aucun département trouvé</span></div></div>';
  return `<div class="nc-s-props">${l.map(d => {
    const deja = p[cle].includes(d);
    return `<div class="nc-s-prop${deja ? ' deja' : ''}"><span><span class="nc-s-num">${d}</span>${echapperTexte(DEPT_NAMES[d])}${deja ? '<small>déjà dans la liste</small>' : ''}</span>`
      + `<button type="button"${deja ? ' disabled' : ` data-nc-dep="${NC.depListe}|${d}|1"`}>${deja ? '✓' : 'Ajouter'}</button></div>`;
  }).join('')}</div>`;
}
function ncSaisie(e){
  if(e.target.id !== 'ncDepQ') return;
  NC.depQ = e.target.value;
  const z = document.getElementById('ncDepProps');
  if(z) z.innerHTML = ncDepProps();
}
function ncRendreSourdine(el){
  const p = ncPrefs(), off = !NC.prefsDispo;
  el.setAttribute('aria-label', 'Par département');
  const ligneDep = (d, liste) => `<div class="nc-s-ligne"><span><b>${echapperTexte(ncDepNom(d))}</b><small>${liste === 'alerte' ? 'Prévenu dès le 1er round, quelle que soit la rareté' : 'Toutes tes communes du département'}</small></span>`
    + `<button type="button"${liste === 'alerte' ? ' class="retirer"' : ''} data-nc-dep="${liste}|${echapperTexte(d)}|0">${liste === 'alerte' ? 'Retirer' : 'Réactiver'}</button></div>`;
  const sec = (liste, titre) => `<div class="nc-s-sec"><p>${titre}</p>${off ? '' : `<button type="button" data-nc-dep-ajout="${liste}">${NC.depListe === liste ? 'Fermer' : '+ Ajouter'}</button>`}</div>`;
  const cherche = (liste) => NC.depListe === liste && !off
    ? `<div class="nc-s-cherche"><input type="search" id="ncDepQ" placeholder="Nom ou numéro du département" autocomplete="off" value="${echapperTexte(NC.depQ || '')}" aria-label="Chercher un département"></div><div id="ncDepProps">${ncDepProps()}</div>` : '';
  const liste = (cle, l) => p[cle].length ? p[cle].map(d => ligneDep(d, l)).join('') : (NC.depListe === l ? '' : '<p class="nc-vide">Aucun département.</p>');
  el.innerHTML = `<div class="nc-tete"><button type="button" class="nc-retour" data-nc="reglages" aria-label="Retour">←</button><h2>Par département</h2>
      <button type="button" class="nc-x" data-nc="fermer" aria-label="Fermer">✕</button></div>
    <div class="nc-corps"><p class="nc-r-intro">${off ? 'Les réglages arrivent très bientôt.' : 'Choisis, département par département, quand être prévenu des attaques contre tes communes, dans le jeu et sur ton téléphone.'}</p>
      ${sec('alerte', '⚡ Prévenir dès la 1re attaque')}${cherche('alerte')}${liste('alerte_dep', 'alerte')}
      ${sec('sourdine', '🔕 En sourdine')}${cherche('sourdine')}${liste('sourdine_dep', 'sourdine')}
      <div class="nc-s-sec"><p>🔕 Communes en sourdine</p></div>
      ${p.sourdine.length ? p.sourdine.map(code => {
        const e = collectionMap.get(code) || othersMap.get(code);
        return `<div class="nc-s-ligne"><span><b>${echapperTexte(e ? e.nom : code)}</b><small>${echapperTexte(e ? (DEPT_NAMES[e.dept] || e.dept) : '')}</small></span><button type="button" data-nc-demuet="${echapperTexte(code)}">Réactiver</button></div>`;
      }).join('') : '<p class="nc-vide">Aucune commune. Touche 🔕 sur une attaque dans la cloche pour en ajouter une.</p>'}</div>`;
  const i = el.querySelector('#ncDepQ');
  if(i && NC.depFocus){ NC.depFocus = false; i.focus(); }
}
