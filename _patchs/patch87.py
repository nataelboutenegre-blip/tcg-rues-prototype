# -*- coding: utf-8 -*-
u"""
patch87 — Ouvrir le paquet en le coupant d'un trait de lumiere
(apercu « Dechirure TerraFront » valide le 9 octobre).

- Toucher le paquet n'importe ou l'ouvre : la coupe file toute seule.
- Ou on coupe soi-meme en glissant le long des pointilles (en partant du
  haut du paquet) : une tete lumineuse suit le doigt et laisse un trait
  brillant ; a 40 % la coupe part toute seule jusqu'au bout. Lache avant :
  le trait se retracte.
- La lumiere prend la couleur de la meilleure carte des que le serveur a
  repondu (blanche, bleue avec une rare, doree avec une legendaire). Le
  tirage part au premier toucher : ca ne change rien aux chances.
- Fin : eclair horizontal, la bande saute d'un bloc et s'envole, lumiere et
  rayons, vibration (Android), puis la pile sort comme avant.
- Reglage Animation coupe (ou mouvements reduits) : toucher = ouverture
  courte comme avant.
- Un echec de paiement sur le paquet pose remet le paquet en place (on peut
  reessayer) ; avant, il restait inerte.
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

# --- le paquet : les elements de la coupe ---
js = rempl(js,
u'''  pack.setAttribute('aria-label', 'Déchirer le paquet');
  pack.innerHTML = `''',
u'''  pack.setAttribute('aria-label', 'Ouvrir le paquet');
  pack.innerHTML = `''', 'aria')
js = rempl(js,
u'''    <div class="paquet-bouts">${MORCEAUX_PAQUET}</div>`;
  return pack;''',
u'''    <div class="paquet-bouts">${MORCEAUX_PAQUET}</div>
    <div class="coupe-lueur"></div><div class="coupe-trace"></div><div class="coupe-tete"></div><div class="coupe-eclair"></div>
    <span class="coupe-consigne" aria-hidden="true">Touche le paquet · ou coupe les pointillés</span>`;
  return pack;''', 'makePackEl')

# --- les sons de la coupe ---
js = rempl(js,
u'''  let bruitBlanc = null;
  const bruit = (duree, f1, f2, vol, type) => {''',
u'''  let bruitBlanc = null;
  const assurerBruit = () => {
    if(!bruitBlanc){
      const n = ctx.sampleRate, d = (bruitBlanc = ctx.createBuffer(1, n, ctx.sampleRate)).getChannelData(0);
      for(let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1;
    }
  };
  const bruit = (duree, f1, f2, vol, type) => {''', 'assurerBruit')
js = rempl(js,
u'''    // patch86 : l'assaut
    assautChoc(){''',
u'''    // patch87 : la coupe
    grain(force){ if(pret()){ const f = 2200 + Math.random() * 2500; bruit(0.03 + Math.random() * 0.03, f, f * 1.3, 0.12 + 0.25 * force); } },
    zip(duree){ if(!pret()) return; assurerBruit();
      const t = ctx.currentTime, s = ctx.createBufferSource(), fl = ctx.createBiquadFilter(), g = ctx.createGain();
      s.buffer = bruitBlanc; fl.type = 'bandpass'; fl.Q.value = 2;
      fl.frequency.setValueAtTime(1800, t); fl.frequency.exponentialRampToValueAtTime(7000, t + duree);
      g.gain.setValueAtTime(0.05, t); g.gain.exponentialRampToValueAtTime(0.3, t + duree); g.gain.exponentialRampToValueAtTime(0.0001, t + duree + 0.05);
      s.connect(fl); fl.connect(g); g.connect(maitre); s.start(t, 0.2, duree + 0.1); },
    cede(lum){ if(!pret()) return;
      bruit(0.45, 900, 4200, 0.45);
      const o = ctx.createOscillator(), g = ctx.createGain(), t = ctx.currentTime;
      const f0 = lum === 'lum-leg' ? 392 : lum === 'lum-rare' ? 330 : 262;
      o.type = 'triangle'; o.frequency.setValueAtTime(f0, t + 0.15); o.frequency.exponentialRampToValueAtTime(f0 * 2, t + 0.7);
      g.gain.setValueAtTime(0.0001, t + 0.15); g.gain.exponentialRampToValueAtTime(lum ? 0.18 : 0.08, t + 0.3); g.gain.exponentialRampToValueAtTime(0.0001, t + 1.1);
      o.connect(g); g.connect(maitre); o.start(t + 0.15); o.stop(t + 1.2); },
    // patch86 : l'assaut
    assautChoc(){''', 'sons coupe')

# --- le geste et l'animation ---
js = rempl(js,
u'''// Les cinq tirages, l'un apres l'autre, avec la gestion d'erreur d'origine.''',
u'''// patch87 : ouvrir le paquet en le coupant d'un trait de lumiere.
// demarrer() est appele au premier toucher (ou au debut de la coupe) et
// renvoie les tirages, ou null si l'ouverture a echoue (le paquet revient).
const SEUIL_COUPE = 0.4;
function lumierePaquet(draws){
  const ids = draws.map(d => d.tier && d.tier.id);
  return ids.includes('legendaire') ? 'lum-leg' : ids.includes('rare') ? 'lum-rare' : '';
}
function armerPaquet(pack, demarrer){
  const zone = document.getElementById('packZone');
  const q = (c) => pack.querySelector(c);
  const languette = q('.paquet-languette'), trace = q('.coupe-trace'), tete = q('.coupe-tete'), lueur = q('.coupe-lueur');
  const anim = ouvAnim && !REDUCED_MOTION;
  let p = 0, fini = false, tirage = null, g = null, rayons = null, jeton = 0, dernierGrain = 0, derniereEtincelle = 0;

  const poser = (v) => {
    p = v;
    trace.style.transform = `scaleX(${v.toFixed(3)})`;
    lueur.style.transform = `scaleX(${Math.max(0, v - 0.02).toFixed(3)})`;
    lueur.style.opacity = Math.min(1, v * 3);
    tete.style.transform = `translateX(${(v * 200).toFixed(1)}px)`;
    tete.style.opacity = v > 0 && v < 1 ? 1 : 0;
    languette.style.transform = v > 0 ? `rotate(${(-v * 4).toFixed(2)}deg)` : '';
    if(rayons){ rayons.style.opacity = Math.min(0.5, v * 0.8); rayons.style.transform = `scale(${(0.3 + v * 0.5).toFixed(3)})`; }
  };
  // quelques etincelles qui partent de la tete (peu : c'est pour un telephone)
  const etincelle = (force) => {
    const now = performance.now();
    if(now - derniereEtincelle < 30) return;
    derniereEtincelle = now;
    for(let i = 0; i < 2; i++){
      const e = document.createElement('i'); e.className = 'coupe-etincelle';
      e.style.left = (p * 200 - 1) + 'px';
      pack.appendChild(e);
      const dx = -10 - Math.random() * 40 * (1 + force), dy = (Math.random() - 0.7) * 50;
      e.animate([{ transform: 'none', opacity: 1 }, { transform: `translate(${dx}px,${dy}px) scale(.3)`, opacity: 0 }],
        { duration: 380 + Math.random() * 250, easing: 'cubic-bezier(.2,.7,.4,1)' }).onfinish = () => e.remove();
    }
  };
  const animerVers = (cible, duree, accel) => new Promise(fin => {
    const mien = ++jeton, de = p, t0 = performance.now();
    const pas = (now) => {
      if(mien !== jeton) return fin();
      const x = Math.min(1, (now - t0) / duree), e = accel ? x * x : 1 - Math.pow(1 - x, 2);
      poser(de + (cible - de) * e);
      if(cible > de){ etincelle(accel ? 1 : 0.5); if(Math.random() < 0.5) sonsOuverture.grain(0.7); }
      x < 1 ? requestAnimationFrame(pas) : fin();
    };
    requestAnimationFrame(pas);
  });
  const engager = () => {
    if(tirage) return;
    pack.classList.add('coupe');
    if(anim){
      rayons = document.createElement('div'); rayons.className = 'coupe-rayons';
      pack.parentElement.insertBefore(rayons, pack);
    }
    tirage = Promise.resolve().then(demarrer).catch(e => { console.error(e); return null; });
    tirage.then(draws => {
      const c = draws && draws.length ? lumierePaquet(draws) : '';
      if(c){ pack.classList.add(c); if(rayons) rayons.classList.add(c); }
    });
  };
  const abandon = () => {
    fini = false; tirage = null; g = null; jeton++;
    pack.classList.remove('coupe', 'attente', 'lum-rare', 'lum-leg');
    if(rayons){ rayons.remove(); rayons = null; }
    poser(0);
  };
  const finir = async (duree) => {
    if(fini) return;
    fini = true; g = null;
    engager();
    if(!anim){
      // animation coupee : une ouverture courte, puis tout le paquet d'un coup
      const draws = await tirage;
      if(!draws) return abandon();
      if(!draws.length) return paquetSansCarte(zone);
      sonsOuverture.dechire();
      pack.classList.add('dechire');
      await attendreOuv(300);
      revealCards(draws);
      return;
    }
    sonsOuverture.grain(0.4);
    sonsOuverture.zip(duree / 1000);
    await animerVers(1, duree, true);
    // le serveur n'a pas encore repondu : la tete attend au bout en palpitant
    pack.classList.add('attente');
    const draws = await tirage;
    pack.classList.remove('attente');
    if(!draws) return abandon();
    if(!draws.length){ if(rayons) rayons.remove(); return paquetSansCarte(zone); }

    const tries = trierPourRevelation(draws);
    const scene = pack.closest('.ouv-scene');
    const pile = construirePileOuv(tries.slice().reverse());
    pile.classList.add('dedans');
    scene.querySelector('.ouv-echelle').appendChild(pile);
    const lum = lumierePaquet(draws);
    sonsOuverture.cede(lum);
    if(navigator.vibrate) try{ navigator.vibrate(lum === 'lum-leg' ? [30, 40, 60] : 35); }catch(e){}
    pack.classList.add('coupee');
    if(rayons){
      const r = rayons;
      r.animate([{ opacity: 0.5, transform: 'scale(.8)' },
                 { opacity: lum ? 0.85 : 0.45, transform: 'scale(1.25) rotate(20deg)' },
                 { opacity: 0, transform: 'scale(1.4) rotate(40deg)' }],
        { duration: lum === 'lum-leg' ? 2200 : 1500, easing: 'ease-in-out', fill: 'forwards' }).onfinish = () => r.remove();
    }
    await attendreOuv(560);
    // le paquet tombe, la pile sort par le haut
    pack.classList.add('sortie');
    pile.classList.remove('dedans');
    pile.classList.add('emerge');
    sonsOuverture.sortie();
    await attendreOuv(800);
    pack.remove();
    pile.classList.remove('emerge');
    lancerRevelation(zone, scene, tries);
  };

  pack.addEventListener('pointerdown', (e) => {
    if(fini || (e.pointerType === 'mouse' && e.button !== 0)) return;
    const r = pack.getBoundingClientRect();
    g = { id: e.pointerId, x0: e.clientX, r, haut: (e.clientY - r.top) / r.height < 90 / 280,
          glisse: false, last: e.clientX, tl: performance.now() };
    try{ pack.setPointerCapture(e.pointerId); }catch(err){}
  });
  pack.addEventListener('pointermove', (e) => {
    if(!g || g.id !== e.pointerId || fini || !anim || !g.haut) return;
    if(!g.glisse){
      if(Math.abs(e.clientX - g.x0) <= 12) return;
      g.glisse = true; engager();
    }
    jeton++;   // le doigt reprend la main sur une retraction en cours
    const v = Math.max(p, Math.min(1, (e.clientX - g.r.left) / g.r.width));
    const now = performance.now(), vit = Math.abs(e.clientX - g.last) / Math.max(1, now - g.tl);
    if(v > p){
      if(now - dernierGrain > Math.max(18, 70 - vit * 60)){ sonsOuverture.grain(Math.min(1, vit)); dernierGrain = now; }
      etincelle(Math.min(1, vit));
    }
    g.last = e.clientX; g.tl = now;
    poser(v);
    if(v >= SEUIL_COUPE) finir(Math.round(300 * (1 - v) + 60));   // seuil passe : la coupe part toute seule
  });
  const lacher = (annule) => (e) => {
    if(!g || g.id !== e.pointerId) return;
    const glisse = g.glisse; g = null;
    if(fini) return;
    if(glisse) animerVers(0, 260);       // avant le seuil : le trait se retracte
    else if(!annule) finir(520);         // un toucher, n'importe ou : ouverture automatique
  };
  pack.addEventListener('pointerup', lacher(false));
  pack.addEventListener('pointercancel', lacher(true));   // le navigateur a pris la main (defilement)
  // clavier (Entree, Espace) : le bouton recoit un clic sans pointeur
  pack.addEventListener('click', (e) => { if(e.detail === 0 && !fini) finir(520); });
}

// Les cinq tirages, l'un apres l'autre, avec la gestion d'erreur d'origine.''', 'armerPaquet')

js = rempl(js,
u'''  sceneOuverture(zone).echelle.appendChild(pack);
  pack.addEventListener('click', () => dechirerPaquet(pack, nbCartes), { once: true });
}''',
u'''  sceneOuverture(zone).echelle.appendChild(pack);
  armerPaquet(pack, () => tirerCartesDuPaquet(nbCartes));   // patch87
}''', 'afficherPaquetATirer')

js = rempl(js,
u'''  sceneOuverture(zone).echelle.appendChild(pack);
  pack.addEventListener('click', async () => {
    if(paquetEnCours) return;
    paquetEnCours = true;
    renderPackStatus();
    const err = await payerPaquet(type);
    if(err){
      paquetEnCours = false;
      notifier({ type: 'erreur', titre: 'Impossible d\\'ouvrir le paquet', texte: messageLisible(err.message) });
      loadPackStatus();
      return;
    }
    delete pack.dataset.pret;
    loadPackStatus();
    dechirerPaquet(pack, 5);
  }, { once: true });
}''',
u'''  sceneOuverture(zone).echelle.appendChild(pack);
  // patch87 : le premier toucher (ou le debut de la coupe) paie, puis tire
  armerPaquet(pack, async () => {
    if(paquetEnCours) return null;
    paquetEnCours = true;
    renderPackStatus();
    const err = await payerPaquet(type);
    if(err){
      paquetEnCours = false;
      notifier({ type: 'erreur', titre: 'Impossible d\\'ouvrir le paquet', texte: messageLisible(err.message) });
      loadPackStatus();
      return null;
    }
    delete pack.dataset.pret;
    loadPackStatus();
    return tirerCartesDuPaquet(5);
  });
}''', 'afficherPaquetPret')
ecrire('app.js', js)

css = lire('style.css')
css += u'''

/* =====================================================================
   patch87 — La coupe au trait de lumiere (apercu valide le 9 octobre)
   ===================================================================== */
.paquet, .coupe-rayons{ --lum: rgba(255,244,214,.95); }
.paquet.lum-rare, .coupe-rayons.lum-rare{ --lum: rgba(90,160,255,.95); }
.paquet.lum-leg, .coupe-rayons.lum-leg{ --lum: rgba(255,200,60,.98); }
.paquet{ touch-action: pan-y; -webkit-user-select:none; user-select:none; -webkit-tap-highlight-color: transparent; }
.pack-zone{ overflow-x: clip; }   /* l'eclair et la bande qui s'envole ne font pas defiler la page */
.paquet .coupe-lueur{ position:absolute; left:0; top: calc(var(--h-languette) - 14px); width:200px; height:30px; z-index:3;
  pointer-events:none; border-radius:50%; transform-origin: 0 50%; transform: scaleX(0); opacity:0; will-change: transform, opacity;
  background: radial-gradient(ellipse at 50% 55%, #fff 0%, var(--lum) 30%, transparent 70%); }
.paquet .coupe-trace{ position:absolute; left:0; top: calc(var(--h-languette) - 1px); width:200px; height:2px; z-index:5;
  pointer-events:none; border-radius:2px; transform-origin: 0 50%; transform: scaleX(0); will-change: transform;
  background: linear-gradient(90deg, var(--lum), #fff 70%); box-shadow: 0 0 6px 2px var(--lum), 0 0 16px 4px var(--lum); }
.paquet .coupe-tete{ position:absolute; left:0; top: var(--h-languette); width:0; height:0; z-index:6; pointer-events:none; opacity:0;
  will-change: transform, opacity; }
.paquet .coupe-tete::before{ content:''; position:absolute; left:-22px; top:-22px; width:44px; height:44px; border-radius:50%;
  background: radial-gradient(circle, #fff 0 14%, var(--lum) 34%, transparent 68%); }
.paquet .coupe-tete::after{ content:''; position:absolute; left:-60px; top:-5px; width:84px; height:10px; border-radius:50%;
  background: radial-gradient(ellipse at 72% 50%, #fff 0 18%, var(--lum) 45%, transparent 72%); }
.paquet .coupe-etincelle{ position:absolute; top: calc(var(--h-languette) - 1px); width:3px; height:3px; border-radius:50%; z-index:6;
  background:#fff; box-shadow: 0 0 6px 2px var(--lum); pointer-events:none; }
.paquet .coupe-eclair{ position:absolute; left:-20px; top: calc(var(--h-languette) - 6px); width:240px; height:12px; z-index:7;
  pointer-events:none; opacity:0; border-radius:50%; background: radial-gradient(ellipse, #fff 0 30%, var(--lum) 55%, transparent 75%); }
.paquet .coupe-consigne{ position:absolute; left:-40px; right:-40px; top: calc(100% + 10px); text-align:center; font-size:.8rem;
  color: var(--brume); pointer-events:none; transition: opacity .2s; }
.ouv-echelle .coupe-rayons{ position:absolute; left:50%; top:36px; width:460px; height:460px; margin:-230px 0 0 -230px; border-radius:50%;
  z-index:0; pointer-events:none; opacity:0; transform: scale(.3); will-change: transform, opacity;
  background: repeating-conic-gradient(from 0deg, var(--lum) 0deg 6deg, transparent 6deg 22deg);
  -webkit-mask: radial-gradient(circle, #000 0 18%, transparent 62%); mask: radial-gradient(circle, #000 0 18%, transparent 62%); }

/* pendant la coupe : plus de survol ni de transition, la bande suit le doigt */
.paquet.coupe{ transform:none; transition:none; }
.paquet.coupe .paquet-languette{ transition:none; transform-origin: 100% 100%; }
.paquet.coupe .perfo-masque{ display:none; }
.paquet.coupe .coupe-consigne{ opacity:0; }
.paquet.attente .coupe-tete{ animation: coupeAttente .45s ease-in-out infinite alternate; }
@keyframes coupeAttente{ from{ opacity:.55; } to{ opacity:1; } }

/* la fin : eclair, la bande saute d'un bloc et s'envole, la lumiere jaillit */
.paquet.coupee{ pointer-events:none; }
.paquet.coupee .paquet-perfo{ opacity:0; transition: opacity .15s; }
.paquet.coupee .coupe-tete{ opacity:0 !important; }
.paquet.coupee .coupe-trace{ animation: coupeFondu .3s ease-out forwards; }
.paquet.coupee .coupe-eclair{ animation: coupeEclair .52s ease-out forwards; }
.paquet.coupee .paquet-languette{ animation: coupeEnvol .82s cubic-bezier(.25,.6,.5,1) forwards; }
.paquet.coupee .coupe-lueur{ animation: coupeJaillit .95s ease-out forwards; }
@keyframes coupeFondu{ to{ opacity:0; } }
@keyframes coupeEclair{ 0%{ opacity:0; transform: scale(.6,.5); } 20%{ opacity:1; transform: scale(1.6,1.4); } 100%{ opacity:0; transform: scale(2.6,.4); } }
@keyframes coupeEnvol{ 0%{ transform: rotate(-4deg); opacity:1; } 22%{ transform: translate(4px,-26px) rotate(-10deg); opacity:1; }
  100%{ transform: translate(150px,-250px) rotate(32deg); opacity:0; } }
@keyframes coupeJaillit{ 0%{ opacity:1; transform: scale(1,1); } 30%{ opacity:1; transform: scale(1,3.4); } 100%{ opacity:0; transform: scale(1,1.6); } }
.paquet.sortie .coupe-lueur, .paquet.sortie .coupe-consigne{ opacity:0; }
'''
ecrire('style.css', css)
print(u'patch87 : OK')
