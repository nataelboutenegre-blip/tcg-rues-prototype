# -*- coding: utf-8 -*-
u"""
patch150 — la bande-annonce de la saison 2, une fois par joueur, jusqu'à
dimanche 25 octobre 10 h (23 octobre).

- Fenêtre plein écran à l'ouverture du jeu, une fois le chargement fini,
  AVANT le mot d'accueil des nouveaux comptes (qui suit à la fermeture).
- Démarre sans le son (les navigateurs l'imposent) ; « Avec le son »
  relance depuis le début avec le son. « Passer » à tout moment ; à la fin
  « Revoir » (avec le son) ou « C'est parti ».
- Une fois par appareil (localStorage tf-bande-annonce-s2-vue, posé dès
  l'ouverture). Plus rien à partir du 25 octobre 10 h de Paris (9 h UTC :
  on repasse à l'heure d'hiver dans la nuit), ni si la saison 2 est ouverte.
- Réglage « réduire les animations » : pas de lecture automatique (éclair de
  l'explosion), la vidéo attend un appui.
- La vidéo (video/bande-annonce-s2.mp4, 3,6 Mo) et son image ne sont
  téléchargées que si la fenêtre s'ouvre.
- ?bandeannonce=1 dans l'adresse force l'affichage, pour tester.
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

for f in ('video/bande-annonce-s2.mp4', 'video/bande-annonce-s2.jpg'):
    assert os.path.exists(os.path.join(BASE, f)), u'%s manquant : copier la vidéo avant le patch' % f

# ---------------------------------------------------------------- index.html
h = lire('index.html')
assert 'voileBA' not in h, u'patch150 deja applique'
h = rempl(h, u'<div class="voile-accueil" id="voileAccueil" hidden>', u'''<div class="voile-ba" id="voileBA" hidden>
  <div class="ba" role="dialog" aria-modal="true" aria-label="Bande-annonce de la saison 2">
    <video id="baVideo" playsinline webkit-playsinline preload="auto"></video>
    <div class="ba-temps" aria-hidden="true"><i id="baBarre"></i></div>
    <button type="button" class="ba-passer" id="baPasser">Passer ✕</button>
    <button type="button" class="ba-son" id="baSon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 5 6 9H3v6h3l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/><path d="M18.5 5.5a9 9 0 0 1 0 13"/></svg>Avec le son</button>
    <div class="ba-fin" id="baFin" hidden><button type="button" class="ba-revoir" id="baRevoir">Revoir</button><button type="button" class="ba-go" id="baGo">C'est parti</button></div>
  </div>
</div>
<div class="voile-accueil" id="voileAccueil" hidden>''', 'html voile')
ecrire('index.html', h)

# ---------------------------------------------------------------- style.css
css = lire('style.css')
css = rempl(css, u"  /* ---------- Mot de passe oublié ---------- */", u"""  /* ---------- patch150 : bande-annonce de la saison 2 ---------- */
  .voile-ba{
    position:fixed; inset:0; z-index:72;
    background: rgba(3,8,18,0.94);
    display:flex; align-items:center; justify-content:center;
    padding: max(12px, env(safe-area-inset-top, 0px)) 12px max(12px, env(safe-area-inset-bottom, 0px));
    opacity:0; transition: opacity .22s;
  }
  .voile-ba.ouvert{ opacity:1; }
  .voile-ba[hidden], .ba-son[hidden], .ba-fin[hidden], .ba-passer[hidden]{ display:none; }
  .ba{
    position:relative; width: min(100%, calc((100dvh - 24px) * 9 / 16)); aspect-ratio: 9 / 16;
    border-radius:18px; overflow:hidden; background:#07101F;
    box-shadow: 0 0 0 1px rgba(240,180,41,0.35), 0 30px 80px rgba(0,0,0,0.6), 0 0 70px rgba(240,180,41,0.12);
    transform: scale(.96); transition: transform .25s cubic-bezier(.2,.8,.3,1.2);
  }
  .voile-ba.ouvert .ba{ transform:none; }
  .ba video{ width:100%; height:100%; object-fit:cover; display:block; background:#07101F; }
  .ba-passer{
    position:absolute; top:12px; right:12px;
    font-family: var(--texte); font-weight:600; font-size:0.9rem; color:#fff;
    background: rgba(7,16,31,0.62); border:1px solid rgba(255,255,255,0.28); border-radius:999px;
    padding:8px 14px; backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px); cursor:pointer;
  }
  .ba-son{
    position:absolute; left:50%; bottom:20px; transform:translateX(-50%);
    display:flex; align-items:center; gap:9px; white-space:nowrap;
    font-family: var(--titre); font-weight:800; font-size:1.3rem; letter-spacing:.02em;
    background: var(--c-legendaire); color: var(--encre);
    border:none; border-radius:999px; padding:11px 22px;
    box-shadow:0 5px 0 #B7791F, 0 10px 30px rgba(0,0,0,0.45); cursor:pointer;
  }
  .ba-son svg{ width:22px; height:22px; }
  .ba-son:active{ transform: translate(-50%, 4px); box-shadow:0 1px 0 #B7791F; }
  .ba-fin{ position:absolute; left:0; right:0; bottom:20px; display:flex; gap:10px; justify-content:center; padding:0 16px; }
  .ba-fin button{ font-family: var(--titre); font-weight:800; font-size:1.25rem; letter-spacing:.02em; border-radius:13px; padding:12px 18px; cursor:pointer; }
  .ba-revoir{ background: rgba(7,16,31,0.6); color:#fff; border:1px solid rgba(255,255,255,0.35); }
  .ba-go{ flex:1; max-width:230px; background: var(--c-legendaire); color: var(--encre); border:none; box-shadow:0 5px 0 #B7791F; }
  .ba-go:active{ transform: translateY(4px); box-shadow:0 1px 0 #B7791F; }
  .ba-temps{ position:absolute; left:0; right:0; top:0; height:3px; background: rgba(255,255,255,0.15); }
  .ba-temps i{ display:block; width:0; height:100%; background: var(--c-legendaire); }
  .ba-passer:focus-visible, .ba-son:focus-visible, .ba-fin button:focus-visible{ outline:2px solid #fff; outline-offset:3px; }
  @media (prefers-reduced-motion: reduce){
    .voile-ba, .ba{ transition:none; }
  }
  /* ---------- Mot de passe oublié ---------- */""", 'css')
ecrire('style.css', css)

# ---------------------------------------------------------------- app.js
js = lire('app.js')
assert 'peutEtreMontrerBandeAnnonce' not in js, u'patch150 deja applique'
js = rempl(js, u"""  renderNotifications();
  peutEtreAfficherAccueil();
  loadObjectifs();""", u"""  renderNotifications();
  peutEtreMontrerBandeAnnonce().then(peutEtreAfficherAccueil);   // patch150 : la bande-annonce d'abord
  loadObjectifs();""", 'appel')
js = rempl(js, u"""// ---------- Mot d'accueil, au tout premier lancement ----------""", u"""// ---------- patch150 : bande-annonce de la saison 2 ----------
// Une fois par appareil, jusqu'au dimanche 25 octobre 10 h de Paris (9 h UTC :
// on repasse a l'heure d'hiver cette nuit-la). La promesse se resout a la
// fermeture, pour que le mot d'accueil des nouveaux comptes passe apres.
const CLE_BA = 'tf-bande-annonce-s2-vue';
const FIN_BA = Date.UTC(2026, 9, 25, 9, 0, 0);
function peutEtreMontrerBandeAnnonce(){
  return new Promise((fini) => {
    const force = new URLSearchParams(location.search).get('bandeannonce') === '1';
    let vue = false;
    try{ vue = localStorage.getItem(CLE_BA) === '1'; } catch(e){}
    const voile = document.getElementById('voileBA'), video = document.getElementById('baVideo');
    if(!voile || !video || (!force && (SAISON2 || Date.now() >= FIN_BA || vue))){ fini(); return; }
    try{ localStorage.setItem(CLE_BA, '1'); } catch(e){}
    const son = document.getElementById('baSon'), fin = document.getElementById('baFin');
    const passer = document.getElementById('baPasser'), barre = document.getElementById('baBarre');
    const calme = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    video.poster = 'video/bande-annonce-s2.jpg';
    video.src = 'video/bande-annonce-s2.mp4';
    video.muted = true;
    voile.hidden = false;
    requestAnimationFrame(() => voile.classList.add('ouvert'));
    const majBarre = () => { if(video.duration) barre.style.width = (100 * video.currentTime / video.duration) + '%'; };
    video.addEventListener('timeupdate', majBarre);
    const lancer = (avecSon) => {
      video.muted = !avecSon;
      try{ video.currentTime = 0; } catch(e){}
      fin.hidden = true; passer.hidden = false; son.hidden = avecSon;
      const p = video.play();
      if(p && p.catch) p.catch(() => { son.hidden = false; });
    };
    // sans le son, la lecture automatique est permise ; avec « réduire les animations », on attend un appui
    if(!calme){ const p = video.play(); if(p && p.catch) p.catch(() => {}); }
    let ferme = false;
    const echap = (e) => { if(e.key === 'Escape') fermer(); };
    function fermer(){
      if(ferme) return; ferme = true;
      video.pause();
      voile.classList.remove('ouvert');
      document.removeEventListener('keydown', echap);
      setTimeout(() => {
        voile.hidden = true;
        video.removeEventListener('timeupdate', majBarre);
        video.removeAttribute('src'); video.load();
        fini();
      }, 230);
    }
    son.onclick = () => lancer(true);
    video.onended = () => { fin.hidden = false; son.hidden = true; passer.hidden = true; barre.style.width = '100%'; document.getElementById('baGo').focus(); };
    passer.onclick = fermer;
    document.getElementById('baGo').onclick = fermer;
    document.getElementById('baRevoir').onclick = () => lancer(true);
    document.addEventListener('keydown', echap);
    passer.focus();
  });
}

// ---------- Mot d'accueil, au tout premier lancement ----------""", 'fonction')
ecrire('app.js', js)
print(u'patch150 applique. Lancer : python3 maj-version.py')
