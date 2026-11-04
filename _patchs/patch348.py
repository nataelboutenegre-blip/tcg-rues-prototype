# patch348 (4/11/2026) : la zone de départ de la saison 3 (va avec s3-6 ; aperçu
# du 4/11 : feuille « Où commences-tu ? » et bandeau du Tirage).
# - Avant le premier paquet du Front de la saison, la feuille « Où commences-tu ? »
#   s'ouvre : les 13 régions et la Suisse, communes libres, joueurs déjà partis
#   là (« dont x de ton clan »), zone complète grisée, Suisse « NOUVEAU ». Le
#   bouton « Commencer en … » enregistre le choix (définitif pour la saison) et
#   ouvre le paquet. « Plus tard » ferme sans rien ouvrir.
# - Bandeau dans Tirage : « Départ : Bretagne · Encore 2 paquets du Front dans ta
#   zone » (3 points) ; avant le choix, « Choisis ta zone de départ » ouvre la
#   feuille ; zone pleine : « tes paquets tirent partout ».
# - Rien en Terra, rien pour la roue du Front.
# ÉTEINT tant que le serveur ne l'ouvre pas : sans s3-6 (zone_depart_etat absente)
# ou avec config_jeu 'zone_depart' ouvert = 0, rien ne change à l'écran.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

# ================================================================== index.html
F = pathlib.Path('index.html'); s = F.read_text(encoding='utf-8')
s = rep(s, """<div class="rdf" id="roueFront" hidden></div><!-- patch343 : la roue du Front -->""",
"""<div class="rdf" id="roueFront" hidden></div><!-- patch343 : la roue du Front -->
      <div class="zd" id="zoneDepart" hidden></div><!-- patch348 : la zone de départ -->""")
F.write_text(s, encoding='utf-8')

# ====================================================================== app.js
F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')

# le bandeau suit l'affichage des paquets et la bascule Front/Terra
s = rep(s, """  renderReserveAccueil();   // patch322
  renderRoue();   // patch343
}""", """  renderReserveAccueil();   // patch322
  renderRoue();   // patch343
  renderZoneDepart();   // patch348
}""")
s = rep(s, """  if(typeof renderRoue === 'function') renderRoue();   // patch343""",
"""  if(typeof renderRoue === 'function') renderRoue();   // patch343
  if(typeof renderZoneDepart === 'function') renderZoneDepart();   // patch348""")

# relu avec la réserve d'accueil (au chargement, puis toutes les 5 min) et après chaque paquet
s = rep(s, """  chargerRoue();   // patch343
}""", """  chargerRoue();   // patch343
  zdCharger();   // patch348
}""")
s = rep(s, """      if(!enTerra()) pcApresPaquet();   // patch336""",
"""      if(!enTerra()) pcApresPaquet();   // patch336
      if(!enTerra()) zdCharger();   // patch348 : un paquet de zone en moins""")

# avant le premier paquet du Front de la saison : la feuille
s = rep(s, """async function openPack(type){
  if(type === 'gratuit' && raBloque()){   // patch322""", """async function openPack(type){
  if(type === 'gratuit' && zdDoitChoisir()){ zdOuvrir(() => openPack(type)); return; }   // patch348
  if(type === 'gratuit' && raBloque()){   // patch322""")
s = rep(s, """  armerPaquet(pack, async () => {
    if(paquetEnCours) return null;
    paquetEnCours = true;""", """  armerPaquet(pack, async () => {
    if(paquetEnCours) return null;
    if(type === 'gratuit' && zdDoitChoisir()){ zdOuvrir(); return null; }   // patch348
    paquetEnCours = true;""")

s = s.rstrip('\n') + r"""

// ---------- patch348 : la zone de départ (s3-6) ----------
// Une fois par saison, le joueur choisit une région (ou la Suisse) : ses 3
// premiers paquets du Front y tombent. Le serveur décide de tout (ouvert, zones,
// cartes restantes) ; sans s3-6 ou éteint, rien ne s'affiche.
var ZD = null, zdSel = null, zdApres = null, zdEnvoi = false;
const ZD_NOUVEAU = new Set(['Suisse']);
const ZD_DANS = { 'Grand Est': 'dans le', 'Centre-Val de Loire': 'dans le', 'Hauts-de-France': 'dans les', 'Pays de la Loire': 'dans les' };
function zdDans(z){ return (ZD_DANS[z] || 'en') + ' ' + z; }
async function zdCharger(){
  try{
    const { data, error } = await sb.rpc('zone_depart_etat');
    ZD = !error && data ? data : null;   // s3-6 pas lancé : rien
  }catch(e){ ZD = null; }
  renderZoneDepart();
  if(zdVoileEl() && !zdVoileEl().hidden) zdRendre();
}
function zdOuverte(){ return !!(ZD && ZD.ouvert && !enTerra()); }
function zdZonesLibres(){ return ZD && Array.isArray(ZD.zones) ? ZD.zones.filter(z => !z.fermee) : []; }
// le joueur doit choisir avant d'ouvrir un paquet du Front
function zdDoitChoisir(){
  return zdOuverte() && !ZD.choisi && zdZonesLibres().length > 0 && !(typeof roueActive === 'function' && roueActive());
}
function renderZoneDepart(){
  const el = document.getElementById('zoneDepart');
  if(!el) return;
  const rien = () => { el.hidden = true; el.innerHTML = ''; el.className = 'zd'; };
  if(!zdOuverte() || (typeof roueActive === 'function' && roueActive())) return rien();
  const n = Math.max(1, Number(ZD.paquets) || 3);
  let html;
  if(!ZD.choisi){
    if(!zdZonesLibres().length) return rien();
    el.className = 'zd zd-choisir';
    html = `<button type="button" class="zd-ligne" data-zd="ouvrir"><span class="zd-pin" aria-hidden="true">📍</span>`
      + `<span class="zd-txt"><b>Choisis ta zone de départ</b><small>Tes ${n} premiers paquets du Front y tomberont</small></span>`
      + `<span class="zd-fleche" aria-hidden="true">›</span></button>`;
  } else {
    const reste = Math.max(0, Number(ZD.paquets_restants) || 0);
    if(reste <= 0) return rien();
    const z = echapperTexte(ZD.choisi);
    if(ZD.actif){
      el.className = 'zd';
      const points = Array.from({ length: n }, (_, i) => `<i class="${i >= n - reste ? 'on' : ''}"></i>`).join('');
      html = `<div class="zd-ligne"><span class="zd-pin" aria-hidden="true">📍</span>`
        + `<span class="zd-txt"><b>Départ : ${z}</b><small>Encore ${reste} paquet${reste > 1 ? 's' : ''} du Front dans ta zone</small></span>`
        + `<span class="zd-points" aria-label="${reste} paquet${reste > 1 ? 's' : ''} sur ${n}">${points}</span></div>`;
    } else {
      el.className = 'zd zd-pleine';
      html = `<div class="zd-ligne"><span class="zd-pin" aria-hidden="true">📍</span>`
        + `<span class="zd-txt"><b>Départ : ${z}</b><small>Plus de commune libre dans ta zone : tes paquets tirent partout</small></span></div>`;
    }
  }
  if(el.innerHTML !== html) el.innerHTML = html;
  el.hidden = false;
}

// la feuille « Où commences-tu ? »
function zdVoileEl(){ return document.getElementById('zdVoile'); }
function zdOuvrir(apres){
  zdApres = typeof apres === 'function' ? apres : null;
  let v = zdVoileEl();
  if(!v){
    v = document.createElement('div');
    v.className = 'pc-voile zd-voile'; v.id = 'zdVoile'; v.hidden = true;
    v.innerHTML = '<div class="pc-boite zd-boite" id="zdBoite" role="dialog" aria-modal="true" aria-label="Choisis ta zone de départ"></div>';
    document.body.appendChild(v);
  }
  zdRendre();
  v.hidden = false;
  requestAnimationFrame(() => v.classList.add('ouvert'));
  zdCharger();   // chiffres frais
}
function zdFermer(){
  const v = zdVoileEl();
  if(!v || v.hidden) return;
  v.classList.remove('ouvert');
  setTimeout(() => { v.hidden = true; }, 180);
}
function zdRendre(){
  const b = document.getElementById('zdBoite');
  if(!b) return;
  const n = Math.max(1, Number(ZD && ZD.paquets) || 3);
  const zones = (ZD && Array.isArray(ZD.zones) ? ZD.zones.slice() : [])
    .sort((a, c) => (a.zone === 'Suisse') - (c.zone === 'Suisse') || a.zone.localeCompare(c.zone, 'fr'));
  if(zdSel && !zones.some(z => z.zone === zdSel && !z.fermee)) zdSel = null;
  const nb = (x) => Number(x || 0).toLocaleString('fr-FR');
  const cases = zones.map(z => {
    const nom = echapperTexte(z.zone);
    const j = Number(z.joueurs) || 0;
    const joueurs = j ? `${j} joueur${j > 1 ? 's' : ''}` : 'aucun joueur';
    const neuf = ZD_NOUVEAU.has(z.zone) ? '<span class="zd-neuf">Nouveau</span>' : '';
    if(z.fermee) return `<button type="button" class="zd-zone fermee" disabled>${neuf}<b>${nom}</b><small>Complète · ${joueurs}</small></button>`;
    const clan = Number(z.clan) > 0 ? `<small class="zd-clan">dont ${z.clan} de ton clan</small>` : '';
    return `<button type="button" class="zd-zone${zdSel === z.zone ? ' on' : ''}" data-zd-zone="${nom}" aria-pressed="${zdSel === z.zone}">${neuf}`
      + `<b>${nom}</b><small>${nb(z.libres)} communes libres · ${joueurs}</small>${clan}</button>`;
  }).join('');
  const seuil = Number(ZD && ZD.seuil) || 0.75;
  const seuilTxt = Math.abs(seuil - 0.75) < 0.001 ? 'les trois quarts' : Math.round(seuil * 100) + ' %';
  const saison = echapperTexte((ZD && ZD.saison_nom) || 'Nouvelle saison');
  b.innerHTML = `<div class="pc-poignee"></div>
    <div class="pc-kicker">${saison} · ton départ</div>
    <div class="pc-titre">Où commences-tu ?</div>
    <p class="pc-txt">Tes <b>${n} premiers paquets du Front</b> tombent dans la zone choisie, puis le tirage reprend partout. <b>Choix définitif</b> pour la saison.</p>
    <div class="zd-grille">${cases || '<p class="pc-txt">Chargement…</p>'}</div>
    <button type="button" class="pc-go" data-zd="valider"${zdSel && !zdEnvoi ? '' : ' disabled'}>${zdEnvoi ? 'Un instant…' : zdSel ? 'Commencer ' + echapperTexte(zdDans(zdSel)) : 'Choisis ta zone'}</button>
    <p class="zd-note">Une zone se ferme quand ${seuilTxt} de ses communes sont prises. Tes communes gardées de la saison passée restent où elles sont.</p>
    <div class="pc-sec"><button type="button" data-zd="fermer">Plus tard</button></div>`;
}
async function zdValider(){
  if(!zdSel || zdEnvoi) return;
  zdEnvoi = true; zdRendre();
  const zone = zdSel;
  const { data, error } = await sb.rpc('zone_depart_choisir', { p_zone: zone });
  zdEnvoi = false;
  if(error){
    notifier({ type: 'erreur', titre: 'Zone non enregistrée', texte: messageLisible(error.message) });
    zdSel = null;
    await zdCharger();
    return;
  }
  ZD = data || ZD;
  zdSel = null;
  renderZoneDepart();
  zdFermer();
  notifier({ type: 'succes', titre: 'Départ : ' + zone, texte: 'Tes prochains paquets du Front tombent ' + zdDans(zone) + '.' });
  const apres = zdApres; zdApres = null;
  if(apres) setTimeout(apres, 220);
}
document.addEventListener('click', (e) => {
  const z = e.target.closest('[data-zd-zone]');
  if(z){ zdSel = z.dataset.zdZone; zdRendre(); return; }
  const b = e.target.closest('[data-zd]');
  if(!b) return;
  const a = b.dataset.zd;
  if(a === 'ouvrir') return zdOuvrir();
  if(a === 'valider') return zdValider();
  if(a === 'fermer'){ zdApres = null; return zdFermer(); }
});
document.addEventListener('click', (e) => { const v = zdVoileEl(); if(v && e.target === v){ zdApres = null; zdFermer(); } });
"""
F.write_text(s, encoding='utf-8')

# =================================================================== style.css
F = pathlib.Path('style.css'); s = F.read_text(encoding='utf-8')
s = s.rstrip('\n') + """

/* patch348 : la zone de départ (saison 3) */
body.mode-terra #zoneDepart{ display:none !important; }
.zd{ max-width:620px; margin:0 0 14px; }
.zd-ligne{ display:flex; align-items:center; gap:12px; width:100%; box-sizing:border-box; text-align:left; font:inherit; color:#fff;
  background:rgba(240,180,41,.08); border:1px solid rgba(240,180,41,.45); border-radius:14px; padding:10px 14px; }
button.zd-ligne{ cursor:pointer; }
.zd-pin{ font-size:1.35rem; line-height:1; flex:none; }
.zd-txt{ flex:1; min-width:0; }
.zd-txt b{ display:block; font-size:.98rem; }
.zd-txt small{ display:block; font-size:.78rem; color:var(--brume); margin-top:2px; }
.zd-points{ display:flex; gap:5px; flex:none; }
.zd-points i{ width:10px; height:10px; border-radius:50%; background:rgba(169,188,212,.3); }
.zd-points i.on{ background:var(--c-legendaire); }
.zd-fleche{ font-size:1.5rem; line-height:1; color:var(--c-legendaire); flex:none; }
.zd-choisir .zd-ligne{ background:rgba(240,180,41,.14); }
.zd-pleine .zd-ligne{ background:rgba(10,22,40,.4); border-color:rgba(169,188,212,.25); }
.zd-pleine .zd-pin{ opacity:.55; }
.zd-boite{ width:min(560px,100%); }
.zd-grille{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; margin:0 0 14px; }
.zd-zone{ position:relative; font:inherit; color:#fff; text-align:left; cursor:pointer; background:rgba(10,22,40,.45);
  border:1.5px solid rgba(169,188,212,.2); border-radius:12px; padding:10px 11px; min-height:64px; }
.zd-zone b{ display:block; font-size:.9rem; line-height:1.2; }
.zd-zone small{ display:block; font-size:.72rem; color:var(--brume); margin-top:3px; line-height:1.35; }
.zd-zone small.zd-clan{ color:#7CC4FF; margin-top:2px; }
.zd-zone.on{ border-color:var(--c-legendaire); background:rgba(240,180,41,.12); box-shadow:0 0 0 1px var(--c-legendaire) inset; }
.zd-zone.fermee{ opacity:.45; cursor:default; }
.zd-neuf{ position:absolute; top:-8px; right:8px; font-size:.6rem; font-weight:800; letter-spacing:.06em; text-transform:uppercase;
  background:#E5484D; color:#fff; border-radius:99px; padding:2px 7px; }
.zd-note{ font-size:.72rem; color:#8FA2BC; line-height:1.45; margin:12px 0 0; }
@media (hover:hover){ .zd-zone:not(.fermee):hover{ border-color:rgba(240,180,41,.6); } }
"""
F.write_text(s, encoding='utf-8')
print('patch348 ok')
