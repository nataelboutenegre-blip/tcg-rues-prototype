# -*- coding: utf-8 -*-
u"""
patch122 — écran de chargement + démarrage plus rapide (idées de Maroli et Wally).

1. Écran de chargement : courbes de niveau qui se tracent autour de
   l'épingle, nom TerraFront, barre qui suit les vraies étapes (carte, tes
   communes, les autres joueurs, tes paquets), une astuce. Il couvre le jeu
   tant qu'il n'est pas prêt : plus de bouton « Ouvrir un paquet » cliquable
   trop tôt. Fondu à la fin ; disparaît au plus tard après 15 s. Visiteur
   non connecté : disparaît dès que la page d'accueil ou la connexion
   s'affiche.
   Les trois scripts passent en « defer » (même ordre d'exécution) : l'écran
   s'affiche tout de suite au lieu d'attendre supabase.js et d3.
2. Chargement en parallèle : toutesLesLignes demandait les paquets de 1 000
   lignes l'un après l'autre (≈ 19 allers-retours pour les communes des
   autres en fin de saison 1). Elle en demande maintenant 6 à la fois, triés
   pour qu'aucune ligne ne saute d'un paquet à l'autre.
3. Mesure : la console du navigateur affiche la durée de chaque étape
   (« [démarrage] … ms »). Rien n'est envoyé nulle part.
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

def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)

js = lire('app.js')
css = lire('style.css')
html = lire('index.html')
assert 'dmEtape' not in js, u'patch122 deja applique'

EPINGLE = u'<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>'

# ---------------------------------------------------------------- index.html
html = rempl(html, u"""<body>
""", u"""<body>
<div class="demarrage" id="demarrage" role="status" aria-live="polite">
  <div class="dm-scene"><svg viewBox="0 0 200 200" id="dmCourbes" aria-hidden="true"></svg>
    <div class="dm-epingle">""" + EPINGLE + u"""</div></div>
  <div class="dm-nom">Terra<b>Front</b></div>
  <div class="dm-etat"><div class="dm-barre"><i id="dmBarre"></i></div><span class="dm-texte" id="dmTexte">Chargement…</span></div>
  <p class="dm-astuce"><b>Astuce :</b> marque d'une ⭐ les 5 communes que tu veux garder à la fin de la saison.</p>
</div>
""", u'ecran')
html = rempl(html, u'<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.2/dist/umd/supabase.js"></script>',
                   u'<script defer src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.2/dist/umd/supabase.js"></script>', u'defer supabase')
html = rempl(html, u'<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>',
                   u'<script defer src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>', u'defer d3')
html = rempl(html, u'<script src="app.js?v=', u'<script defer src="app.js?v=', u'defer app')

# ---------------------------------------------------------------- style.css
css += u"""
/* ---------- patch122 : ecran de chargement ---------- */
.demarrage{ position:fixed; inset:0; z-index:9999; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:22px;
  background:radial-gradient(120% 80% at 50% 38%, #18305A 0%, var(--nuit) 62%); color:#fff; font-family:var(--texte); transition:opacity .45s ease; }
.demarrage.fini{ opacity:0; pointer-events:none; }
.dm-scene{ position:relative; width:min(240px,62vw); aspect-ratio:1; }
.dm-scene > svg{ position:absolute; inset:0; width:100%; height:100%; overflow:visible; }
.dm-anneau{ fill:none; stroke:var(--c-legendaire); stroke-width:1.1; stroke-dasharray:1; stroke-dashoffset:1; animation:dmTrace 2.4s ease-out forwards; }
@keyframes dmTrace{ to{ stroke-dashoffset:0; } }
.dm-epingle{ position:absolute; left:50%; top:50%; width:74px; height:74px; margin:-37px 0 0 -37px; border-radius:50%; background:var(--nuit);
  box-shadow:0 0 0 2px var(--c-legendaire), 0 0 0 8px rgba(15,31,56,.92), 0 0 0 9.5px rgba(240,180,41,.4); display:flex; align-items:center; justify-content:center;
  animation:dmPouls 1.8s ease-in-out infinite; }
.dm-epingle svg{ width:34px; height:34px; stroke:var(--c-legendaire); }
@keyframes dmPouls{ 50%{ box-shadow:0 0 0 2px var(--c-legendaire), 0 0 0 8px rgba(15,31,56,.92), 0 0 0 9.5px rgba(240,180,41,.4), 0 0 34px rgba(240,180,41,.35); } }
.dm-nom{ font-family:var(--titre); font-weight:900; font-size:2.6rem; letter-spacing:.02em; line-height:1; }
.dm-nom b{ color:var(--c-legendaire); font-weight:900; }
.dm-etat{ display:flex; flex-direction:column; align-items:center; gap:10px; width:min(260px,70vw); }
.dm-barre{ width:100%; height:4px; border-radius:2px; background:rgba(169,188,212,.16); overflow:hidden; }
.dm-barre i{ display:block; height:100%; width:4%; background:var(--c-legendaire); border-radius:2px; transition:width .5s ease; }
.dm-texte{ font-size:.82rem; color:var(--brume); min-height:1.2em; }
.dm-astuce{ position:absolute; bottom:calc(28px + env(safe-area-inset-bottom,0px)); left:16px; right:16px; text-align:center; font-size:.78rem; color:var(--brume); opacity:.8; max-width:46ch; margin:0 auto; line-height:1.5; }
.dm-astuce b{ color:#fff; font-weight:600; }
@media (prefers-reduced-motion:reduce){ .dm-anneau{ animation:none; stroke-dashoffset:0; } .dm-epingle{ animation:none; } }
"""

# ---------------------------------------------------------------- app.js : ecran
js = rempl(js, u"""async function initAuth(){
  const { data: { session: s } } = await sb.auth.getSession();""", u"""// ---------- patch122 : ecran de chargement ----------
const DM_T0 = performance.now();
let dmFini = false;
function dmMesure(etiquette){ try{ console.info(`[démarrage] ${etiquette} : ${Math.round(performance.now() - DM_T0)} ms`); }catch(e){} }
function dmEtape(pct, texte){
  if(dmFini) return;
  const b = document.getElementById('dmBarre'), t = document.getElementById('dmTexte');
  if(b) b.style.width = pct + '%';
  if(t) t.textContent = texte;
}
function dmFin(){
  if(dmFini) return;
  dmFini = true;
  dmMesure('jeu affiché');
  const el = document.getElementById('demarrage');
  if(!el) return;
  dmEtape(100, 'Prêt');
  el.classList.add('fini');
  setTimeout(() => el.remove(), 600);
}
(function dmCourbes(){
  const svg = document.getElementById('dmCourbes');
  if(!svg) return;
  const R = aleatoireStable(hashTexte('demarrage')), k1 = 2 + Math.floor(R() * 3), k2 = 3 + Math.floor(R() * 4);
  const p1 = R() * 6.28, p2 = R() * 6.28, a1 = .08 + R() * .1, a2 = .04 + R() * .06;
  let h = '';
  for(let i = 1; i <= 7; i++){
    const r = i * 12.5, pts = [];
    for(let k = 0; k < 90; k++){
      const t = k / 90 * Math.PI * 2, rr = r * (1 + a1 * Math.sin(k1 * t + p1 + i * .35) + a2 * Math.sin(k2 * t + p2 - i * .2));
      pts.push((100 + rr * Math.cos(t)).toFixed(1) + ',' + (100 + rr * Math.sin(t) * .9).toFixed(1));
    }
    h += `<path class="dm-anneau" pathLength="1" d="M${pts.join('L')}Z" style="animation-delay:${(i * .12).toFixed(2)}s;stroke-opacity:${(.55 - i * .06).toFixed(2)}"/>`;
  }
  svg.innerHTML = h;
  dmEtape(12, 'Connexion…');
})();
// jamais bloque derriere l'ecran : 15 s au plus
setTimeout(dmFin, 15000);

async function initAuth(){
  const { data: { session: s } } = await sb.auth.getSession();
  dmMesure('session');
  if(!s || recuperationEnCours) dmFin();""", u'ecran js')

js = rempl(js, u"""  document.getElementById('whoami').textContent = session_.user.email;
  await loadOutline();
  chargerTotalCommunes();
  await loadMyCollection();
  await loadOthersPossessions();
  await loadPackStatus();""", u"""  document.getElementById('whoami').textContent = session_.user.email;
  dmEtape(25, 'La carte de France…');
  await loadOutline();
  dmMesure('carte');
  chargerTotalCommunes();
  dmEtape(45, 'Tes communes…');
  await loadMyCollection();
  dmMesure('mes communes');
  dmEtape(65, 'Les territoires des autres joueurs…');
  await loadOthersPossessions();
  dmMesure('les autres joueurs');
  dmEtape(88, 'Tes paquets…');
  await loadPackStatus();
  dmMesure('paquets');
  dmFin();""", u'etapes')

# ---------------------------------------------------------------- app.js : pagination en parallele
js = rempl(js, u"""async function toutesLesLignes(construireRequete){
  const TAILLE = 1000;
  let tout = [], debut = 0;
  for(;;){
    const { data, error } = await construireRequete().range(debut, debut + TAILLE - 1);
    if(error) return { data: null, error };
    tout = tout.concat(data || []);
    if(!data || data.length < TAILLE) return { data: tout, error: null };
    debut += TAILLE;
  }
}""", u"""async function toutesLesLignes(construireRequete, cle = 'commune_code'){
  // patch122 : 6 paquets de 1 000 a la fois au lieu d'un seul. Tries sur une
  // cle unique, pour qu'une ligne ne puisse pas sauter d'un paquet a l'autre.
  const TAILLE = 1000, EN_PARALLELE = 6;
  let tout = [], page = 0;
  for(;;){
    const lot = [];
    for(let k = 0; k < EN_PARALLELE; k++){
      const debut = (page + k) * TAILLE;
      lot.push(construireRequete().order(cle, { ascending: true }).range(debut, debut + TAILLE - 1));
    }
    const reponses = await Promise.all(lot);
    for(const { data, error } of reponses){
      if(error) return { data: null, error };
      tout = tout.concat(data || []);
      if(!data || data.length < TAILLE) return { data: tout, error: null };
    }
    page += EN_PARALLELE;
  }
}""", u'pagination')

ecrire('app.js', js)
ecrire('style.css', css)
ecrire('index.html', html)
print(u'patch122 applique')
