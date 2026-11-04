# patch343 (4/11/2026) : la roue du Front (aperçu v2 validé « ok c'est parfait ! »,
# va avec s2-98).
# - Les comptes bloqués par la réserve d'accueil (et tout le monde si le pot est
#   vide) voient la roue à la place des paquets du Front : mêmes jetons (1 toutes
#   les 20 min, 3 en réserve), « N tours dispo », « Prochain tour dans mm:ss »,
#   compte à rebours dans le bouton quand il n'y a plus de tour, tours restants
#   du jour, chances de chaque case (lues sur le serveur) sous la roue.
# - Le serveur tire la case (roue_front_tourner) ; la roue tourne ~4 s et atterrit
#   dessus (sans animation si « Animation » est coupée). Les chiffres restent
#   droits pendant qu'elle tourne. Carte du gain : énergie, lingots ou paquet
#   Terra, et ce qui est vraiment entré si une réserve était pleine.
# - Bandeau de la réserve : « la roue du Front remplace tes paquets ».
# - Notification « Un tour de roue t'attend » quand un jeton revient.
# - Règles : la réserve reste jusqu'à la fin de la saison, la roue. Une ligne
#   dans la cloche.
# Sans s2-98 (roue_front_etat absente), rien ne change.
import pathlib, json

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

# ================================================================== index.html
F = pathlib.Path('index.html'); s = F.read_text(encoding='utf-8')
s = rep(s, """<div class="ra" id="reserveAccueil" role="status" hidden></div><!-- patch322 -->""",
"""<div class="ra" id="reserveAccueil" role="status" hidden></div><!-- patch322 -->
      <div class="rdf" id="roueFront" hidden></div><!-- patch343 : la roue du Front -->""")
s = rep(s, """Quand il ne reste que <b>3 000 communes libres</b> ou moins dans le pot, seuls les joueurs arrivés depuis moins de 7 jours peuvent encore en ouvrir.</p>""",
"""Quand il ne reste que <b>3 000 communes libres</b> ou moins dans le pot, seuls les joueurs arrivés depuis moins de 7 jours peuvent encore en ouvrir, et cette <b>réserve d'accueil</b> reste en place jusqu'à la fin de la saison.</p>
            <p><b>La roue du Front</b> remplace alors les paquets des autres joueurs : un tour par paquet (toujours 1 toutes les 20 min, 3 en réserve), <b>15 tours par jour</b> au plus, gratuite. Elle donne de l'énergie (sans dépasser le maximum des bonus), des lingots (sans dépasser ta réserve de lingots) ou un paquet Terra. Les chances de chaque case sont affichées sous la roue.</p><!-- patch343 -->""")
F.write_text(s, encoding='utf-8')

# ====================================================================== app.js
F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')

# la notification quand un jeton revient : un tour de roue au lieu d'un paquet
s = rep(s, """  if(dispoPrecedente !== null && dispo > dispoPrecedente && !paquetEnCours && !raBloque()){   // patch322""",
"""  if(dispoPrecedente !== null && dispo > dispoPrecedente && !paquetEnCours && roueActive() && !roueTourne && ROUE.tours_jour < ROUE.par_jour){   // patch343
    notifier({
      type: 'succes',
      titre: 'Un tour de roue t\\'attend',
      texte: dispo > 1 ? `Tu en as ${dispo} en réserve. Touche ici pour tourner la roue du Front.` : 'Touche ici pour tourner la roue du Front.',
      aller: () => { ncAller('front', 'tirage'); window.scrollTo({ top: 0 }); }
    });
  } else if(dispoPrecedente !== null && dispo > dispoPrecedente && !paquetEnCours && !raBloque() && !roueActive()){   // patch322""")

# la roue suit l'affichage des paquets (bascule Front/Terra comprise)
s = rep(s, """  renderReserveAccueil();   // patch322
}
function paquetPretAffiche(){""", """  renderReserveAccueil();   // patch322
  renderRoue();   // patch343
}
function paquetPretAffiche(){""")

# la bascule Front/Terra remet la roue à jour tout de suite
s = rep(s, """  majBascule();
  rangerGroupes();   // patch191""", """  majBascule();
  rangerGroupes();   // patch191
  if(typeof renderRoue === 'function') renderRoue();   // patch343""")

# l'état de la roue est relu avec celui de la réserve (au démarrage, puis toutes les 5 min)
s = rep(s, """    RESERVE_ACCUEIL = !error && data ? data : null;   // s2-76 pas lancé : rien
  }catch(e){ RESERVE_ACCUEIL = null; }
  renderReserveAccueil();
  if(typeof renderPackStatus === 'function' && packStatusCache) renderPackStatus();
}""",
"""    RESERVE_ACCUEIL = !error && data ? data : null;   // s2-76 pas lancé : rien
  }catch(e){ RESERVE_ACCUEIL = null; }
  renderReserveAccueil();
  if(typeof renderPackStatus === 'function' && packStatusCache) renderPackStatus();
  chargerRoue();   // patch343
}""")

# le bandeau : la roue remplace les paquets
s = rep(s, """        <p class="ra-x">Les <b>${fr(Math.min(libres, seuil))}</b> dernières communes libres sont réservées aux joueurs arrivés depuis moins de ${jours} jours. Tes paquets du Front sont gardés. Pour gagner du terrain, attaque !</p>
        <div class="ra-act"><button type="button" class="ra-go fort" data-ra="attaquer">Attaquer</button><button type="button" class="ra-go" data-ra="terra">Paquets Terra</button></div>`;""",
"""        ${roueActive() ? `<p class="ra-x">Les <b>${fr(Math.min(libres, seuil))}</b> dernières communes libres sont réservées aux joueurs arrivés depuis moins de ${jours} jours. En attendant, <b>la roue du Front remplace tes paquets</b>.</p>`
        : `<p class="ra-x">Les <b>${fr(Math.min(libres, seuil))}</b> dernières communes libres sont réservées aux joueurs arrivés depuis moins de ${jours} jours. Tes paquets du Front sont gardés. Pour gagner du terrain, attaque !</p>
        <div class="ra-act"><button type="button" class="ra-go fort" data-ra="attaquer">Attaquer</button><button type="button" class="ra-go" data-ra="terra">Paquets Terra</button></div>`}`;   // patch343
    } else if(libres === 0 && roueActive()){   // patch343 : pot vide, la roue est pour tout le monde
      cas = 'bloque';
      html = `<span class="ra-ic">🛡️</span><span class="ra-t">Plus aucune commune libre</span>
        <p class="ra-x">Le pot du Front est vide. En attendant, <b>la roue du Front remplace tes paquets</b>. Pour gagner du terrain, attaque !</p>`;""")

ROUE_JS = r"""
// ---------- patch343 : la roue du Front (s2-98) ----------
// Les comptes bloqués par la réserve d'accueil (et tout le monde quand le pot
// est vide) tournent la roue au lieu d'ouvrir un paquet du Front. Mêmes jetons
// (1 toutes les 20 min, 3 en réserve), tours du jour plafonnés par le serveur.
// Le serveur tire la case (roue_front_tourner) : la roue ne fait qu'y atterrir.
var ROUE = null, roueLu = 0, roueTourne = false, roueRot = -14, roueSig = '', roueEtaitActive = false;
var roueChancesOuvertes = false, roueGainMinuterie = null;
const ROUE_STYLE = {
  petit:   { c1: '#FFD45C', c2: '#C98A12', puce: '#F0B429', ic: 'e' },
  lingots: { c1: '#4C6A96', c2: '#22385C', puce: '#3B5A86', ic: 'l' },
  eclair:  { c1: '#FF9A4D', c2: '#D0561A', puce: '#F07A33', ic: 'e' },
  mixte:   { c1: '#6FA8FF', c2: '#2C5FD0', puce: '#4C86F0', ic: 'el' },
  gros:    { c1: '#FF7A7E', c2: '#B92D33', puce: '#E5484D', ic: 'e', fort: true },
  coffre:  { c1: '#C29BFF', c2: '#6E3BD6', puce: '#9A6BF0', ic: 'l', fort: true },
  terra:   { c1: '#4BE09A', c2: '#178553', puce: '#2FBF78', ic: 't', muet: true, fort: true },
  jackpot: { c1: '#FF6FA0', c2: '#C2124F', puce: '#E8306F', ic: 's', muet: true, fort: true },
};
const ROUE_BOLT = 'M13.2 2.5 5.5 13.2h5.3l-1 8.3 7.7-10.7h-5.3z';
async function chargerRoue(){
  if(!SAISON2) return;
  if(roueTourne) return;   // l'état arrive avec le tour en cours
  try{
    const { data, error } = await sb.rpc('roue_front_etat');
    ROUE = !error && data ? data : null;   // s2-98 pas lancé : rien
  }catch(e){ ROUE = null; }
  roueLu = Date.now();
  renderRoue();
}
function roueActive(){
  return !!(SAISON2 && !enTerra() && ROUE && ROUE.ouverte);
}
function roueJetons(){
  if(!ROUE) return 0;
  const j = Number(ROUE.jetons) || 0;
  if(j >= 3) return j;   // un cadeau au-dessus de 3 est gardé
  return Math.min(3, j + (Date.now() - roueLu) / 1200000);
}
function roueCases(){
  return (ROUE && Array.isArray(ROUE.cases) ? ROUE.cases : []).filter(k => Number(k.poids) > 0);
}
function roueStyle(k){
  const e = Number(k.energie) > 0, l = Number(k.lingots) > 0;
  return ROUE_STYLE[k.id] || { c1: '#8A9BB4', c2: '#3D4B60', puce: '#8A9BB4', ic: e && l ? 'el' : e ? 'e' : l ? 'l' : Number(k.terra) > 0 ? 't' : 's' };
}
function roueAngles(){
  const L = roueCases(), tot = L.reduce((s, k) => s + Number(k.poids), 0) || 1;
  let a = 0;
  return L.map((k, i) => { const d = Number(k.poids) / tot * 360; const r = { k, i, a0: a, a1: a + d, am: a + d / 2, p: Number(k.poids) / tot * 100 }; a += d; return r; });
}
function rouePt(ang, r){ return [165 + r * Math.sin(ang * Math.PI / 180), 165 - r * Math.cos(ang * Math.PI / 180)]; }
function roueIcone(ic, s){
  const lingot = (x, y, k) => `<g transform="translate(${x} ${y}) scale(${k})"><path d="M-9 4 L-6 -4 H6 L9 4 Z" fill="#FFD35A" stroke="#7A4E0C" stroke-width="1.4"/><path d="M-5 -2.5 H5" stroke="#FFF3C4" stroke-width="1.3"/></g>`;
  const eclair = (x, y, k) => `<g transform="translate(${x} ${y}) scale(${k}) translate(-12 -12)"><path d="${ROUE_BOLT}" fill="#FFF7D6" stroke="#6b4508" stroke-width="1.2" stroke-linejoin="round"/></g>`;
  if(ic === 'e') return eclair(0, 0, s);
  if(ic === 'l') return lingot(0, 0, s);
  if(ic === 'el') return eclair(-9 * s, 0, s * .85) + lingot(9 * s, 1, s * .85);
  if(ic === 't') return `<g transform="scale(${s})"><rect x="-6.5" y="-9" width="13" height="18" rx="2.5" fill="#E9FFF3" stroke="#0e5c37" stroke-width="1.4"/><rect x="-4" y="-6.5" width="8" height="7" rx="1" fill="#3DD68C"/></g>`;
  return `<g transform="scale(${s})"><path d="M0 -10 L2.9 -3.2 10 -3.1 4.3 1.4 6.3 8.4 0 4.3 -6.3 8.4 -4.3 1.4 -10 -3.1 -2.9 -3.2Z" fill="#FFE27A" stroke="#7a4f0e" stroke-width="1.2"/></g>`;
}
function roueTexteCase(k){
  if(roueStyle(k).muet) return '';
  const e = Number(k.energie) || 0, l = Number(k.lingots) || 0;
  return e && l ? `+${e} · +${l}` : e ? `+${e}` : l ? `+${l}` : '';
}
function roueGainsTexte(k){
  const e = Number(k.energie) || 0, l = Number(k.lingots) || 0, t = Number(k.terra) || 0;
  return [e ? `+${e}<span class="rdf-e">${ICONE_ENERGIE}</span>` : '', l ? `+${l} lingot${l > 1 ? 's' : ''}` : '', t ? `${t} paquet${t > 1 ? 's' : ''} Terra` : '']
    .filter(Boolean).join(' ');
}
function roueSvgHtml(){
  const A = roueAngles(), R = 140;
  let defs = '<defs>', segs = '', labs = '';
  for(const s of A){
    const st = roueStyle(s.k);
    const [x0, y0] = rouePt(s.a0, R), [x1, y1] = rouePt(s.a1, R);
    defs += `<radialGradient id="rdf-g${s.i}" cx="165" cy="165" r="${R}" gradientUnits="userSpaceOnUse"><stop offset="0.25" stop-color="${st.c1}"/><stop offset="1" stop-color="${st.c2}"/></radialGradient>`;
    segs += A.length === 1 ? `<circle class="rdf-seg" data-i="${s.i}" cx="165" cy="165" r="${R}" fill="url(#rdf-g${s.i})"/>`
      : `<path class="rdf-seg" data-i="${s.i}" d="M165,165 L${x0.toFixed(2)},${y0.toFixed(2)} A${R},${R} 0 ${s.a1 - s.a0 > 180 ? 1 : 0} 1 ${x1.toFixed(2)},${y1.toFixed(2)} Z" fill="url(#rdf-g${s.i})" stroke="#1B1206" stroke-width="1.6"/>`;
    const grand = s.p >= 15, moyen = s.p >= 5;
    const [mx, my] = rouePt(s.am, grand ? 96 : moyen ? 108 : 116);
    const txt = roueTexteCase(s.k);
    const lab = txt ? `<text y="${grand ? 15 : 12}" font-size="${grand ? 19 : 15}" text-anchor="middle" dominant-baseline="middle">${txt}</text>` : '';
    labs += `<g class="rdf-lab" data-i="${s.i}" data-x="${mx.toFixed(1)}" data-y="${my.toFixed(1)}"><g transform="translate(0 ${txt ? (grand ? -9 : -8) : 0})">${roueIcone(st.ic, grand ? 1.15 : moyen ? .9 : .78)}</g>${lab}</g>`;
  }
  defs += `<filter id="rdf-lueur" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <filter id="rdf-halo" x="-250%" y="-250%" width="600%" height="600%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <linearGradient id="rdf-anneau" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFE7A0"/><stop offset=".45" stop-color="#C8902A"/><stop offset="1" stop-color="#5E3B08"/></linearGradient></defs>`;
  let amp = '';
  for(let i = 0; i < 28; i++){ const [bx, by] = rouePt(i * 360 / 28, R + 11); amp += `<circle class="rdf-amp${i % 2 ? '' : ' b'}" cx="${bx.toFixed(1)}" cy="${by.toFixed(1)}" r="3.6"/>`; }
  return `<svg viewBox="0 0 330 330" aria-hidden="true">${defs}<circle cx="165" cy="165" r="${R + 18}" fill="#1A1006"/><circle cx="165" cy="165" r="${R + 15}" fill="url(#rdf-anneau)"/><circle cx="165" cy="165" r="${R + 6}" fill="#1A1006"/>${amp}</svg>
    <svg class="rdf-roue" id="rdfRoue" viewBox="0 0 330 330" aria-hidden="true">${segs}${labs}<circle cx="165" cy="165" r="${R}" fill="none" stroke="rgba(255,240,200,.35)" stroke-width="1.5"/></svg>
    <svg viewBox="0 0 330 330" aria-hidden="true"><g filter="url(#rdf-lueur)"><path d="M165 40 L151 8 Q165 -2 179 8 Z" fill="url(#rdf-anneau)" stroke="#3a2405" stroke-width="2"/><circle cx="165" cy="12" r="5" fill="#FFF6CF"/></g></svg>`;
}
function roueChancesHtml(){
  const A = roueAngles(); if(!A.length) return '';
  const fr1 = (n, d) => n.toLocaleString('fr-FR', { maximumFractionDigits: d });
  const moyE = A.reduce((s, x) => s + x.p / 100 * (Number(x.k.energie) || 0), 0), moyL = A.reduce((s, x) => s + x.p / 100 * (Number(x.k.lingots) || 0), 0);
  return `<h4>Chances de chaque case</h4>${A.map(x => `<div class="rdf-ch"><i style="background:${roueStyle(x.k).puce}"></i><span>${echapperTexte(x.k.nom || x.k.id)}</span><b>${roueGainsTexte(x.k)}</b><span>${fr1(x.p, 1)} %</span></div>`).join('')}
    <p class="rdf-ch-pied">En moyenne : ${fr1(moyE, 1)} énergie et ${fr1(moyL, 2)} lingot par tour. ${ROUE.par_jour} tours au plus par jour.</p>`;
}
function setRoueRot(r){
  roueRot = r;
  const svg = document.getElementById('rdfRoue'); if(!svg) return;
  svg.style.transform = `rotate(${r}deg)`;
  // les étiquettes restent droites, comme les nacelles d'une grande roue
  for(const g of svg.querySelectorAll('.rdf-lab')) g.setAttribute('transform', `translate(${g.dataset.x} ${g.dataset.y}) rotate(${-r})`);
}
function renderRoue(){
  const el = document.getElementById('roueFront'), panel = document.getElementById('panel-tirage');
  const actif = roueActive();
  if(panel) panel.classList.toggle('roue-active', actif);
  if(actif !== roueEtaitActive){ roueEtaitActive = actif; if(typeof renderReserveAccueil === 'function') renderReserveAccueil(); }
  if(!el) return;
  el.hidden = !actif;
  if(!actif) return;
  const sig = JSON.stringify(ROUE.cases || []);
  if(sig !== roueSig && !roueTourne){
    roueSig = sig;
    el.innerHTML = `<div class="rdf-titre">La roue du Front</div><div class="rdf-sous">Énergie et lingots à gagner</div>
      <div class="rdf-cadre">${roueSvgHtml()}<button type="button" class="rdf-centre" id="rdfCentre">Tourner</button><div class="rdf-gain" id="rdfGain" hidden></div></div>
      <div class="rdf-jetons"><span class="rdf-slots" id="rdfSlots"></span><span class="rdf-dispo"><b id="rdfDispo"></b><span id="rdfProchain"></span></span></div>
      <div class="rdf-jour" id="rdfJour"></div>
      <button type="button" class="rdf-lien" id="rdfLien"></button>
      <div class="rdf-chances" id="rdfChances" hidden></div>`;
    setRoueRot(roueRot);
  }
  const ch = document.getElementById('rdfChances');
  if(ch){ ch.hidden = !roueChancesOuvertes; if(roueChancesOuvertes) ch.innerHTML = roueChancesHtml(); }
  const li = document.getElementById('rdfLien');
  if(li) li.textContent = roueChancesOuvertes ? 'Masquer les chances' : 'Voir les chances de chaque case';
  renderRoueInfos();
}
function roueMmss(s){ s = Math.max(0, Math.ceil(s)); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); }
function roueEcrire(id, html){
  const e = document.getElementById(id); if(!e) return null;
  if(e._rdf !== html){ e.innerHTML = html; e._rdf = html; }
  return e;
}
function renderRoueInfos(){
  const el = document.getElementById('roueFront');
  if(!el || el.hidden || !ROUE || !el.offsetParent) return;   // onglet caché : rien à écrire
  const live = roueJetons(), dispo = Math.floor(live);
  const par = Number(ROUE.par_jour) || 15, faits = Number(ROUE.tours_jour) || 0, fini = faits >= par, reste = Math.max(0, par - faits);
  const prochain = live >= 3 ? 0 : (1 - (live % 1)) * 1200;
  const slot = (plein) => `<span class="rdf-slot${plein ? '' : ' vide'}"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="${ROUE_BOLT}"/></svg></span>`;
  roueEcrire('rdfSlots', [0, 1, 2].map(i => slot(i < dispo)).join(''));
  roueEcrire('rdfDispo', fini ? 'Fini pour aujourd’hui' : `${dispo} tour${dispo > 1 ? 's' : ''} dispo`);
  roueEcrire('rdfProchain', fini ? 'La roue revient demain, tes tours restent en réserve'
    : dispo >= 3 ? 'Réserve pleine : tourne avant d’en perdre !'
    : dispo === 0 ? 'Un tour revient toutes les <em>20 min</em>'
    : `Prochain tour dans <em>${roueMmss(prochain)}</em>`);
  roueEcrire('rdfJour', fini ? `${par} tours faits aujourd’hui` : `${reste} tour${reste > 1 ? 's' : ''} restant${reste > 1 ? 's' : ''} aujourd’hui`);
  const b = document.getElementById('rdfCentre');
  if(b){
    const peut = !roueTourne && !fini && dispo >= 1;
    roueEcrire('rdfCentre', roueTourne ? 'Tourner' : fini ? 'Demain<small>plus de tour</small>' : dispo < 1 ? `${roueMmss(prochain)}<small>prochain tour</small>` : 'Tourner');
    b.disabled = !peut;
    b.classList.toggle('attente', !peut && !roueTourne);
    b.setAttribute('aria-label', peut ? 'Tourner la roue du Front' : fini ? 'Plus de tour aujourd’hui' : roueTourne ? 'La roue tourne' : `Prochain tour dans ${roueMmss(prochain)}`);
  }
}
function roueAnimer(cible){
  return new Promise((fini) => {
    const A = roueAngles(), seg = A.find(s => s.k.id === cible) || A[0];
    if(!seg){ fini(); return; }
    const vise = -(seg.am + (Math.random() - .5) * (seg.a1 - seg.a0) * 0.6);   // pas toujours pile au milieu
    const depart = roueRot, delta = ((vise - depart) % 360 + 360) % 360;
    const arrivee = depart + (ouvAnim ? 5 * 360 : 0) + delta;
    if(!ouvAnim){ setRoueRot(arrivee % 360); fini(); return; }
    const duree = 4200, t0 = performance.now();
    let dernier = null, dernierTic = 0;
    const pas = (t) => {
      const p = Math.min(1, (t - t0) / duree), e = 1 - Math.pow(1 - p, 4);
      const r = depart + (arrivee - depart) * e;
      setRoueRot(r);
      const sous = ((-r % 360) + 360) % 360, i = A.findIndex(s => sous >= s.a0 && sous < s.a1);
      if(i !== dernier){ if(dernier !== null && t - dernierTic > 45){ sonsOuverture.assautTic(); dernierTic = t; } dernier = i; }
      if(p < 1) requestAnimationFrame(pas);
      else { setRoueRot(arrivee % 360); fini(); }
    };
    requestAnimationFrame(pas);
  });
}
function roueGainCacher(){
  clearTimeout(roueGainMinuterie);
  const g = document.getElementById('rdfGain'); if(g) g.hidden = true;
  const el = document.getElementById('roueFront'); if(el) el.classList.remove('gagne');
  document.querySelectorAll('#roueFront .gagnant').forEach(x => x.classList.remove('gagnant'));
}
function roueGainMontrer(d){
  const A = roueAngles(), seg = A.find(s => s.k.id === d.case);
  const k = seg ? seg.k : { nom: 'Gagné', energie: d.energie_prevue, lingots: d.lingots_prevus, terra: d.terra };
  const e = Number(d.energie) || 0, ep = Number(d.energie_prevue) || 0, l = Number(d.lingots) || 0, lp = Number(d.lingots_prevus) || 0, t = Number(d.terra) || 0;
  const parts = [];
  if(ep) parts.push(`+${ep}<span class="rdf-e">${ICONE_ENERGIE}</span>`);
  if(lp) parts.push(`+${lp}${ICONE_LINGOT}`);
  if(t) parts.push(`+${t} paquet${t > 1 ? 's' : ''} Terra`);
  let note;
  if(ep && e < ep) note = e ? `Énergie au maximum : +${e} seulement` : 'Ton énergie était déjà au maximum';
  else if(lp && l < lp) note = l ? `Réserve de lingots pleine : +${l} seulement` : 'Ta réserve de lingots était déjà pleine';
  else if(ep && lp) note = `Énergie : ${d.energie_totale} · lingots : ${d.lingots_total}`;
  else if(ep) note = `Ton énergie : ${d.energie_totale}`;
  else if(lp) note = `Tes lingots : ${d.lingots_total}`;
  else note = 'À ouvrir dans Terra';
  const g = document.getElementById('rdfGain'), el = document.getElementById('roueFront');
  if(!g || !el) return;
  g.className = 'rdf-gain' + (parts.length > 1 || t ? ' long' : '');
  g.style.setProperty('--rdf-c', seg ? roueStyle(k).puce : '#F0B429');
  g.innerHTML = `<div class="k">${echapperTexte(k.nom || '')} !</div><div class="v">${parts.join(' ')}</div><div class="n">${note}</div>${t ? '<button type="button" class="rdf-gain-go" data-rdf="terra">Aller dans Terra</button>' : ''}`;
  g.hidden = false;
  if(seg){
    el.classList.add('gagne');
    el.querySelectorAll(`[data-i="${seg.i}"]`).forEach(x => x.classList.add('gagnant'));
  }
  if(roueStyle(k).fort) sonsOuverture.assautConquete(); else sonsOuverture.assautGagne();
  clearTimeout(roueGainMinuterie);
  roueGainMinuterie = setTimeout(roueGainCacher, t ? 9000 : 5000);
}
async function roueTourner(){
  if(roueTourne || !roueActive()) return;
  if(Math.floor(roueJetons()) < 1 || Number(ROUE.tours_jour) >= Number(ROUE.par_jour)) return;
  const el = document.getElementById('roueFront');
  roueTourne = true; roueGainCacher(); renderRoueInfos();
  if(el) el.classList.add('tourne');
  let data = null, error = null;
  try{ ({ data, error } = await sb.rpc('roue_front_tourner')); }catch(e){ error = e; }
  if(error || !data){
    roueTourne = false; if(el) el.classList.remove('tourne');
    notifier({ type: 'erreur', titre: 'La roue n’a pas tourné', texte: messageLisible((error && error.message) || 'Réessaie dans un instant.') });
    chargerRoue();
    return;
  }
  ROUE.jetons = Number(data.jetons); roueLu = Date.now();
  ROUE.tours_jour = Number(data.tours_jour); if(data.par_jour) ROUE.par_jour = Number(data.par_jour);
  if(packStatusCache){ packStatusCache.jetons_actuels = Number(data.jetons); packStatusFetchedAt = Date.now(); dispoPrecedente = Math.floor(Number(data.jetons)); }
  renderRoueInfos();
  await roueAnimer(data.case);
  if(el) el.classList.remove('tourne');
  roueTourne = false;
  roueGainMontrer(data);
  renderRoueInfos();
  if(Number(data.energie) > 0 && typeof majEnergie === 'function') majEnergie();
}
document.getElementById('roueFront')?.addEventListener('click', (e) => {
  if(e.target.closest('#rdfCentre')){ roueTourner(); return; }
  if(e.target.closest('#rdfLien')){ roueChancesOuvertes = !roueChancesOuvertes; renderRoue(); return; }
  if(e.target.closest('[data-rdf="terra"]')){ roueGainCacher(); ncAller('terra', 'tirage'); return; }
  if(e.target.closest('#rdfGain')) roueGainCacher();
});
setInterval(siVisible(() => { if(roueActive()) renderRoueInfos(); }), 1000);
"""
s = rep(s, """
// ---------- patch313 : le sondage « d'autres pays ? » (s2-80) ----------""", ROUE_JS + """
// ---------- patch313 : le sondage « d'autres pays ? » (s2-80) ----------""")
F.write_text(s, encoding='utf-8')

# =================================================================== style.css
F = pathlib.Path('style.css'); s = F.read_text(encoding='utf-8')
s += """
/* patch343 : la roue du Front (remplace les paquets du Front pendant la réserve d'accueil) */
body:not(.mode-terra) #panel-tirage.roue-active .pack-buttons, body:not(.mode-terra) #panel-tirage.roue-active #packZone,
body:not(.mode-terra) #panel-tirage.roue-active #packStatus{ display:none !important; }
body.mode-terra #roueFront{ display:none !important; }
.rdf{ position:relative; max-width:620px; margin:0 0 16px; text-align:center; padding:14px 0 10px; border-radius:22px;
  background:radial-gradient(circle at 50% 46%, rgba(240,180,41,.20), rgba(240,180,41,.04) 42%, transparent 66%); }
.rdf[hidden]{ display:none; }
.rdf-titre{ font:900 1.55rem/1 var(--titre); letter-spacing:.06em; text-transform:uppercase; color:#FFE29A;
  text-shadow:0 0 18px rgba(240,180,41,.55), 0 2px 0 #7a4f0e; margin:0 0 2px; }
.rdf-sous{ font-size:.74rem; color:#A9BCD4; margin:0 0 6px; }
.rdf-cadre{ position:relative; width:min(330px, 86vw); aspect-ratio:1; margin:0 auto; }
.rdf-cadre > svg{ position:absolute; inset:0; width:100%; height:100%; }
.rdf-roue{ filter:drop-shadow(0 14px 26px rgba(0,0,0,.55)); will-change:transform; }
.rdf-lab text{ fill:#fff; stroke:rgba(0,0,0,.5); stroke-width:3px; paint-order:stroke; font-family:var(--titre), sans-serif; font-weight:900; text-anchor:middle; dominant-baseline:middle; }
.rdf-seg, .rdf-lab{ transition:opacity .35s ease; }
.rdf.gagne .rdf-seg:not(.gagnant){ opacity:.38; }
.rdf.gagne .rdf-lab:not(.gagnant){ opacity:.45; }
.rdf-seg.gagnant{ filter:url(#rdf-lueur); }
.rdf-amp{ fill:#B7791F; }
.rdf-amp.b{ fill:#FFF6CF; filter:url(#rdf-halo); }
.rdf.tourne .rdf-amp{ animation:rdfClign .36s steps(1) infinite; }
.rdf.tourne .rdf-amp.b{ animation-delay:-.18s; }
@keyframes rdfClign{ 0%{ fill:#FFF6CF; } 50%{ fill:#B7791F; } }
.rdf-centre{ position:absolute; left:35.5%; top:35.5%; width:29%; height:29%; border-radius:50%; border:0; cursor:pointer; padding:0;
  background:radial-gradient(circle at 34% 28%, #FFF1B8 0%, #FFD35A 22%, #F0B429 52%, #A8700F 100%);
  box-shadow:0 5px 0 #6e470c, 0 0 0 6px #241405, 0 0 0 9px #E9B53A, 0 0 24px rgba(255,200,80,.6);
  color:#2A1804; font:900 1.05rem/1.05 var(--titre); letter-spacing:.04em; text-transform:uppercase; -webkit-tap-highlight-color:transparent;
  transition:transform .12s ease, box-shadow .12s ease; }
.rdf-centre:not(:disabled):active{ transform:translateY(3px); box-shadow:0 2px 0 #6e470c, 0 0 0 6px #241405, 0 0 0 9px #E9B53A, 0 0 18px rgba(255,200,80,.5); }
.rdf-centre small{ display:block; font:700 .62rem/1.2 var(--texte, inherit); letter-spacing:0; text-transform:none; opacity:.8; margin-top:2px; }
.rdf-centre:disabled{ cursor:default; }
.rdf-centre.attente{ background:radial-gradient(circle at 34% 28%, #D7DDE6, #8E9AAB 55%, #4B5566); color:#1C2430;
  box-shadow:0 5px 0 #2b313b, 0 0 0 6px #10151d, 0 0 0 9px #6B778A; font-variant-numeric:tabular-nums; }
.rdf-jetons{ display:flex; align-items:center; justify-content:center; gap:12px; margin:12px auto 2px; padding:0 4px; }
.rdf-slots{ display:flex; gap:6px; flex:none; }
.rdf-slot{ width:30px; height:30px; border-radius:9px; display:grid; place-items:center; border:1.5px solid rgba(240,180,41,.55); background:rgba(240,180,41,.16); color:#FFD35A; box-sizing:border-box; }
.rdf-slot svg{ width:17px; height:17px; }
.rdf-slot.vide{ border:1.5px dashed rgba(169,188,212,.35); background:transparent; color:rgba(169,188,212,.35); }
.rdf-dispo{ text-align:left; line-height:1.2; min-width:0; }
.rdf-dispo b{ display:block; font:900 1.25rem/1 var(--titre); color:#fff; letter-spacing:.02em; }
.rdf-dispo span{ font-size:.76rem; color:#A9BCD4; }
.rdf-dispo span em{ font-style:normal; color:#FFD35A; font-weight:700; font-variant-numeric:tabular-nums; }
.rdf-jour{ font-size:.68rem; color:#7F92AA; margin-top:4px; }
.rdf-lien{ display:inline-block; margin-top:6px; padding:4px 8px; border:0; background:none; font:inherit; font-size:.72rem; color:#A9BCD4; text-decoration:underline; cursor:pointer; }
.rdf-chances{ margin:8px auto 0; max-width:330px; text-align:left; background:rgba(9,16,30,.7); border:1px solid rgba(169,188,212,.18); border-radius:14px; padding:8px 12px; }
.rdf-chances[hidden]{ display:none; }
.rdf-chances h4{ margin:2px 0 6px; font:800 .78rem/1.2 var(--titre); letter-spacing:.06em; text-transform:uppercase; color:#FFE29A; }
.rdf-ch{ display:grid; grid-template-columns:12px 1fr auto 44px; gap:8px; align-items:center; padding:4px 0; border-top:1px solid rgba(169,188,212,.08); font-size:.78rem; color:#DCE5F0; }
.rdf-ch i{ width:10px; height:10px; border-radius:3px; }
.rdf-ch b{ color:#fff; font-weight:800; white-space:nowrap; }
.rdf-ch span:last-child{ text-align:right; color:#A9BCD4; font-variant-numeric:tabular-nums; }
.rdf-ch-pied{ font-size:.68rem; color:#7F92AA; margin:6px 0 2px; }
.rdf-e{ display:inline-flex; vertical-align:-2px; color:#FFD35A; }
.rdf-e svg{ width:1em; height:1em; }
.rdf-gain{ --rdf-c:#FF6B6F; position:absolute; left:50%; top:40%; transform:translateX(-50%); z-index:3; min-width:60%; max-width:92%; box-sizing:border-box; padding:10px 16px 11px; border-radius:16px; cursor:pointer;
  background:linear-gradient(160deg,#2A1A3E,#140C22); border:1.5px solid var(--rdf-c);
  box-shadow:0 16px 34px rgba(0,0,0,.6);
  box-shadow:0 0 0 4px color-mix(in srgb, var(--rdf-c) 18%, transparent), 0 16px 34px rgba(0,0,0,.6), 0 0 40px color-mix(in srgb, var(--rdf-c) 45%, transparent);
  animation:rdfGain .35s cubic-bezier(.2,1.4,.4,1); }
.rdf-gain[hidden]{ display:none; }
@keyframes rdfGain{ from{ transform:translateX(-50%) scale(.6); opacity:0; } to{ transform:translateX(-50%) scale(1); opacity:1; } }
.rdf-gain .k{ font-size:.66rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; color:#FFD9A0; color:color-mix(in srgb, var(--rdf-c) 60%, #fff); }
.rdf-gain .v{ font:900 2.2rem/1 var(--titre); color:#fff; margin-top:4px; text-shadow:0 0 16px color-mix(in srgb, var(--rdf-c) 70%, transparent); display:flex; align-items:center; justify-content:center; gap:6px; flex-wrap:wrap; }
.rdf-gain.long .v{ font-size:1.55rem; }
.rdf-gain .v .rdf-e svg{ width:.9em; height:.9em; }
.rdf-gain .v .lingot{ width:26px; height:17px; }
.rdf-gain .n{ font-size:.72rem; color:#C9D3E0; margin-top:4px; }
.rdf-gain-go{ margin-top:8px; padding:6px 12px; border-radius:9px; border:0; background:#2FBF78; color:#062814; font-weight:800; font-size:.78rem; cursor:pointer; }
@media (prefers-reduced-motion: reduce){ .rdf.tourne .rdf-amp{ animation:none; } .rdf-gain{ animation:none; } }
"""
F.write_text(s, encoding='utf-8')

# ======================================================= data/nouveautes.json
F = pathlib.Path('data/nouveautes.json'); d = json.loads(F.read_text(encoding='utf-8'))
assert d[0]['date'] == '2026-11-04', d[0]['date']
d[0]['nouveautes'].insert(0, "🎡 Roue du Front : les dernières communes libres restent aux nouveaux joueurs jusqu’à la fin de la saison. Pour les autres, la roue remplace les paquets du Front : un tour toutes les 20 min (3 en réserve), 15 par jour, pour de l’énergie, des lingots ou un paquet Terra. Les chances de chaque case sont affichées sous la roue")
F.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch343 appliqué')
