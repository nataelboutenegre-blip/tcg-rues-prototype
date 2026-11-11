
// ---------- patch412 : « Qui possède ta commune ? » (s3-9), la fiche publique, sans compte ----------
// Sur la page d'accueil : recherche, fiche de la commune (propriétaire, depuis quand, petite carte des 12 km autour),
// « Viens la reprendre » / « Viens la conquérir », « Partager ». Adresse : terrafront.fr/?c=cognac-16.
// La commune vue est gardée (tf-cible, 3 h) : après l'inscription ou la connexion, le jeu ouvre la carte du Front dessus
// (commune tenue) ou le Tirage du Front (commune libre). Un joueur déjà connecté qui ouvre ?c= arrive aussi sur la carte.
var CP = { jeton: 0, fiche: null, minuteur: null, contours: new Map(), fait: false };
function cpE(s){ return echapperTexte(String(s == null ? '' : s)); }
function cpRefUrl(){ try{ return new URLSearchParams(location.search).get('c') || ''; }catch(e){ return ''; } }
function cpCouleur(p){
  if(!p) return null;
  if(p.couleur) return p.couleur;
  return p.h != null ? OPPONENT_COLORS[Number(p.h) % OPPONENT_COLORS.length] : null;
}
function cpDuree(iso){
  const ms = Date.now() - new Date(iso).getTime();
  if(!(ms > 0)) return 'à l’instant';
  const h = Math.floor(ms / 3600e3), j = Math.floor(h / 24);
  if(j >= 2) return `${j} jours`;
  if(j === 1) return '1 jour';
  if(h >= 1) return `${h} h`;
  return `${Math.max(1, Math.floor(ms / 60e3))} min`;
}
function cpTier(id){ return TIERS.find(t => t.id === id) || TIERS[TIERS.length - 1]; }
function cpGarder(d){
  try{ localStorage.setItem('tf-cible', JSON.stringify({ code: d.code, nom: d.nom, pris: !!d.proprio, lat: d.lat, lon: d.lon, le: Date.now() })); }catch(e){}
}

// la recherche (8 communes au plus, les plus peuplées d'abord)
async function cpChercher(q){
  const ul = document.getElementById('cpResultats');
  if(!ul) return;
  const j = ++CP.jeton;
  if(String(q).trim().length < 2){ ul.hidden = true; ul.innerHTML = ''; return; }
  let L = [];
  try{ const r = await sb.rpc('communes_publiques_chercher', { p_texte: q }); L = Array.isArray(r.data) ? r.data : []; }catch(e){}
  if(j !== CP.jeton) return;
  ul.innerHTML = L.length ? L.map(c => `<li><button type="button" data-cp-ref="${cpE(c.adresse)}"><b>${cpE(c.nom)}</b><span class="cp-r-dep">${cpE(c.dept)}</span><small>${cpE(cpTier(c.tier).label)} · ${fmtNombre(Number(c.population) || 0)} hab.</small></button></li>`).join('')
    : '<li class="cp-r-vide">Aucune commune de ce nom.</li>';
  ul.hidden = false;
}

// la fiche
async function cpOuvrir(ref, defiler){
  const f = document.getElementById('cpFiche'), ul = document.getElementById('cpResultats');
  if(!f) return;
  if(ul){ ul.hidden = true; }
  const j = ++CP.jeton;
  f.hidden = false;
  f.innerHTML = '<p class="cp-attente">Un instant…</p>';
  if(defiler){ const s = document.getElementById('lpCp'); if(s && s.scrollIntoView) s.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  let d = null;
  try{ const r = await sb.rpc('commune_publique', { p_ref: ref }); d = r.data; }catch(e){}
  if(j !== CP.jeton) return;
  if(!d){ f.innerHTML = '<p class="cp-attente">Commune introuvable : essaie avec son nom.</p>'; return; }
  CP.fiche = d;
  cpGarder(d);
  try{ history.replaceState(null, '', location.pathname + '?c=' + encodeURIComponent(d.adresse)); }catch(e){}
  f.innerHTML = cpFicheHtml(d);
  cpCarte(d);
}
function cpFicheHtml(d){
  const t = cpTier(d.tier), u = urlPhoto(d.photo), p = d.proprio, coul = cpCouleur(p);
  const qui = p
    ? `<p class="cp-qui"><i style="background:${cpE(coul)}"></i><span>Tenue par <b>${cpE(p.pseudo)}</b>${p.clan ? ` <span class="cp-clan" style="--c:${cpE(p.clan_couleur || '#4C9BE8')}" title="${cpE(p.clan_nom || '')}">${cpE(p.clan)}</span>` : ''}${d.depuis ? ` depuis ${cpDuree(d.depuis)}` : ''}</span></p>`
      + (Number(d.prises) > 1 ? `<p class="cp-prises">Prise ${Number(d.prises)} fois cette saison</p>` : '')
    : `<p class="cp-qui libre"><i></i><span><b>Personne</b> ne la tient pour l’instant.</span></p>`;
  return `<div class="cp-carte">
    <div class="cp-photo">${u ? `<img src="${cpE(u)}" alt="" decoding="async" data-onfail="1">` : ''}<span class="cp-rarete" style="--c:${t.color}">${cpE(t.label)}</span></div>
    <div class="cp-corps">
      <h3 class="cp-nom">${cpE(d.nom)} <span class="cp-dep">${cpE(d.dept)}</span></h3>
      <p class="cp-chiffres">${fmtNombre(Number(d.population) || 0)} habitants${d.rang ? ` · n° ${fmtNombre(Number(d.rang))} / ${fmtNombre(Number(d.palier_total) || 0)}` : ''}</p>
      ${qui}
      <canvas class="cp-mini" id="cpMini" aria-label="Les communes autour de ${cpE(d.nom)}"></canvas>
      <p class="cp-legende"><span><i class="cp-l-joueur"></i>tenue par un joueur</span><span><i class="cp-l-libre"></i>libre</span><span>12 km autour</span></p>
      <div class="cp-actions">
        <button type="button" class="lp-cta cp-cta" data-cp-viens>${p ? 'Viens la reprendre' : 'Viens la conquérir'}</button>
        <button type="button" class="cp-partager" data-cp-partager>Partager</button>
      </div>
      <p class="cp-sous">${p ? 'Gratuit, dans le navigateur, sans rien installer. Un bonus de débutant t’aide pendant 7 jours.' : 'Gratuit, dans le navigateur, sans rien installer. Ouvre des paquets du Front : chaque carte est une vraie commune, et elle devient à toi.'}</p>
      ${d.photo_auteur ? `<p class="cp-credit">Photo : ${cpE(d.photo_auteur)}${d.photo_licence ? ' · ' + cpE(d.photo_licence) : ''}</p>` : ''}
    </div>
  </div>`;
}

// la petite carte : la commune et ses voisines à moins de 12 km, aux couleurs de leurs propriétaires
async function cpContours(dep){
  if(CP.contours.has(dep)) return CP.contours.get(dep);
  let data = null;
  try{ const r = await fetch(`contours/${dep}.json?v=${CONTOURS_V}`, { cache: 'force-cache' }); if(r.ok) data = await r.json(); }catch(e){}
  CP.contours.set(dep, data);
  return data;
}
async function cpCarte(d){
  const cv = document.getElementById('cpMini');
  if(!cv) return;
  const voisines = new Map((d.voisines || []).map(v => [v.c, v]));
  const deps = new Set([d.dept, ...(d.voisines || []).map(v => v.d).filter(Boolean)]);
  const L = await Promise.all([...deps].map(cpContours));
  if(CP.fiche !== d || !document.body.contains(cv)) return;
  const larg = cv.clientWidth || 320, haut = Math.round(larg * 0.62);
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  cv.width = Math.round(larg * dpr); cv.height = Math.round(haut * dpr); cv.style.height = haut + 'px';
  const ctx = cv.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = '#0A1729'; ctx.fillRect(0, 0, larg, haut);
  const lat0 = Number(d.lat), lon0 = Number(d.lon), kx = 111.32 * Math.cos(lat0 * Math.PI / 180), ky = 110.57;
  const s = larg / 28;   // 28 km de large
  const P = (lon, lat) => [larg / 2 + (lon - lon0) * kx * s, haut / 2 + (lat0 - lat) * ky * s];
  let cible = null;
  for(const data of L){
    if(!data) continue;
    for(const code in data){
      const anneaux = data[code];
      const [x0, y0] = P(anneaux[0][0][0], anneaux[0][0][1]);
      if(x0 < -larg * 0.6 || x0 > larg * 1.6 || y0 < -haut * 0.6 || y0 > haut * 1.6) continue;
      const p = new Path2D();
      for(const a of anneaux){ a.forEach(([lon, lat], i) => { const [x, y] = P(lon, lat); i ? p.lineTo(x, y) : p.moveTo(x, y); }); p.closePath(); }
      if(code === d.code){ cible = p; continue; }
      const v = voisines.get(code);
      const c = v && (v.couleur || v.h != null) ? cpCouleur(v) : null;
      ctx.globalAlpha = c ? 0.82 : 1;
      ctx.fillStyle = c || (v ? '#1B3A5E' : '#132741');
      ctx.fill(p);
      ctx.globalAlpha = 1;
      ctx.strokeStyle = '#0A1729'; ctx.lineWidth = 0.7; ctx.stroke(p);
    }
  }
  if(cible){
    ctx.fillStyle = cpCouleur(d.proprio) || '#2B4E78';
    ctx.fill(cible);
    ctx.strokeStyle = '#07111F'; ctx.lineWidth = 5; ctx.stroke(cible);
    ctx.strokeStyle = '#FFFFFF'; ctx.lineWidth = 2.4; ctx.stroke(cible);
  }
  // l'échelle : 5 km
  ctx.fillStyle = 'rgba(232,238,247,.85)';
  ctx.fillRect(12, haut - 14, 5 * s, 2.5);
  ctx.font = '600 11px system-ui, sans-serif'; ctx.fillText('5 km', 12, haut - 20);
}

// « Viens la reprendre » / « Viens la conquérir » : l'inscription, la commune gardée
function cpViens(){
  if(CP.fiche) cpGarder(CP.fiche);
  quitterLanding('inscription');
}
async function cpPartager(b){
  const d = CP.fiche;
  if(!d) return;
  const url = location.origin + location.pathname + '?c=' + encodeURIComponent(d.adresse);
  const texte = d.proprio ? `${d.nom} est tenue par ${d.proprio.pseudo} sur TerraFront. Qui possède ta commune ?` : `Personne ne tient ${d.nom} sur TerraFront. Qui possède ta commune ?`;
  try{
    if(navigator.share){ await navigator.share({ title: `Qui possède ${d.nom} ?`, text: texte, url }); return; }
  }catch(e){ if(e && e.name === 'AbortError') return; }
  try{ await navigator.clipboard.writeText(url); if(b){ b.textContent = 'Lien copié'; setTimeout(() => { if(b.isConnected) b.textContent = 'Partager'; }, 2500); } }catch(e){ prompt('Le lien à partager :', url); }
}
document.addEventListener('input', (e) => {
  if(e.target && e.target.id === 'cpRecherche'){
    clearTimeout(CP.minuteur);
    const q = e.target.value;
    CP.minuteur = setTimeout(() => cpChercher(q), 220);
  }
});
document.addEventListener('keydown', (e) => {
  if(e.target && e.target.id === 'cpRecherche' && e.key === 'Enter'){
    e.preventDefault();
    const b = document.querySelector('#cpResultats [data-cp-ref]');
    if(b) cpOuvrir(b.dataset.cpRef);
  }
});
document.addEventListener('click', (e) => {
  const r = e.target.closest('[data-cp-ref]');
  if(r){ cpOuvrir(r.dataset.cpRef); return; }
  if(e.target.closest('[data-cp-viens]')){ cpViens(); return; }
  const pa = e.target.closest('[data-cp-partager]');
  if(pa){ cpPartager(pa); return; }
  if(e.target.closest('[data-cp-aller]')){
    const s = document.getElementById('lpCp'), i = document.getElementById('cpRecherche');
    if(s && s.scrollIntoView) s.scrollIntoView({ behavior: 'smooth', block: 'start' });
    if(i) setTimeout(() => i.focus({ preventScroll: true }), 450);
  }
});

// une fois connecté : la commune vue sur la page d'accueil, ou ?c= dans l'adresse
async function cpApresConnexion(){
  if(CP.fait) return;
  let cible = null;
  try{ cible = JSON.parse(localStorage.getItem('tf-cible') || 'null'); }catch(e){}
  if(cible && !(Date.now() - (Number(cible.le) || 0) < 3 * 3600e3)) cible = null;
  const ref = cpRefUrl();
  if(!cible && !ref) return;
  CP.fait = true;
  try{ localStorage.removeItem('tf-cible'); }catch(e){}
  if(ref){ try{ history.replaceState(null, '', location.pathname); }catch(e){} }
  if(ref && (!cible || cible.code !== ref)){
    try{ const r = await sb.rpc('commune_publique', { p_ref: ref }); const d = r.data; if(d) cible = { code: d.code, nom: d.nom, pris: !!d.proprio, lat: d.lat, lon: d.lon }; }catch(e){}
  }
  if(!cible || !SAISON2) return;
  for(let i = 0; i < 30 && !(collectionMap.size || othersMap.size); i++) await new Promise(r => setTimeout(r, 500));
  const tenue = collectionMap.has(cible.code) || othersMap.has(cible.code);
  if(!tenue){
    ncAller('front', 'tirage', () => notifier({ type: 'info', titre: `${cible.nom} est libre`, texte: 'Ouvre des paquets du Front : chaque carte tirée est une vraie commune, et elle devient à toi.' }));
    return;
  }
  ncAller('front', 'territoire', () => {
    voirCommuneSurCarte({ code: cible.code, lat: Number(cible.lat), lon: Number(cible.lon) });
    setTimeout(() => {
      const w = document.getElementById('mapWrap');
      if(w && (othersMap.has(cible.code) || collectionMap.has(cible.code))) ouvrirPanneau(cible.code, w.clientWidth / 2, Math.min(w.clientHeight / 2, 260));
    }, 900);
  });
}
