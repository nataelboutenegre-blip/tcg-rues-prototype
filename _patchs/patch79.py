# -*- coding: utf-8 -*-
u"""
patch79 — deux corrections du 7 octobre.

1. Fiche d'un joueur : « 0 perdue au combat » pour tout le monde. La fiche
   lisait p.perdues, un champ que profil_joueur n'envoie pas (il s'appelle
   communes_perdues). Corrigé côté jeu, rien à changer en base.
2. La bulle qui s'ouvre au clic sur une commune de la carte se déplace :
   on l'attrape par son en-tête (souris ou doigt). Sur téléphone elle garde
   toute la largeur et se déplace de haut en bas. Une fois déplacée, elle
   reste à sa place pour les communes suivantes, jusqu'à sa fermeture.
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

js = lire('app.js')

# 1. perdues au combat
js = rempl(js,
u'''<span class="pr-puce">🛡️ ${nb(p.perdues)} perdue${p.perdues > 1 ? 's' : ''} au combat</span>''',
u'''<span class="pr-puce">🛡️ ${nb(p.communes_perdues)} perdue${p.communes_perdues > 1 ? 's' : ''} au combat</span>''', 'perdues')

# 2. bulle déplaçable
js = rempl(js,
u'''  panneauCommune = null;
  panneauAncre = null;
}''',
u'''  panneauCommune = null;
  panneauAncre = null;
  panneauDeplace = null;
}''', 'fermer')
js = rempl(js,
u'''let panneauAncre = null;''',
u'''let panneauAncre = null;
// Position choisie par le joueur en faisant glisser la bulle (patch79).
// Tant qu'elle est ouverte, la bulle y reste, même pour une autre commune.
let panneauDeplace = null;''', 'etat')
js = rempl(js,
u'''function recadrerPanneau(el){
  if(!el || el.hidden || surTelephone()) return;''',
u'''function recadrerPanneau(el){
  if(el && !el.hidden && panneauDeplace){ poserPanneauDeplace(el); return; }
  if(!el || el.hidden || surTelephone()) return;''', 'recadrer')
js = rempl(js,
u'''function placerPanneau(el, xCss, yCss){
  if(surTelephone()){ el.style.left = ''; el.style.top = ''; montrerPanneau(el); return; }''',
u'''function placerPanneau(el, xCss, yCss){
  if(panneauDeplace){ poserPanneauDeplace(el); return; }
  if(surTelephone()){ el.style.left = ''; el.style.top = ''; el.style.bottom = ''; montrerPanneau(el); return; }''', 'placer')
js = rempl(js,
u'''// Les actions renvoient vers l'onglet concerne, la recherche deja remplie sur''',
u'''// ----- déplacer la bulle (patch79) -----
// La position voulue, remise dans le cadre de la carte. Sur téléphone, la
// bulle garde toute la largeur : seul le haut change.
function poserPanneauDeplace(el){
  const wrap = document.getElementById('mapWrap');
  if(!wrap || !panneauDeplace) return;
  const b = el.getBoundingClientRect(), marge = 8;
  const haut = Math.max(marge, Math.min(panneauDeplace.top, wrap.clientHeight - b.height - marge));
  el.style.top = Math.round(haut) + 'px';
  el.style.bottom = 'auto';
  if(surTelephone()){ el.style.left = ''; return; }
  const gauche = Math.max(marge, Math.min(panneauDeplace.left, wrap.clientWidth - b.width - marge));
  el.style.left = Math.round(gauche) + 'px';
}
(function(){
  const el = document.getElementById('mapPanneau');
  if(!el) return;
  let geste = null;
  el.addEventListener('pointerdown', (e) => {
    // on attrape par l'en-tête, ou par la petite barre tout en haut
    const enHaut = e.clientY - el.getBoundingClientRect().top < 20;
    if(!(enHaut || e.target.closest('.pc-tete')) || e.target.closest('button, a, input, select, [data-pc], [data-profil]')) return;
    if(e.pointerType === 'mouse' && e.button !== 0) return;
    const wrap = document.getElementById('mapWrap');
    const rw = wrap.getBoundingClientRect(), re = el.getBoundingClientRect();
    geste = { id: e.pointerId, dx: e.clientX - (re.left - rw.left - wrap.clientLeft), dy: e.clientY - (re.top - rw.top - wrap.clientTop) };
    try { el.setPointerCapture(e.pointerId); } catch(err){}
    el.classList.add('pc-glisse');
    e.preventDefault();
  });
  el.addEventListener('pointermove', (e) => {
    if(!geste || geste.id !== e.pointerId) return;
    panneauDeplace = { left: e.clientX - geste.dx, top: e.clientY - geste.dy };
    poserPanneauDeplace(el);
  });
  const fin = (e) => { if(!geste || geste.id !== e.pointerId) return; geste = null; el.classList.remove('pc-glisse'); };
  el.addEventListener('pointerup', fin);
  el.addEventListener('pointercancel', fin);
})();

// Les actions renvoient vers l'onglet concerne, la recherche deja remplie sur''', 'glisser')
ecrire('app.js', js)

css = lire('style.css')
MARQUE = u'/* ---------- Bulle de la carte déplaçable (patch79) ---------- */'
assert MARQUE not in css, u'patch79 déjà passé'
css = css.rstrip('\n') + u'\n\n' + MARQUE + u'''
.pc{ padding-top:20px; }
.pc::before{ content:''; position:absolute; left:50%; top:7px; width:36px; height:4px; margin-left:-18px;
  border-radius:2px; background: rgba(169,188,212,.35); }
.pc-tete{ cursor:grab; touch-action:none; user-select:none; -webkit-user-select:none; }
.pc-tete button, .pc-tete a, .pc-tete [data-profil]{ cursor:pointer; }
.pc.pc-glisse{ animation:none; box-shadow:0 24px 60px rgba(0,0,0,.6); }
.pc.pc-glisse .pc-tete{ cursor:grabbing; }
'''
ecrire('style.css', css)
print(u'patch79 : OK')
