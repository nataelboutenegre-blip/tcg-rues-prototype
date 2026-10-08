# -*- coding: utf-8 -*-
u"""
patch85 — Ouverture de paquet plus fluide.

Mesuré au banc (processeur ralenti x4, comme un téléphone moyen, avec une
collection de 1 500 communes et 8 000 communes adverses) : chaque carte
retournée bloquait l'écran 60 à 240 ms. Causes :

1. la carte du Territoire se redessinait entièrement à chaque carte
   retournée (calcul de la triangulation des 9 500 communes, territoires,
   marqueurs) alors qu'elle n'était pas affichée. Elle attend maintenant
   qu'on ouvre l'onglet Territoire, comme le fait déjà la Collection ;
2. la pile était refabriquée avec les FACES complètes des cartes (dessin
   des courbes de niveau compris) à chaque carte, alors qu'on n'en voit
   que le dos. Elle ne fabrique plus que des dos ;
3. les lueurs et l'éclat des cartes rares animaient un filtre de
   luminosité, qui oblige le navigateur à repeindre toute la carte à
   chaque image. Ils animent maintenant l'opacité d'un calque, ce que le
   téléphone fait sans effort. Rendu visuel identique à l'œil ;
4. chaque son de déchirure ou de carte fabriquait son propre bruit blanc
   (des dizaines de milliers de tirages au hasard). Un seul bruit est
   fabriqué au premier son, puis réutilisé.
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

# 1. la carte attend qu'on la regarde
js = rempl(js,
u'''function renderMapOverlay(){
  if(canvasActif()){''',
u'''function renderMapOverlay(){
  // patch85 : onglet ferme, on redessinera a l'ouverture (une seule fois)
  if(rendreALOuverture('territoire', renderMapOverlay)) return;
  if(canvasActif()){''', 'renderMapOverlay')
js = rempl(js,
u'''function demanderDessin(){
  if(!canvasActif() || CV.dessinPlanifie) return;''',
u'''function demanderDessin(){
  if(!canvasActif() || CV.dessinPlanifie) return;
  if(rendreALOuverture('territoire', demanderDessin)) return;   // patch85''', 'demanderDessin')

# 2. la pile ne fabrique que des dos
js = rempl(js,
u'''  pileDraws.forEach((d, i) => {
    const dos = makeCardEl(d, () => {});''',
u'''  pileDraws.forEach((d, i) => {
    const dos = makeDosEl(d);''', 'pile')
js = rempl(js,
u'''let pendingFlips = 0;''',
u'''// Le dos seul, pour la pile : la face n'y est jamais visible (patch85)
function makeDosEl(draw){
  const wrap = document.createElement('div');
  wrap.className = 'card ' + draw.tier.id;
  wrap.innerHTML = `
    <div class="card-inner">
      <div class="face face-back">
        ${DOS_MOTIF_SVG}
        <span class="dos-coin hg"></span><span class="dos-coin hd"></span><span class="dos-coin bg"></span><span class="dos-coin bd"></span>
        <div class="dos-embleme">${ICONE_EPINGLE}</div>
      </div>
    </div>`;
  return wrap;
}

let pendingFlips = 0;''', 'makeDosEl')
# 4. un seul bruit blanc, reutilise
js = rempl(js,
u'''    const n = Math.floor(ctx.sampleRate * duree), b = ctx.createBuffer(1, n, ctx.sampleRate), d = b.getChannelData(0);
    for(let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1;
    const s = ctx.createBufferSource(), fl = ctx.createBiquadFilter(), g = ctx.createGain(), t = ctx.currentTime;
    s.buffer = b; fl.type = type || 'bandpass'; fl.Q.value = 0.8;''',
u'''    // patch85 : une seconde de bruit fabriquee une fois, on en lit un morceau
    if(!bruitBlanc){
      const n = ctx.sampleRate, d = (bruitBlanc = ctx.createBuffer(1, n, ctx.sampleRate)).getChannelData(0);
      for(let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1;
    }
    const s = ctx.createBufferSource(), fl = ctx.createBiquadFilter(), g = ctx.createGain(), t = ctx.currentTime;
    s.buffer = bruitBlanc; fl.type = type || 'bandpass'; fl.Q.value = 0.8;''', 'bruit')
js = rempl(js,
u'''    s.connect(fl); fl.connect(g); g.connect(maitre); s.start(t);
  };''',
u'''    s.connect(fl); fl.connect(g); g.connect(maitre);
    s.start(t, Math.random() * Math.max(0, 1 - duree), Math.min(duree, 1));
  };''', 'bruit depart')
js = rempl(js,
u'''  const bruit = (duree, f1, f2, vol, type) => {''',
u'''  let bruitBlanc = null;
  const bruit = (duree, f1, f2, vol, type) => {''', 'bruit cache')
ecrire('app.js', js)

# 3. des animations d'opacite plutot que de filtre
css = lire('style.css')
css = rempl(css,
u'''.ouv-dos.lueur-rare .face-back{ box-shadow: 0 0 0 2px var(--c-rare), 0 0 26px 4px rgba(47,124,246,.75); animation: ouvPulse 1.1s ease-in-out infinite; }
.ouv-dos.lueur-leg .face-back{ box-shadow: 0 0 0 2px var(--c-legendaire), 0 0 34px 8px rgba(240,180,41,.8); animation: ouvPulse .8s ease-in-out infinite; }
@keyframes ouvPulse{ 50%{ filter: brightness(1.35); } }
.card.ouv-eclat .face-front{ animation: ouvEclat .7s ease-out; }
@keyframes ouvEclat{ 0%{ filter: brightness(2.2); } 100%{ filter: brightness(1); } }''',
u'''/* patch85 : lueur et eclat par opacite d'un calque (plus de filtre anime) */
.ouv-dos.lueur-rare .face-back{ box-shadow: 0 0 0 2px var(--c-rare), 0 0 26px 4px rgba(47,124,246,.75); }
.ouv-dos.lueur-leg .face-back{ box-shadow: 0 0 0 2px var(--c-legendaire), 0 0 34px 8px rgba(240,180,41,.8); }
.ouv-dos.lueur-rare .face-back::after, .ouv-dos.lueur-leg .face-back::after{
  content:''; position:absolute; inset:0; border-radius:inherit; pointer-events:none;
  background: radial-gradient(circle at 50% 42%, rgba(255,255,255,.5), rgba(255,255,255,.12) 70%);
  opacity:0; will-change:opacity; animation: ouvPulse 1.1s ease-in-out infinite; }
.ouv-dos.lueur-leg .face-back::after{ background: radial-gradient(circle at 50% 42%, rgba(255,236,170,.6), rgba(255,236,170,.14) 70%); animation-duration:.8s; }
@keyframes ouvPulse{ 50%{ opacity:.55; } }
.card.ouv-eclat .face-front::after{
  content:''; position:absolute; inset:0; border-radius:inherit; pointer-events:none; z-index:5;
  background: radial-gradient(circle at 50% 40%, #fff, rgba(255,255,255,.75) 60%, rgba(255,255,255,.5));
  opacity:0; will-change:opacity; animation: ouvEclat .7s ease-out; }
@keyframes ouvEclat{ 0%{ opacity:.85; } 100%{ opacity:0; } }''', 'animations')
css = rempl(css,
u'''.ouv-rangee .card, .ouv-dos .face-back, .card.ouv-eclat .face-front,''',
u'''.ouv-rangee .card, .ouv-dos .face-back, .card.ouv-eclat .face-front,
  .ouv-dos .face-back::after, .card.ouv-eclat .face-front::after,''', 'reduced motion')
ecrire('style.css', css)
print(u'patch85 : OK')
