# patch322 : le bandeau de la réserve d'accueil dans le Tirage du Front (aperçu validé le 2/11 au soir)
#  s2-76 réserve les 3 000 dernières communes libres aux comptes de moins de 7 jours. Jusqu'ici
#  un ancien ne le découvrait qu'en cliquant (erreur). Trois bandeaux, Front seulement :
#   1. « bientôt » (bleu) : ancien joueur, moins de 9 000 communes libres (réserve + 6 000) ;
#   2. « bloqué » (rouge) : le serveur dit que le joueur est bloqué ; boutons Attaquer / Paquets Terra ;
#      le bouton du paquet est grisé (« Paquets du Front en pause »), le paquet prêt n'est plus
#      affiché, pas de notification « un paquet gratuit t'attend », et openPack refuse sans appel ;
#   3. « nouveau » (vert) : réserve atteinte, compte de moins de 7 jours : date limite.
#  Pas de SQL : reserve_accueil_etat() existe depuis s2-76 ; le nombre de communes libres vient
#  de saison_courante() (potLibres, déjà affiché sous le paquet).
import pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

# ---------- index.html ----------
f = pathlib.Path('index.html'); s = f.read_text(encoding='utf-8')
assert 'patch322' not in s
s = rep(s, """      <button type="button" class="cdj-carte" id="cdjCarte" hidden></button>
      <div class="pack-buttons">""", """      <button type="button" class="cdj-carte" id="cdjCarte" hidden></button>
      <div class="ra" id="reserveAccueil" role="status" hidden></div><!-- patch322 -->
      <div class="pack-buttons">""")
f.write_text(s, encoding='utf-8')

# ---------- style.css ----------
f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch322' not in s
s += """
/* patch322 : le bandeau de la réserve d'accueil (Tirage, Front) */
.ra{ display:grid; grid-template-columns:28px minmax(0,1fr); gap:4px 10px; align-items:start;
  max-width:620px; box-sizing:border-box; margin:0 0 14px; padding:12px 14px 13px; border-radius:14px;
  border:1px solid rgba(169,188,212,.3); background:rgba(169,188,212,.07); color:#fff; text-align:left; }
.ra[hidden]{ display:none; }
.ra-ic{ width:28px; height:28px; border-radius:50%; display:grid; place-items:center; font-size:.95rem;
  background:rgba(169,188,212,.16); grid-row:span 2; margin-top:1px; }
.ra-t{ font-size:.9rem; font-weight:700; line-height:1.3; }
.ra-t b{ font-family:var(--titre); font-weight:900; font-size:1.1rem; letter-spacing:.01em; font-variant-numeric:tabular-nums; }
.ra-x{ font-size:.76rem; color:#C3D0E0; line-height:1.45; margin:0; }
.ra-x b{ color:#fff; }
.ra-act{ grid-column:2; display:flex; gap:8px; flex-wrap:wrap; margin-top:8px; }
.ra-go{ font:inherit; font-size:.76rem; font-weight:700; border-radius:999px; padding:7px 13px; cursor:pointer; white-space:nowrap;
  border:1px solid rgba(255,255,255,.3); background:rgba(255,255,255,.08); color:#fff; }
.ra.bientot{ border-color:rgba(91,155,255,.4); background:linear-gradient(160deg,rgba(47,124,246,.14),rgba(15,31,56,.5) 60%); }
.ra.bientot .ra-ic{ background:rgba(47,124,246,.25); }
.ra.bientot .ra-t b{ color:#8DB8FF; }
.ra.bloque{ border-color:rgba(229,72,77,.55); background:linear-gradient(160deg,rgba(229,72,77,.18),rgba(15,31,56,.55) 60%); }
.ra.bloque .ra-ic{ background:rgba(229,72,77,.3); }
.ra.bloque .ra-go.fort{ background:#E5484D; border-color:#E5484D; }
.ra.nouveau{ border-color:rgba(43,212,139,.5); background:linear-gradient(160deg,rgba(43,212,139,.14),rgba(15,31,56,.5) 60%); }
.ra.nouveau .ra-ic{ background:rgba(43,212,139,.24); }
.ra.nouveau .ra-t b{ color:#5BE3A6; }
button.open-btn.ra-pause{ opacity:.5; cursor:not-allowed; }
body.mode-terra #reserveAccueil{ display:none !important; }
"""
f.write_text(s, encoding='utf-8')

# ---------- app.js ----------
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch322' not in s

# 1. chargement au démarrage, avec Premiers pas
s = rep(s, """  chargerPremiersPas();   // patch306
  chargerSondagePays();   // patch313""", """  chargerPremiersPas();   // patch306
  chargerReserveAccueil(); setInterval(siVisible(chargerReserveAccueil), 300000);   // patch322
  chargerSondagePays();   // patch313""")

# 2. renderPackStatus : pas de notification « paquet gratuit » si bloqué, et le bandeau suit
s = rep(s, """  if(dispoPrecedente !== null && dispo > dispoPrecedente && !paquetEnCours){""",
           """  if(dispoPrecedente !== null && dispo > dispoPrecedente && !paquetEnCours && !raBloque()){   // patch322""")
s = rep(s, """  const ps = document.getElementById('packStatus');
  if(ps) ps.hidden = !ps.children.length;
}""", """  const ps = document.getElementById('packStatus');
  if(ps) ps.hidden = !ps.children.length;
  renderReserveAccueil();   // patch322
}""")

# 3. le paquet prêt n'est pas montré à un joueur bloqué
s = rep(s, """  const pret = zone.querySelector('.paquet[data-pret]');
  if(dispo >= 1 && zone.children.length === 0) afficherPaquetPret('gratuit');""", """  const pret = zone.querySelector('.paquet[data-pret]');
  if(raBloque()){ if(pret) zone.innerHTML = ''; return; }   // patch322
  if(dispo >= 1 && zone.children.length === 0) afficherPaquetPret('gratuit');""")

# 4. openPack : refus local, sans appel au serveur
s = rep(s, """async function openPack(type){
  chargerNomsMonuments();""", """async function openPack(type){
  if(type === 'gratuit' && raBloque()){   // patch322
    notifier({ type: 'info', titre: 'Réserve d\\'accueil', texte: 'Les dernières communes du pot sont réservées aux nouveaux joueurs : ton paquet est gardé. Pour gagner du terrain, attaque !' });
    return;
  }
  chargerNomsMonuments();""")

# 5. le code du bandeau, après Premiers pas
s = rep(s, """document.getElementById('premiersPas')?.addEventListener('click', (e) => {
  const b = e.target.closest('[data-pp]');
  if(b) ppAction(b.dataset.pp, b);
});""", """document.getElementById('premiersPas')?.addEventListener('click', (e) => {
  const b = e.target.closest('[data-pp]');
  if(b) ppAction(b.dataset.pp, b);
});

// ---------- patch322 : le bandeau de la réserve d'accueil (s2-76) ----------
// Les dernières communes libres du Front vont aux comptes de moins de 7 jours.
// Le serveur dit si CE joueur est bloqué ; le nombre de communes libres vient
// de saison_courante() (potLibres). Trois cas : bientôt, bloqué, nouveau.
var RESERVE_ACCUEIL = null, raRelu = 0, raHtml = null, raCree = null;
var RA_AVANT = 6000;   // le bandeau « bientôt » s'affiche 6 000 communes avant la réserve
async function chargerReserveAccueil(){
  if(!SAISON2) return;
  raRelu = Date.now();
  if(raCree == null){
    try{ const { data: ss } = await sb.auth.getSession(); const c = ss && ss.session && ss.session.user && ss.session.user.created_at; if(c) raCree = new Date(c).getTime(); }catch(e){}
  }
  try{
    const { data, error } = await sb.rpc('reserve_accueil_etat');
    RESERVE_ACCUEIL = !error && data ? data : null;   // s2-76 pas lancé : rien
  }catch(e){ RESERVE_ACCUEIL = null; }
  renderReserveAccueil();
  if(typeof renderPackStatus === 'function' && packStatusCache) renderPackStatus();
}
function raBloque(){
  return !!(SAISON2 && !enTerra() && RESERVE_ACCUEIL && RESERVE_ACCUEIL.ouvert && RESERVE_ACCUEIL.bloque);
}
function raLibres(){
  if(typeof potLibres === 'number' && potLibres !== null) return Math.max(0, potLibres);
  const s = (typeof saisonEtat !== 'undefined') ? saisonEtat : null;
  return s && s.libres != null ? Number(s.libres) : null;
}
function raInscription(){ return raCree; }
function renderReserveAccueil(){
  const el = document.getElementById('reserveAccueil');
  const btn = document.getElementById('openFreeBtn');
  const R = RESERVE_ACCUEIL;
  const bloque = raBloque();
  if(btn){
    btn.classList.toggle('ra-pause', bloque);
    btn.textContent = bloque ? 'Paquets du Front en pause' : 'Ouvrir un paquet gratuit';
    if(bloque){ btn.disabled = true; btn.title = 'Réserve d\\'accueil : les dernières communes sont pour les nouveaux joueurs'; }
  }
  if(!el) return;
  let cas = null, html = '';
  const libres = raLibres();
  const fr = (n) => Number(n).toLocaleString('fr-FR').replace(/\\u202f/g, '\\u00a0');   // espace fine absente de la police : espace insécable
  if(SAISON2 && !enTerra() && R && R.ouvert && libres != null){
    const seuil = Number(R.communes) || 3000, jours = Number(R.jours) || 7;
    const ins = raInscription();
    const ancien = ins == null || ins < Date.now() - jours * 86400000;
    if(bloque){
      cas = 'bloque';
      html = `<span class="ra-ic">🛡️</span><span class="ra-t">Réserve d'accueil active</span>
        <p class="ra-x">Les <b>${fr(Math.min(libres, seuil))}</b> dernières communes libres sont réservées aux joueurs arrivés depuis moins de ${jours} jours. Tes paquets du Front sont gardés. Pour gagner du terrain, attaque !</p>
        <div class="ra-act"><button type="button" class="ra-go fort" data-ra="attaquer">Attaquer</button><button type="button" class="ra-go" data-ra="terra">Paquets Terra</button></div>`;
    } else if(libres <= seuil && !ancien){
      cas = 'nouveau';
      const date = new Date(ins + jours * 86400000).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' });
      html = `<span class="ra-ic">🎁</span><span class="ra-t">Les dernières communes sont pour toi</span>
        <p class="ra-x">Les <b>${fr(libres)}</b> dernières communes libres sont réservées aux nouveaux joueurs. Tu peux en tirer jusqu'au <b>${date}</b>, profites-en !</p>`;
    } else if(libres <= seuil && ancien){
      // le serveur ne nous a pas encore dit bloqué : on lui redemande (une fois par minute au plus)
      if(Date.now() - raRelu > 60000) setTimeout(chargerReserveAccueil, 0);
    } else if(ancien && libres - seuil <= RA_AVANT){
      cas = 'bientot';
      const n = libres - seuil;
      html = `<span class="ra-ic">⏳</span><span class="ra-t">Plus que <b>${fr(n)}</b> commune${n > 1 ? 's' : ''} avant la réserve d'accueil</span>
        <p class="ra-x">Ensuite, les ${fr(seuil)} dernières communes libres iront aux joueurs arrivés depuis moins de ${jours} jours. Tes paquets du Front seront gardés, et pour gagner du terrain il faudra attaquer. Terra n'est pas concerné.</p>`;
    }
  }
  el.hidden = !cas;
  el.className = 'ra' + (cas ? ' ' + cas : '');
  if(raHtml !== html){ el.innerHTML = html; raHtml = html; }
}
document.getElementById('reserveAccueil')?.addEventListener('click', (e) => {
  const b = e.target.closest('[data-ra]');
  if(!b) return;
  if(b.dataset.ra === 'attaquer') ncAller('front', 'combat');
  else if(b.dataset.ra === 'terra') ncAller('terra', 'tirage');
});""")

# 6. le compteur de communes libres baisse : le bandeau suit
s = rep(s, """  document.getElementById('potJauge').setAttribute('aria-valuenow', String(Math.round(pct)));
  bloc.hidden = false;
}""", """  document.getElementById('potJauge').setAttribute('aria-valuenow', String(Math.round(pct)));
  bloc.hidden = false;
  if(typeof renderReserveAccueil === 'function') renderReserveAccueil();   // patch322
}""")
f.write_text(s, encoding='utf-8')
print('patch322 ok')
