# -*- coding: utf-8 -*-
u"""
patch156 — « Glisse pour acheter » : le paquet acheté ne part plus d'un clic,
il faut faire glisser le bouton jusqu'au bout (aperçu validé le 24 octobre).

- L'achat part à 92 % de la course ; lâché avant, le bouton revient et rien
  n'est payé. Un clic ou Entrée sur le bouton ne fait rien.
- Clavier : flèche droite pour pousser (6 appuis), flèche gauche ou Échap pour
  revenir.
- Impossible (solde, 5 par jour, paquet en cours) : le bouton ne bouge pas et
  le texte dit pourquoi.
- Le paquet gratuit garde son bouton. En Front, rien ne s'achète : caché.
- #openBuyBtn reste le bouton (la poignée) : disabled marche comme avant.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)

FLECHE = u'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h12M13 6l6 6-6 6"/></svg>'

h = lire('index.html')
assert 'glisserAchat' not in h, u'patch156 deja applique'
h = rempl(h, u'''        <button class="open-btn secondary" id="openBuyBtn">Acheter un paquet (200 pts)</button>''',
u'''        <div class="glisser" id="glisserAchat">
          <span class="glisser-rempli" id="glisserRempli"></span>
          <span class="glisser-texte" id="glisserTexte">Glisse pour acheter<small>200 pts</small></span>
          <button type="button" class="glisser-bouton" id="openBuyBtn" aria-label="Glisse jusqu'au bout pour acheter un paquet à 200 points">''' + FLECHE + u'''</button>
        </div>''', 'bouton')
ecrire('index.html', h)

css = lire('style.css')
css = rempl(css, u"  /* ---------- Mot de passe oublié ---------- */", u"""  /* ---------- patch156 : glisser pour acheter ---------- */
  .glisser{ position:relative; width:min(330px, 100%); height:48px; border-radius:14px; user-select:none; -webkit-user-select:none; overflow:hidden;
    background: rgba(7,16,31,.55); box-shadow: inset 0 0 0 2px rgba(169,188,212,.35), 0 5px 0 rgba(0,0,0,.25); align-self:center; }
  .glisser-rempli{ position:absolute; left:0; top:0; bottom:0; width:0; border-radius:14px; background: linear-gradient(90deg, rgba(240,180,41,.08), rgba(240,180,41,.32)); pointer-events:none; }
  .glisser-texte{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; padding-left:52px; padding-right:12px;
    font-family: var(--titre); font-weight:800; font-size:1.1rem; letter-spacing:.03em; white-space:nowrap; pointer-events:none;
    background: linear-gradient(90deg, rgba(255,255,255,.45) 0%, rgba(255,255,255,.45) 40%, #fff 50%, rgba(255,255,255,.45) 60%, rgba(255,255,255,.45) 100%);
    background-size:300% 100%; -webkit-background-clip:text; background-clip:text; color:transparent; animation: glisserReflet 2.6s linear infinite; }
  .glisser-texte small{ font-family: var(--texte); font-weight:600; font-size:.8rem; margin-left:8px; letter-spacing:0; }
  @keyframes glisserReflet{ from{ background-position:100% 0; } to{ background-position:-50% 0; } }
  .glisser-bouton{ position:absolute; left:4px; top:4px; width:40px; height:40px; padding:0; border:none; border-radius:11px; background: var(--c-legendaire); color: var(--encre);
    display:grid; place-items:center; box-shadow:0 3px 0 #B7791F, 0 4px 12px rgba(0,0,0,.35); cursor:grab; touch-action:none; }
  .glisser-bouton:active:not(:disabled){ cursor:grabbing; }
  .glisser-bouton:focus-visible{ outline:none; box-shadow:0 0 0 3px #fff, 0 3px 0 #B7791F; }
  .glisser-bouton svg{ width:22px; height:22px; pointer-events:none; }
  .glisser.retour .glisser-bouton, .glisser.retour .glisser-rempli{ transition: transform .35s cubic-bezier(.3,1.5,.5,1), width .35s cubic-bezier(.3,1.5,.5,1); }
  .glisser.fait{ box-shadow: inset 0 0 0 2px rgba(61,214,140,.7), 0 5px 0 rgba(0,0,0,.25); }
  .glisser.fait .glisser-rempli{ background: linear-gradient(90deg, rgba(61,214,140,.15), rgba(61,214,140,.35)); }
  .glisser.fait .glisser-texte{ animation:none; color:#9CF7C9; background:none; padding-left:12px; }
  .glisser.fait .glisser-bouton{ background:#3DD68C; box-shadow:0 3px 0 #1E8E58; }
  .glisser.off{ opacity:.45; }
  .glisser.off .glisser-texte{ animation:none; color: rgba(255,255,255,.75); background:none; }
  .glisser.off .glisser-bouton{ background:#5B6673; box-shadow:none; cursor:default; }
  body.mode-front #glisserAchat{ display:none !important; }
  @media (prefers-reduced-motion: reduce){
    .glisser-texte{ animation:none; color:#fff; background:none; }
    .glisser.retour .glisser-bouton, .glisser.retour .glisser-rempli{ transition:none; }
  }
  /* ---------- Mot de passe oublié ---------- */""", 'css')
ecrire('style.css', css)

js = lire('app.js')
assert 'glisserAchat' not in js, u'patch156 deja applique'
js = rempl(js, u"""  document.getElementById('openBuyBtn').disabled = paquetEnCours || achetesJour >= 5 || packStatusCache.solde < 200;""",
u"""  document.getElementById('openBuyBtn').disabled = paquetEnCours || achetesJour >= 5 || packStatusCache.solde < 200;
  majGlisserAchat(paquetEnCours ? 'Paquet en cours…' : achetesJour >= 5 ? '5 paquets achetés aujourd\\'hui'
    : packStatusCache.solde < 200 ? 'Solde insuffisant' : null);   // patch156""", 'etat')
js = rempl(js, u"""document.getElementById('openBuyBtn').addEventListener('click', () => openPack('achete'));""",
u"""// ---------- patch156 : glisser pour acheter ----------
// Le paquet achete part seulement quand la poignee arrive au bout (92 %).
// Un clic, Entree ou Espace ne font rien : c'est tout l'interet.
var GLISSER = (() => {
  const zone = document.getElementById('glisserAchat');
  const bouton = document.getElementById('openBuyBtn');
  const rempli = document.getElementById('glisserRempli');
  const texte = document.getElementById('glisserTexte');
  const FLECHE = bouton.innerHTML;
  const COCHE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12l5 5 9-10"/></svg>';
  const SEUIL = 0.92;
  let depart = null, x = 0, fini = false, raison = null;
  const course = () => Math.max(1, zone.clientWidth - bouton.offsetWidth - 8);
  const poser = (v) => {
    x = Math.max(0, Math.min(course(), v));
    bouton.style.transform = 'translateX(' + x + 'px)';
    rempli.style.width = x > 0 ? (x + bouton.offsetWidth / 2 + 4) + 'px' : '0';
  };
  const revenir = () => { zone.classList.add('retour'); poser(0); setTimeout(() => zone.classList.remove('retour'), 360); };
  const texteRepos = () => { texte.innerHTML = raison ? echapperTexte(raison) : 'Glisse pour acheter<small>200 pts</small>'; };
  const valider = () => {
    fini = true; depart = null;
    poser(course());
    zone.classList.add('fait');
    texte.textContent = 'Paquet acheté !';
    bouton.innerHTML = COCHE;
    try{ if(navigator.vibrate) navigator.vibrate(30); }catch(e){}
    openPack('achete');
    setTimeout(() => {
      fini = false;
      zone.classList.remove('fait');
      bouton.innerHTML = FLECHE;
      texteRepos();
      revenir();
    }, 1300);
  };
  bouton.addEventListener('pointerdown', (e) => {
    if(fini || bouton.disabled) return;
    depart = e.clientX - x;
    try{ bouton.setPointerCapture(e.pointerId); }catch(err){}
    zone.classList.remove('retour');
  });
  bouton.addEventListener('pointermove', (e) => { if(depart !== null) poser(e.clientX - depart); });
  const lacher = () => {
    if(depart === null) return;
    depart = null;
    if(x >= course() * SEUIL) valider(); else revenir();
  };
  bouton.addEventListener('pointerup', lacher);
  bouton.addEventListener('pointercancel', lacher);
  bouton.addEventListener('keydown', (e) => {
    if(fini || bouton.disabled) return;
    if(e.key === 'ArrowRight'){ e.preventDefault(); zone.classList.remove('retour'); poser(x + course() / 6); if(x >= course() * SEUIL) valider(); }
    else if(e.key === 'ArrowLeft' || e.key === 'Escape'){ e.preventDefault(); revenir(); }
  });
  bouton.addEventListener('blur', () => { if(!fini && depart === null && x > 0) revenir(); });
  return {
    maj(r){
      raison = r;
      if(fini || depart !== null) return;   // pas pendant un geste
      zone.classList.toggle('off', !!r);
      texteRepos();
      if(r && x > 0) revenir();
    }
  };
})();
function majGlisserAchat(raison){ if(typeof GLISSER !== 'undefined' && GLISSER) GLISSER.maj(raison); }""", 'glisser')
ecrire('app.js', js)
print(u'patch156 applique. Lancer : python3 maj-version.py')
