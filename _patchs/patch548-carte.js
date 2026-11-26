
// ---------- patch548 : la carte du Territoire allégée ----------
// Au-dessus de la carte : France / Outre-mer, « ☰ » (affichage) et « 🎨 Mon territoire ».
// Les options d'affichage (couleurs, calques, cacher les autres) passent dans un panneau qui monte du bas ;
// la couleur et le motif du territoire s'ouvrent depuis la carte (et depuis le Profil), sans passer par la Boutique.
// Les éléments d'origine sont DÉPLACÉS (mêmes id, mêmes écouteurs) : rien n'est dupliqué.
function mfeInstaller(){
  const wrap = document.getElementById('mapWrap');
  if(!wrap) return;
  let barre = document.getElementById('mapBarre');
  if(!barre){
    barre = document.createElement('div');
    barre.id = 'mapBarre'; barre.className = 'map-barre';
    barre.innerHTML = `<span class="mb-zone"></span>
      <button type="button" class="mb-btn" id="mapAffBtn" aria-haspopup="dialog" aria-label="Affichage de la carte">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg><b id="mapAffNb"></b></button>
      <button type="button" class="mb-btn or" id="mapTerrBtn" aria-haspopup="dialog">🎨 Mon territoire</button>`;
    wrap.parentElement.insertBefore(barre, wrap);
    barre.querySelector('#mapAffBtn').addEventListener('click', () => mfeOuvrir('affichage'));
    barre.querySelector('#mapTerrBtn').addEventListener('click', () => mfeOuvrir('territoire'));
  }
  const zone = document.getElementById('frontZone');
  const z = barre.querySelector('.mb-zone');
  if(zone && zone.parentElement !== z) z.appendChild(zone);
  const f = mfeFeuille();
  const place = (id, cible) => { const e = document.getElementById(id), c = f.querySelector(cible); if(e && c && e.parentElement !== c) c.appendChild(e); };
  place('mapCouleurs', '[data-mfe-p="couleurs"]');
  place('mapCalques', '[data-mfe-p="calques"]');
  place('toggleOthersBtn', '[data-mfe-p="autres"]');
  const outils = document.querySelector('#panel-territoire .map-outils');
  if(outils) outils.hidden = !outils.children.length;
  mfeCompter();
}
function mfeCompter(){
  const nb = document.querySelectorAll('#mapCalques .actif').length;
  const b = document.getElementById('mapAffNb');
  if(b){ b.textContent = nb || ''; b.hidden = !nb; }
}
function mfeFeuille(){
  let f = document.getElementById('mapFeuille');
  if(f) return f;
  f = document.createElement('div');
  f.id = 'mapFeuille'; f.className = 'mfe'; f.hidden = true;
  f.innerHTML = `<div class="mfe-voile" data-mfe="fermer"></div>
    <div class="mfe-feuille" role="dialog" aria-modal="true" aria-labelledby="mfeTitre">
      <div class="mfe-tete"><span class="mfe-poignee" aria-hidden="true"></span><h3 id="mfeTitre"></h3>
        <button type="button" class="mfe-x" data-mfe="fermer" aria-label="Fermer">✕</button></div>
      <div class="mfe-corps" data-mfe-vue="affichage">
        <h4>Couleurs</h4><div data-mfe-p="couleurs"></div>
        <h4>Sur la carte</h4><div data-mfe-p="calques"></div>
        <h4>Les autres joueurs</h4><div data-mfe-p="autres"></div>
      </div>
      <div class="mfe-corps" data-mfe-vue="territoire"><div id="mfeTerr"></div></div>
    </div>`;
  document.body.appendChild(f);
  f.addEventListener('click', async (e) => {
    if(e.target.closest('[data-mfe="fermer"]')){ mfeFermer(); return; }
    if(e.target.closest('[data-calque]')) setTimeout(mfeCompter, 0);
    if(!e.target.closest('#mfeTerr')) return;
    if(e.target.closest('[data-mot="ouvrir"]')){ mfeFermer(); motOuvrir(); return; }
    const pc = e.target.closest('[data-pf="couleur"]');
    if(pc){ await choisirCouleur(pc.dataset.couleur); mfeTerrRendre(); return; }
    const dr = e.target.closest('[data-pf="dore"]');
    if(dr){
      try{ localStorage.setItem(CLE_DORE, dr.checked ? '1' : '0'); }catch(err){}
      appliquerCouleurMoi();
      try{ renderMapOverlay(); }catch(err){}
    }
  });
  document.addEventListener('keydown', (e) => { if(e.key === 'Escape' && !f.hidden) mfeFermer(); });
  return f;
}
function mfeTerrRendre(){
  const c = document.getElementById('mfeTerr');
  if(!c) return;
  c.innerHTML = `<div class="atb-bloc atb-terr">${blocCouleur()}</div>${motBlocAtelier()}`;
  const dessiner = () => { const b = c.querySelector('[data-mot-bande="moi"]'); if(b) motBande(b, MTF.moi, motMaCouleur()); };
  dessiner();
  if(!MTF.formes && MTF.ouvert !== false) motFormesCharger().then(dessiner).catch(() => {});
  if(!MTF.lu && !MTF.lecture){ MTF.lecture = motMoiCharger().then(ok => { MTF.lecture = null; if(ok && !document.getElementById('mapFeuille').hidden) mfeTerrRendre(); }); }
}
let mfeRetour = null;
function mfeOuvrir(vue){
  mfeInstaller();
  const f = mfeFeuille();
  f.querySelectorAll('[data-mfe-vue]').forEach(v => { v.hidden = v.dataset.mfeVue !== vue; });
  f.querySelector('#mfeTitre').textContent = vue === 'territoire' ? '🎨 Mon territoire' : 'Affichage de la carte';
  if(vue === 'territoire') mfeTerrRendre();
  mfeRetour = document.activeElement;
  f.hidden = false;
  requestAnimationFrame(() => f.classList.add('ouvert'));
  const x = f.querySelector('.mfe-x'); if(x) x.focus({ preventScroll: true });
}
function mfeFermer(){
  const f = document.getElementById('mapFeuille');
  if(!f || f.hidden) return;
  f.classList.remove('ouvert');
  setTimeout(() => { f.hidden = true; }, 180);
  mfeCompter();
  if(mfeRetour && mfeRetour.focus) try{ mfeRetour.focus({ preventScroll: true }); }catch(e){}
}
document.addEventListener('click', (e) => {   // Profil : « Ma couleur et mon motif »
  if(e.target.closest('[data-pf="mon-territoire"]')) mfeOuvrir('territoire');
});
// les éléments de la carte sont (re)créés par ces fonctions : on les range juste après
for(const nom of ['rendreCalques', 'couleursRendre', 'majZoneFront']){
  const f = window[nom];
  if(typeof f === 'function') window[nom] = function(){ const r = f.apply(this, arguments); try{ mfeInstaller(); }catch(e){} return r; };
}
setTimeout(mfeInstaller, 0);
function blocTerrLien(){   // Profil : un lien vers « Mon territoire » au lieu du nuancier en double
  const c = motMaCouleur();
  const nom = NOMS_COULEURS[PALETTE_TERRITOIRE.indexOf(c)] || '';
  const motif = typeof MTF !== 'undefined' && MTF.moi;
  return `<div class="pf-terr"><button type="button" class="pf-terr-lien" data-pf="mon-territoire">
      <b class="pt-pastille" style="background:${c}" aria-hidden="true"></b>
      <span><b>Ma couleur et mon motif sur la carte</b><small>${maCouleurChoisie ? 'Couleur : ' + echapperTexte(nom) : 'Couleur automatique'}${motif ? ' · motif en place' : ''}</small></span><i aria-hidden="true">›</i></button></div>`;
}
