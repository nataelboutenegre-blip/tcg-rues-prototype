# -*- coding: utf-8 -*-
u"""
patch69 — La Commune du jour jouable sans compte.

POURQUOI
  C'est la porte d'entree pour faire connaitre le jeu (discussion du
  4 octobre) : un resultat partage sur Discord ou ailleurs menait a un
  ecran de connexion, et la plupart des gens repartent a cet ecran-la.

LE CHOIX IMPORTANT : SANS COMPTE, ON JOUE LA COMMUNE D'HIER
  Un mode sans compte se relance a volonte. S'il donnait la commune du
  jour, n'importe qui y lirait deux distances (assez pour la situer), puis
  jouerait avec son vrai compte et « trouverait » du premier coup. Celle
  d'hier n'a plus rien de secret. Le visiteur le sait, et l'ecran de fin
  l'invite a creer un compte pour jouer celle d'aujourd'hui.

CE QUE LE VISITEUR VOIT
  - Sur la page d'accueil et l'ecran de connexion : « Jouer a la Commune
    du jour, sans compte ».
  - Le lien terrafront.fr/?onglet=cdj (celui du resultat partage) y mene
    directement quand on n'est pas connecte.
  - Le meme jeu que les joueurs, avec un bandeau : commune d'hier, sans
    compte. A la fin : la reponse, combien de joueurs l'ont trouvee, et
    « Creer mon compte » / « J'ai deja un compte ».
  - Ses essais sont gardes dans son navigateur jusqu'au lendemain.

COTE SERVEUR (_sql/cdj-3-invite.sql)
  cdj_invite(codes) : rien n'est enregistre, le navigateur renvoie ses
  essais et le serveur recalcule tout. Seule fonction appelable sans
  compte (role anon).

AUSSI
  Le texte partage pointe maintenant vers terrafront.fr/?onglet=cdj.
"""
import io, os

ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI

def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f:
        return f.read()

def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f:
        f.write(s)

def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)


# ---------------- index.html ----------------
html = lire('index.html')

html = rempl(html,
u"""          <span class="lp-gratuit">Gratuit · aucune carte bancaire</span>""",
u"""          <span class="lp-gratuit">Gratuit · aucune carte bancaire</span>
        </div>
        <div class="lp-invite">
          <button class="lp-invite-btn" data-cdj-invite>Jouer à la Commune du jour, sans compte</button>
          <span>Trouve une commune mystère en six essais, sans t'inscrire.</span>""", 'accueil')

html = rempl(html,
u"""      <button class="auth-retour" id="authOubliRetour" hidden>Retour à la connexion</button>""",
u"""      <button class="auth-retour" id="authOubliRetour" hidden>Retour à la connexion</button>
      <button class="auth-invite" data-cdj-invite>Essayer sans compte : la Commune du jour</button>""", 'connexion')

html = rempl(html,
u"""<div id="gameScreen" class="app-shell" style="display:none">""",
u"""<div id="cdjInvite" class="cdj-invite-ecran" hidden>
  <div class="cdj-invite-barre">
    <p class="lp-marque">Terra<span>Front</span></p>
    <button class="lp-connexion" data-cdj-connexion>J'ai déjà un compte</button>
  </div>
  <div id="cdjInviteHote"></div>
</div>

<div id="gameScreen" class="app-shell" style="display:none">""", 'ecran invite')

html = rempl(html,
u"""      <div class="sub">La même commune pour tout le monde, six essais pour la trouver. Chaque erreur dévoile un indice, et chaque essai dit à quelle distance tu es et dans quelle direction chercher. Nouvelle commune chaque jour à minuit.</div>""",
u"""      <div class="sub">La même commune pour tout le monde, six essais pour la trouver. Chaque erreur dévoile un indice, et chaque essai dit à quelle distance tu es et dans quelle direction chercher. Nouvelle commune chaque jour à minuit.</div>
      <p class="cdj-invite-bandeau" id="cdjInviteBandeau" hidden></p>""", 'bandeau')

ecrire('index.html', html)


# ---------------- app.js ----------------
js = lire('app.js')

# un lien partage ?onglet=cdj, sans compte : directement la partie
js = rempl(js,
u"""  else if(s) showGame(s);
  else if(dejaJoue()) showAuth();""",
u"""  else if(s) showGame(s);
  else if(new URLSearchParams(location.search).get('onglet') === 'cdj') montrerInviteCdj();
  else if(dejaJoue()) showAuth();""", 'arrivee par lien')

# pendant la partie sans compte, l'evenement « pas de session » ne doit pas
# afficher l'ecran de connexion par-dessus
js = rempl(js,
u"""    if(s2) showGame(s2);
    else { showAuth(); ecranAuth('principal'); }""",
u"""    if(s2) showGame(s2);
    else if(cdjInvite) return;
    else { showAuth(); ecranAuth('principal'); }""", 'auth sans session')

js = rempl(js,
u"""async function showGame(session_){
  cacherLanding();""",
u"""async function showGame(session_){
  if(cdjInvite) quitterInviteCdj();
  cacherLanding();""", 'entree dans le jeu')

js = rempl(js,
u"""document.addEventListener('visibilitychange', () => {
  if(!document.hidden && cdjEtat && cdjEtat.jour !== cdjJourParis()) chargerCdj();
});""",
u"""document.addEventListener('visibilitychange', () => {
  if(cdjInvite) return;
  if(!document.hidden && cdjEtat && cdjEtat.jour !== cdjJourParis()) chargerCdj();
});""", 'minuit')

js = rempl(js,
u"""  if(!svg || !FRANCE_OUTLINE || !cdjEtat) return;
  if(!cdjBornes){
    let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    for(const anneau of FRANCE_OUTLINE) for(const [lo, la] of anneau){""",
u"""  const contour = FRANCE_OUTLINE || cdjContour;
  if(!svg || !contour || !cdjEtat) return;
  if(!cdjBornes){
    let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    for(const anneau of contour) for(const [lo, la] of anneau){""", 'contour 1')
js = rempl(js,
u"""  for(const anneau of FRANCE_OUTLINE){
    h += `<path class="cdj-fr\"""",
u"""  for(const anneau of contour){
    h += `<path class="cdj-fr\"""", 'contour 2')

js = rempl(js,
u"""\\nterrafront.fr`;""",
u"""\\nterrafront.fr/?onglet=cdj`;""", 'lien partage')

# l'essai : sans compte, on renvoie toute la liste au serveur
js = rempl(js,
u"""    const { data, error } = await sb.rpc('cdj_essayer', { p_code: cdjChoix.code });
    if(error) throw error;
    cdjEtat = data;""",
u"""    let data, error;
    if(cdjInvite){
      const codes = cdjInviteCodes.concat(cdjChoix.code);
      ({ data, error } = await sb.rpc('cdj_invite', { p_codes: codes }));
      if(!error){ cdjInviteCodes = codes; cdjInviteGarder(data.jour); }
    } else {
      ({ data, error } = await sb.rpc('cdj_essayer', { p_code: cdjChoix.code }));
    }
    if(error) throw error;
    cdjEtat = data;""", 'essai invite')
js = rempl(js,
u"""    // la partie a pu changer ailleurs (autre appareil, minuit) : on la relit
    chargerCdj();""",
u"""    // la partie a pu changer ailleurs (autre appareil, minuit) : on la relit
    if(cdjInvite) chargerCdjInvite(); else chargerCdj();""", 'relecture')

# la fin : sans compte, l'invitation a s'inscrire remplace serie et partage
js = rempl(js,
u"""function renderCdjFin(){
  const z = document.getElementById('cdjFin');
  const e = cdjEtat;
  z.hidden = !e.fini;
  if(!e.fini) return;""",
u"""function renderCdjFin(){
  const z = document.getElementById('cdjFin');
  const e = cdjEtat;
  z.hidden = !e.fini;
  if(!e.fini) return;
  if(e.invite){ renderCdjFinInvite(z, e); return; }""", 'fin invite')

js = rempl(js,
u"""  document.getElementById('cdjNumero').textContent = '#' + e.numero;""",
u"""  document.getElementById('cdjNumero').textContent = '#' + e.numero;
  const bandeau = document.getElementById('cdjInviteBandeau');
  bandeau.hidden = !e.invite;
  if(e.invite) bandeau.innerHTML = `Tu joues <b>la commune d’hier</b>, sans compte. Celle d’aujourd’hui est réservée aux joueurs inscrits.`;""", 'bandeau rendu')

js = rempl(js,
u"""
initAuth();
""",
u"""
// ---------- Commune du jour sans compte (patch69) ----------
// Le panneau du jeu est deplace tel quel dans l'ecran invite, puis remis a
// sa place a la connexion : un seul jeu, un seul code d'affichage.
let cdjInvite = false;
let cdjInviteCodes = [];
let cdjContour = null;
let cdjPlace = null;
const CLE_CDJ_INVITE = 'tf-cdj-invite';

function cdjInviteGarder(jour){
  try { localStorage.setItem(CLE_CDJ_INVITE, JSON.stringify({ jour, codes: cdjInviteCodes })); } catch(e){}
}
function cdjInviteRelire(){
  try { const x = JSON.parse(localStorage.getItem(CLE_CDJ_INVITE) || 'null'); return x && Array.isArray(x.codes) ? x : null; }
  catch(e){ return null; }
}

async function chargerCdjInvite(){
  const garde = cdjInviteRelire();
  cdjInviteCodes = garde ? garde.codes : [];
  let { data, error } = await sb.rpc('cdj_invite', { p_codes: cdjInviteCodes });
  // ce qui etait garde concernait une autre journee : on repart de zero
  if(!error && garde && garde.jour !== data.jour){
    cdjInviteCodes = [];
    ({ data, error } = await sb.rpc('cdj_invite', { p_codes: [] }));
  }
  if(error){
    console.warn('TERRAFRONT commune du jour (invite) indisponible', error);
    cdjEtat = null;
  } else {
    cdjEtat = data;
    cdjInviteGarder(data.jour);
  }
  cdjDernierIndice = null;
  renderCdj();
}

function montrerInviteCdj(){
  const ecran = document.getElementById('cdjInvite');
  const panneau = document.getElementById('panel-cdj');
  if(!ecran || !panneau) return;
  if(!cdjPlace) cdjPlace = { parent: panneau.parentNode, suivant: panneau.nextSibling };
  document.getElementById('cdjInviteHote').appendChild(panneau);
  panneau.classList.add('active');
  cacherLanding();
  document.getElementById('authScreen').style.display = 'none';
  document.getElementById('gameScreen').style.display = 'none';
  ecran.hidden = false;
  cdjInvite = true;
  window.scrollTo(0, 0);
  if(!FRANCE_OUTLINE && !cdjContour){
    fetch('data/france-outline.json').then(r => r.json()).then(c => { cdjContour = c; renderCdjFrance(); }).catch(() => {});
  }
  cdjChargerNoms();
  chargerCdjInvite();
}

function quitterInviteCdj(){
  const ecran = document.getElementById('cdjInvite');
  const panneau = document.getElementById('panel-cdj');
  if(cdjPlace && panneau){
    cdjPlace.parent.insertBefore(panneau, cdjPlace.suivant);
    panneau.classList.remove('active');
  }
  if(ecran) ecran.hidden = true;
  cdjInvite = false;
  cdjEtat = null;
  cdjDernierIndice = null;
}

function renderCdjFinInvite(z, e){
  const r = e.reponse;
  const nb = e.essais.length;
  const qui = e.joueurs > 0
    ? `${e.trouves} joueur${e.trouves > 1 ? 's' : ''} sur ${e.joueurs} l’${e.trouves > 1 ? 'ont' : 'a'} trouvée.`
    : '';
  z.innerHTML = `<h2 class="${e.trouve ? 'gagne' : ''}">${e.trouve ? `Trouvée en ${nb}` : 'Pas trouvée'}</h2>
    <p>C’était <b>${echapperTexte(r.nom)}</b>, ${echapperTexte(DEPT_NAMES[r.dept] || r.dept)}, ${Number(r.pop).toLocaleString('fr-FR')} habitants. ${qui}</p>
    <div class="cdj-invite-appel">
      <b>La commune d’aujourd’hui t’attend.</b>
      <p>Crée un compte gratuit pour la jouer avec les autres, garder ta série et comparer tes résultats. Tu pourras aussi ouvrir des paquets et collectionner les vraies communes de France.</p>
      <div class="cdj-invite-actions">
        <button type="button" class="cdj-copier cdj-plein" data-cdj-inscription>Créer mon compte</button>
        <button type="button" class="cdj-copier" data-cdj-connexion>J’ai déjà un compte</button>
      </div>
    </div>`;
}

document.addEventListener('click', (ev) => {
  if(ev.target.closest('[data-cdj-invite]')){ montrerInviteCdj(); return; }
  const inscr = ev.target.closest('[data-cdj-inscription]');
  const conn = ev.target.closest('[data-cdj-connexion]');
  if(!inscr && !conn) return;
  quitterInviteCdj();
  quitterLanding(inscr ? 'inscription' : 'connexion');
});

initAuth();
""", 'module invite')

ecrire('app.js', js)


# ---------------- style.css ----------------
css = lire('style.css')
css += u"""

/* ---------- Commune du jour sans compte (patch69) ---------- */
.lp-invite{ display:flex; align-items:center; gap:6px 14px; flex-wrap:wrap; margin-top:14px; }
.lp-invite span{ font-size:.86rem; color:#8FA4BF; }
.lp-invite-btn{ font: inherit; font-weight:600; font-size:.95rem; padding:10px 16px; border-radius:10px; cursor:pointer;
  background:transparent; color: var(--c-legendaire); border:1px solid rgba(240,180,41,.55); }
.lp-invite-btn:focus-visible, .auth-invite:focus-visible{ outline:2px solid #fff; outline-offset:2px; }
.auth-invite{ display:block; width:100%; margin-top:14px; font: inherit; font-size:.9rem; font-weight:600; padding:10px; border-radius:10px;
  cursor:pointer; background:transparent; color: var(--c-legendaire); border:1px dashed rgba(240,180,41,.5); }
.cdj-invite-ecran{ min-height:100vh; padding:0 16px 40px; max-width:1180px; margin:0 auto; }
.cdj-invite-ecran[hidden]{ display:none; }
.cdj-invite-barre{ display:flex; align-items:center; justify-content:space-between; gap:12px; padding:18px 0 6px; }
#cdjInviteHote .tab-panel{ display:block; }
.cdj-invite-bandeau{ margin:12px 0 0; padding:10px 12px; border-radius:10px; font-size:.92rem; color: var(--brume);
  background: rgba(240,180,41,.08); border:1px solid rgba(240,180,41,.35); }
.cdj-invite-bandeau b{ color:#fff; }
.cdj-invite-appel{ display:flex; flex-direction:column; gap:8px; padding:14px; border-radius:12px;
  background: rgba(240,180,41,.08); border:1px solid rgba(240,180,41,.4); }
.cdj-invite-appel b{ font-family: var(--titre); font-size:22px; font-weight:800; letter-spacing:.01em; }
.cdj-invite-appel p{ margin:0; }
.cdj-invite-actions{ display:flex; gap:10px; flex-wrap:wrap; }
.cdj-copier.cdj-plein{ background: var(--c-legendaire); color: var(--nuit); }
"""
ecrire('style.css', css)

print(u'patch69 applique : index.html, app.js, style.css')
