# -*- coding: utf-8 -*-
u"""
patch188 — Terra et Front se distinguent d'un coup d'oeil (apercu valide le
26 octobre, « c'est parfait ») :
 - une lueur de la couleur du mode en haut de la page (vert Terra, rouge Front) ;
 - un liseré lumineux sur la barre des onglets (a droite sur ordinateur,
   en haut de la barre du bas sur telephone) ;
 - un surtitre au-dessus du titre de chaque page :
   « Mode Terra · ta collection » / « Mode Front · la conquete » ;
 - le paquet qui attend porte un halo de la couleur du mode ;
 - au changement de mode, un balayage d'environ 1 s avec le nom du mode
   (coupe si l'appareil demande moins d'animations).
Aucun SQL. Rien ne change tant que SAISON2 = false (classes mode-terra/front).
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

js = lire('app.js')
assert 'modeBalayage' not in js, u'patch188 deja applique'
js = rempl(js, u"""    modeJeu = b.dataset.mode;
    try { localStorage.setItem('tf-mode', modeJeu); } catch(err){}
    appliquerMode();
  });""", u"""    modeJeu = b.dataset.mode;
    try { localStorage.setItem('tf-mode', modeJeu); } catch(err){}
    appliquerMode();
    balayerMode();   // patch188
  });""", 'bascule')
js = rempl(js, u"""function majBascule(){""", u"""// patch188 : le balayage au changement de mode
function balayerMode(){
  let el = document.getElementById('modeBalayage');
  if(!el){
    el = document.createElement('div');
    el.id = 'modeBalayage';
    el.setAttribute('aria-hidden', 'true');
    document.body.appendChild(el);
  }
  const terra = modeJeu === 'terra';
  el.className = terra ? 'terra' : 'front';
  el.innerHTML = `<div><b>${terra ? 'Terra' : 'Front'}</b><small>${terra ? 'Ta collection' : 'La conquête'}</small></div>`;
  el.classList.remove('passe'); void el.offsetWidth; el.classList.add('passe');
}
function majBascule(){""", 'balayage')
ecrire('app.js', js)

css = lire('style.css')
assert 'patch188' not in css, u'patch188 deja applique (css)'
css += u"""

/* ---------- patch188 : chaque mode a son ambiance ---------- */
body.mode-terra{ --mode:#5FD39D; --mode-fonce:#1E5A44; --mode-lueur:rgba(30,110,84,.32); }
body.mode-front{ --mode:#FF8A8E; --mode-fonce:#5A1E26; --mode-lueur:rgba(140,34,52,.34); }
body.mode-terra .content, body.mode-front .content{
  background: radial-gradient(110% 420px at 55% -60px, var(--mode-lueur), transparent 72%) no-repeat;
  transition: background .5s ease; }
body.mode-terra .sidebar, body.mode-front .sidebar{
  box-shadow: inset -3px 0 0 var(--mode), 6px 0 22px -10px var(--mode); transition: box-shadow .4s ease; }
@media (max-width: 720px){
  body.mode-terra .sidebar, body.mode-front .sidebar{ box-shadow: inset 0 3px 0 var(--mode), 0 -6px 22px -10px var(--mode); }
}
body.mode-terra .tab-panel > h1::before, body.mode-front .tab-panel > h1::before{
  display:block; margin-bottom:6px; padding-left:26px;
  font-family: var(--texte); font-size:.74rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; line-height:1.3;
  color: var(--mode); background: linear-gradient(var(--mode), var(--mode)) left center / 18px 2px no-repeat; }
body.mode-terra .tab-panel > h1::before{ content:"Mode Terra · ta collection"; }
body.mode-front .tab-panel > h1::before{ content:"Mode Front · la conquête"; }
body.mode-terra #packZone .paquet[data-pret], body.mode-front #packZone .paquet[data-pret]{
  filter: drop-shadow(0 18px 24px rgba(0,0,0,0.5)) drop-shadow(0 0 22px var(--mode-lueur)); }

#modeBalayage{ position:fixed; inset:0; z-index:200; pointer-events:none; display:grid; place-items:center; opacity:0; --mode:#5FD39D; --mode-fonce:#1E5A44; }
#modeBalayage.front{ --mode:#FF8A8E; --mode-fonce:#5A1E26; }
#modeBalayage::before{ content:""; position:absolute; inset:0; transform:translateX(-100%);
  background: linear-gradient(100deg, transparent 18%, rgba(0,0,0,0) 20%, color-mix(in srgb, var(--mode-fonce) 92%, transparent) 42%, color-mix(in srgb, var(--mode-fonce) 92%, transparent) 58%, transparent 82%); }
#modeBalayage > div{ position:relative; text-align:center; }
#modeBalayage b{ display:block; font-family: var(--titre); font-weight:900; font-size: clamp(3.2rem, 11vw, 6rem); letter-spacing:.08em; text-transform:uppercase; color: var(--mode); text-shadow: 0 0 30px var(--mode); line-height:1; }
#modeBalayage small{ display:block; margin-top:6px; font-size:.82rem; letter-spacing:.2em; text-transform:uppercase; color:#fff; }
#modeBalayage.passe{ animation: tf-mode-apparait .9s ease both; }
#modeBalayage.passe::before{ animation: tf-mode-glisse .9s cubic-bezier(.6,0,.3,1) both; }
@keyframes tf-mode-glisse{ 0%{ transform:translateX(-100%); } 45%,55%{ transform:translateX(0); } 100%{ transform:translateX(100%); } }
@keyframes tf-mode-apparait{ 0%{ opacity:0; } 25%,70%{ opacity:1; } 100%{ opacity:0; } }
@media (prefers-reduced-motion: reduce){
  #modeBalayage.passe, #modeBalayage.passe::before{ animation:none; }
  body.mode-terra .content, body.mode-front .content, body.mode-terra .sidebar, body.mode-front .sidebar{ transition:none; }
}
"""
ecrire('style.css', css)
print(u'patch188 applique. Lancer : python3 maj-version.py')
