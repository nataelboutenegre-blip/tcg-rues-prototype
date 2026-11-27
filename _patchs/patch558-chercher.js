
// patch558 : chercher une commune sur les cartes (idée de Saaslil) : en tête du menu ☰ de la carte du Front,
// et une loupe sur Terra › Ma France. Même recherche que l'accueil, avec la position pour centrer la carte.
const CHC = { jeton: 0, minuteur: null };
function chcDep(d){ return DEPT_NAMES[d] || CANTONS[d] || PROVINCES_BE[d] || CANTONS_LU[d] || d; }
function chcHtml(id){
  return `<div class="chc"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>`
    + `<input type="search" id="${id}" class="chc-champ" placeholder="Nom d’une commune…" autocomplete="off" enterkeyhint="search" aria-label="Chercher une commune"></div>`
    + `<ul class="chc-res" hidden></ul>`;
}
// filtre : ce que la carte sait montrer ; choisir : ce qu'on fait de la commune
function chcArmer(champ, filtre, choisir){
  const ul = champ.parentElement.nextElementSibling;
  let L = [];
  const lancer = async () => {
    const q = champ.value, j = ++CHC.jeton;
    if(q.trim().length < 2){ ul.hidden = true; ul.innerHTML = ''; return; }
    let r = [];
    try{ const x = await sb.rpc('carte_chercher', { p_texte: q }); r = Array.isArray(x.data) ? x.data : []; }catch(e){}
    if(j !== CHC.jeton) return;
    L = r.filter(filtre);
    ul.innerHTML = L.length ? L.map((c, i) => {
      const t = TIERS.find(x => x.id === c.tier) || TIERS[TIERS.length - 1];
      return `<li><button type="button" data-chc="${i}"><b>${echapperTexte(c.nom)}</b><span class="chc-d">${echapperTexte(chcDep(c.dept))}${/^\d/.test(c.dept) ? ' (' + echapperTexte(c.dept) + ')' : ''}</span><span class="chc-t ${t.id}">${echapperTexte(t.label)}</span></button></li>`;
    }).join('') : '<li class="chc-vide">Aucune commune de ce nom.</li>';
    ul.hidden = false;
  };
  champ.addEventListener('input', () => { clearTimeout(CHC.minuteur); CHC.minuteur = setTimeout(lancer, 220); });
  champ.addEventListener('keydown', (e) => { if(e.key === 'Enter' && L.length){ e.preventDefault(); champ.blur(); choisir(L[0]); } });
  ul.addEventListener('click', (e) => {
    const b = e.target.closest('[data-chc]');
    if(!b) return;
    const c = L[Number(b.dataset.chc)];
    if(c){ champ.blur(); choisir(c); }
  });
}
function chcVider(champ){
  if(!champ) return;
  champ.value = '';
  const ul = champ.parentElement.nextElementSibling;
  if(ul){ ul.hidden = true; ul.innerHTML = ''; }
}

// Front : la carte se centre, l'anneau de visée se pose, la fiche s'ouvre si la commune a un propriétaire
function chcFront(c){
  mfeFermer();
  chcVider(document.getElementById('chcFront'));
  setTimeout(() => {
    voirCommuneSurCarte({ code: c.code, lat: c.lat, lon: c.lon });
    if(estOutremerCode(c.code)) return;
    setTimeout(() => {
      if(!collectionMap.has(c.code) && !othersMap.has(c.code)) return;
      const p = project(c.lat, c.lon), ech = echelleCarte();
      try{ ouvrirPanneau(c.code, p.x * MAP_W * ech * mapZoom + mapPanX, p.y * MAP_H * ech * mapZoom + mapPanY); }catch(e){}
    }, 140);
  }, 200);
}
function chcFrontInstaller(){
  const f = document.getElementById('mapFeuille');
  const corps = f && f.querySelector('[data-mfe-vue="affichage"]');
  if(!corps || corps.querySelector('#chcFront')) return;
  const bloc = document.createElement('div');
  bloc.className = 'chc-bloc';
  bloc.innerHTML = '<h4>Chercher une commune</h4>' + chcHtml('chcFront');
  corps.prepend(bloc);
  chcArmer(bloc.querySelector('#chcFront'), (c) => c.lat != null && c.lon != null, chcFront);
}
(function(){
  const avant = mfeFeuille;
  mfeFeuille = function(){ const f = avant.apply(this, arguments); chcFrontInstaller(); return f; };
})();
// la loupe sur le bouton ☰
(function(){
  const avant = mfeInstaller;
  mfeInstaller = function(){
    const r = avant.apply(this, arguments);
    const b = document.getElementById('mapAffBtn');
    if(b && !b.querySelector('.chc-loupe')){
      b.insertAdjacentHTML('afterbegin', '<svg class="chc-loupe" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>');
      b.setAttribute('aria-label', 'Chercher une commune et affichage de la carte');
    }
    return r;
  };
})();

// Terra › Ma France : la loupe ouvre un champ sur la carte ; la carte zoome sur la commune et sa bulle s'ouvre
function chcTerraOuvrir(){
  const cadre = document.getElementById('mfCadre');
  if(!cadre) return;
  let p = cadre.querySelector('.chc-mf');
  if(!p){
    p = document.createElement('div');
    p.className = 'chc-mf';
    p.innerHTML = chcHtml('chcTerra') + '<button type="button" class="chc-x" data-chc-fermer aria-label="Fermer la recherche">✕</button>';
    cadre.appendChild(p);
    chcArmer(p.querySelector('#chcTerra'), (c) => c.lat != null && !!DEPT_NAMES[c.dept] && !estOutremerCode(c.code), chcTerra);
    p.querySelector('[data-chc-fermer]').addEventListener('click', chcTerraFermer);
  }
  p.hidden = false;
  const champ = p.querySelector('#chcTerra');
  if(champ) champ.focus();
}
function chcTerraFermer(){
  const p = document.querySelector('#mfCadre .chc-mf');
  if(!p) return;
  chcVider(p.querySelector('#chcTerra'));
  p.hidden = true;
}
function chcTerra(c){
  chcTerraFermer();
  if(!MF.larg) return;
  const pt = project(c.lat, c.lon), bx = pt.x * MAP_W, by = pt.y * MAP_H;
  if(MF.figer){   // la vue départements ne dessine pas les communes : on la quitte
    MF.figer = false; try{ localStorage.setItem('tf-mf-figer', '0'); }catch(e){}
    const fb = document.querySelector('[data-mf="figer"]'); if(fb){ fb.classList.remove('on'); fb.setAttribute('aria-pressed', 'false'); }
  }
  MF.k = Math.max(MF.k, 9);
  const S = mfEchelle();
  MF.ox = MF.larg / 2 - bx * S - MF.baseX * MF.k;
  MF.oy = MF.haut / 2 - by * S - MF.baseY * MF.k;
  mfLimiter();
  MF.dernierZoom = performance.now();
  MF.bulle = { code: c.code, dep: c.dept, chemin: null };
  majBulleMF();
  mfPlanifier();
  // le contour arrive avec le département : on entoure la commune dès qu'il est là
  let n = 0;
  const attendre = () => {
    if(!MF.bulle || MF.bulle.code !== c.code) return;
    const cc = CONTOURS.get(c.dept);
    if(cc && cc !== 'erreur' && cc[c.code]){ MF.bulle.chemin = cheminCommuneCanvas(c.code, cc[c.code]); mfPlanifier(); return; }
    if(++n < 40) setTimeout(attendre, 150);
  };
  attendre();
}
document.addEventListener('click', (e) => {
  if(e.target.closest('[data-mf="chercher"]')){ e.stopPropagation(); chcTerraOuvrir(); }
}, true);
