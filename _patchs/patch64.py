# -*- coding: utf-8 -*-
u"""
patch64 — La nouvelle ouverture de paquet, et le compteur de communes libres.

POURQUOI
  Ouvrir un paquet, c'est ce que les joueurs font le plus souvent. Jusqu'ici :
  le paquet se dechirait, puis cinq dos de cartes s'alignaient et le joueur
  les retournait dans le desordre. Aucune attente, aucune montee.
  La demo validee par Natael le 4 octobre (artifact « Ouverture de paquet
  TerraFront », version 3) est reprise ici telle quelle, sur les vraies
  cartes du jeu.

CE QUE LE JOUEUR VOIT
  1. Le paquet est au centre. Au survol de la souris, un trait dore suit
     les dents de la perforation tant qu'on reste dessus.
  2. Au clic : le paquet tremble de plus en plus, le trait brille ; puis le
     coin droit se souleve d'abord, le gauche tient, et la bande s'envole.
     Le paquet tombe, la pile de cartes sort par le haut.
  3. Chaque clic sur la pile retourne la carte suivante, DE LA MOINS RARE A
     LA PLUS RARE. A la premiere, la pile glisse a gauche pour laisser la
     place a la carte retournee, a droite. Sous la carte : ses habitants
     (gentile) ou un fait, quand la base les connait.
  4. Avant une derniere carte rare ou legendaire, son dos s'illumine.
  5. Les cartes retournees s'alignent en dessous, comme avant.
  Reglages, memorises dans le navigateur : « Son » et « Animation ».
  Animation coupee = tout le paquet d'un coup. « Tout reveler » en cours de
  route. Les reglages « reduire les animations » du systeme sont respectes.

  Au-dessus des boutons : « N communes libres », avec une jauge vers le
  seuil de fin de saison. Les chiffres viennent de saison_courante(), que le
  jeu appelle deja au demarrage : aucun appel en plus. Le nombre baisse
  localement a chaque paquet, sans requete.

CE QUI NE CHANGE PAS
  - Le tirage cote serveur : ouvrir_paquet puis tirer_carte, cinq fois,
    exactement comme avant, avec la meme gestion d'erreur (paquet court,
    tirage vide). Seul l'ORDRE D'AFFICHAGE change : les cartes sont deja
    tirees quand la pile apparait.
  - La carte elle-meme (makeCardEl), la collection, les objectifs, le
    bouton « paquet suivant ».
  - Paquets gratuits et achetes : meme animation, pas davantage pour un
    paquet paye (regulation des loot boxes, voir la page SAISON 2).

SONS
  Generes par Web Audio : aucun fichier, aucune licence. Ils ne partent
  qu'apres un clic (regle des navigateurs).
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


# =========================================================================
#  index.html : compteur de communes libres, reglages
# =========================================================================
html = lire('index.html')

html = rempl(html,
u"""      <div class="puces" id="packStatus"><span class="puce">Chargement…</span></div>
      <div class="pack-buttons">
        <button class="open-btn" id="openFreeBtn">Ouvrir un paquet gratuit</button>
        <button class="open-btn secondary" id="openBuyBtn">Acheter un paquet (200 pts)</button>
      </div>""",
u"""      <div class="puces" id="packStatus"><span class="puce">Chargement…</span></div>
      <div class="pot-libres" id="potLibres" hidden>
        <div class="pot-ligne">
          <span class="pot-nombre"><b id="potNombre">—</b> communes libres</span>
          <span class="pot-seuil" id="potSeuil"></span>
        </div>
        <div class="pot-jauge" role="progressbar" aria-label="Avancée de la saison" aria-valuemin="0" aria-valuemax="100" id="potJauge"><i id="potBarre"></i></div>
      </div>
      <div class="pack-buttons">
        <button class="open-btn" id="openFreeBtn">Ouvrir un paquet gratuit</button>
        <button class="open-btn secondary" id="openBuyBtn">Acheter un paquet (200 pts)</button>
        <div class="ouv-reglages" aria-label="Réglages de l'ouverture">
          <button type="button" class="ouv-bascule" id="ouvSon" aria-pressed="true">Son</button>
          <button type="button" class="ouv-bascule" id="ouvAnim" aria-pressed="true">Animation</button>
        </div>
      </div>""",
u'compteur et reglages dans le Tirage')

ecrire('index.html', html)


# =========================================================================
#  app.js
# =========================================================================
js = lire('app.js')

# --- le paquet : la perforation devient une ligne de dents fines, avec le trait dore
js = rempl(js,
u"""    <div class="paquet-languette">${motif}<div class="paquet-pointilles"></div></div>""",
u"""    <div class="paquet-languette">${motif}</div>
    <svg class="paquet-perfo" viewBox="0 0 100 10" preserveAspectRatio="none" aria-hidden="true"><polyline class="perfo-base" points="${PERFO_POINTS}"/></svg>
    <div class="perfo-masque"><svg class="paquet-perfo perfo-lueur" viewBox="0 0 100 10" preserveAspectRatio="none" aria-hidden="true"><polyline class="perfo-trace" points="${PERFO_POINTS}"/></svg></div>""",
u'perforation en dents fines')

js = rempl(js,
u"""// Morceaux de papier projetes a la dechirure : positions figees, calculees une fois""",
u"""// La perforation : 36 dents fines, de gauche a droite. Le trait dore du
// survol et de la dechirure suit exactement ces points.
const PERFO_POINTS = Array.from({ length: 73 }, (_, i) =>
  (i * 100 / 72).toFixed(3) + ',' + (i % 2 ? 2 : 8)).join(' ');

// Morceaux de papier projetes a la dechirure : positions figees, calculees une fois""",
u'points de la perforation')

# --- le paquet pose dans la scene, au centre
js = rempl(js,
u"""function afficherPaquetATirer(type, nbCartes){
  const zone = document.getElementById('packZone');
  zone.innerHTML = '';
  const pack = makePackEl(type);
  zone.appendChild(pack);
  pack.addEventListener('click', () => dechirerPaquet(pack, nbCartes), { once: true });
}""",
u"""function afficherPaquetATirer(type, nbCartes){
  const zone = document.getElementById('packZone');
  zone.innerHTML = '';
  const pack = makePackEl(type);
  sceneOuverture(zone).echelle.appendChild(pack);
  pack.addEventListener('click', () => dechirerPaquet(pack, nbCartes), { once: true });
}""",
u'paquet a tirer dans la scene')

js = rempl(js,
u"""  zone.innerHTML = '';
  const pack = makePackEl(type);
  pack.dataset.pret = '1';
  pack.setAttribute('aria-label', 'Ouvrir un paquet gratuit');
  zone.appendChild(pack);""",
u"""  zone.innerHTML = '';
  const pack = makePackEl(type);
  pack.dataset.pret = '1';
  pack.setAttribute('aria-label', 'Ouvrir un paquet gratuit');
  sceneOuverture(zone).echelle.appendChild(pack);""",
u'paquet pret dans la scene')

# --- la dechirure : on tire pendant la charge, puis la pile sort du paquet
ANCIEN_DECHIRER = u"""// Le paquet se tend, puis se dechire. Le tirage part pendant l'animation,
// pour ne pas laisser le joueur attendre une fois le paquet disparu.
async function dechirerPaquet(pack, nbCartes){
  const zone = document.getElementById('packZone');
  pack.classList.add('tension');
  if(!REDUCED_MOTION) await new Promise(r => setTimeout(r, 200));
  pack.classList.add('dechire');
  const animation = new Promise(resolve => setTimeout(resolve, REDUCED_MOTION ? 0 : 660));
  const draws = [];
  for(let i = 0; i < nbCartes; i++){"""
NOUVEAU_DECHIRER = u"""// Le paquet se charge, puis se dechire. Le tirage part des le clic, pendant
// la charge : quand la bande s'arrache, les cartes sont deja la.
async function dechirerPaquet(pack, nbCartes){
  const zone = document.getElementById('packZone');
  const tirage = tirerCartesDuPaquet(nbCartes);

  if(!ouvAnim){
    // animation coupee : une dechirure courte, puis tout le paquet d'un coup
    sonsOuverture.dechire();
    pack.classList.add('dechire');
    const [draws] = await Promise.all([tirage, attendreOuv(300)]);
    if(draws.length === 0) return paquetSansCarte(zone);
    revealCards(draws);
    return;
  }

  // 1. la tension monte, la perforation s'allume
  sonsOuverture.charge();
  pack.classList.add('charge');
  const [draws] = await Promise.all([tirage, attendreOuv(650)]);
  if(draws.length === 0) return paquetSansCarte(zone);

  // 2. la bande s'arrache par la droite ; les cartes attendent dans le paquet
  const tries = trierPourRevelation(draws);
  const scene = pack.closest('.ouv-scene');
  const pile = construirePileOuv(tries.slice().reverse());
  pile.classList.add('dedans');
  scene.querySelector('.ouv-echelle').appendChild(pile);
  pack.classList.remove('charge');
  pack.classList.add('dechire');
  sonsOuverture.dechire();
  await attendreOuv(500);

  // 3. le paquet tombe, la pile sort par le haut
  pack.classList.add('sortie');
  pile.classList.remove('dedans');
  pile.classList.add('emerge');
  sonsOuverture.sortie();
  await attendreOuv(800);
  pack.remove();
  pile.classList.remove('emerge');
  lancerRevelation(zone, scene, tries);
}

// Les cinq tirages, l'un apres l'autre, avec la gestion d'erreur d'origine.
async function tirerCartesDuPaquet(nbCartes){
  const draws = [];
  for(let i = 0; i < nbCartes; i++){"""
js = rempl(js, ANCIEN_DECHIRER, NOUVEAU_DECHIRER, u'dechirerPaquet')

js = rempl(js,
u"""      lat: row.latitude, lon: row.longitude, tier, rank: row.rang, tierSize: row.palier_total
    });
  }
  await animation;
  if(draws.length === 0){
    if(zone) zone.innerHTML = '';
    paquetEnCours = false;
    loadPackStatus();
    return;
  }
  revealCards(draws);
}""",
u"""      lat: row.latitude, lon: row.longitude, tier, rank: row.rang, tierSize: row.palier_total
    });
  }
  return draws;
}

function paquetSansCarte(zone){
  if(zone) zone.innerHTML = '';
  paquetEnCours = false;
  loadPackStatus();
}""",
u'fin du tirage')

# --- la revelation : remplace l'ancienne grille de dos a retourner
ANCIEN_REVEAL = u"""function revealCards(draws){
  const zone = document.getElementById('packZone');
  zone.innerHTML = '';
  pendingFlips = draws.length;
  draws.forEach((draw, index) => {
    const carte = makeCardEl(draw, () => {
      collectionMap.set(draw.code, draw);
      session[draw.tier.id]++;
      session.total++;
      renderStats();
      renderCollection();
      renderMapOverlay();
      pendingFlips--;
      if(pendingFlips <= 0){
        paquetEnCours = false;
        loadObjectifs();
        // les cartes restent affichees : c'est le joueur qui decide de passer au suivant
        loadPackStatus().then(proposerPaquetSuivant);
      }
    });
    // les cartes arrivent l'une apres l'autre
    carte.classList.add('entree');
    carte.style.animationDelay = (index * 90) + 'ms';
    zone.appendChild(carte);
  });
}"""
NOUVEAU_REVEAL = u"""// Ce qui se passe quand une carte est retournee : inchange depuis l'ancienne grille.
function surCarteRetournee(draw){
  return () => {
    collectionMap.set(draw.code, draw);
    session[draw.tier.id]++;
    session.total++;
    renderStats();
    renderCollection();
    renderMapOverlay();
    pendingFlips--;
    if(pendingFlips <= 0){
      paquetEnCours = false;
      loadObjectifs();
      // les cartes restent affichees : c'est le joueur qui decide de passer au suivant
      loadPackStatus().then(proposerPaquetSuivant);
    }
  };
}

// Animation coupee : tout le paquet d'un coup, deja retourne.
function revealCards(draws){
  const zone = document.getElementById('packZone');
  const tries = trierPourRevelation(draws);
  zone.innerHTML = '';
  pendingFlips = tries.length;
  potRetirer(tries.length);
  const rangee = document.createElement('div');
  rangee.className = 'ouv-rangee';
  zone.appendChild(rangee);
  tries.forEach(draw => {
    const carte = makeCardEl(draw, surCarteRetournee(draw));
    rangee.appendChild(carte);
    carte.click();
  });
  sonsOuverture.revele(tries[tries.length - 1].tier.id);
  annoncerOuv('Paquet ouvert : ' + tries.map(d => d.nom + ', ' + d.tier.label).join(' ; '));
}

// ---------- Ouverture de paquet : scene, pile, revelation triee, sons ----------
const RANG_TIER = { commun: 0, peucommun: 1, rare: 2, legendaire: 3 };
// la meilleure carte arrive en dernier
const trierPourRevelation = (draws) =>
  draws.slice().sort((a, b) => RANG_TIER[a.tier.id] - RANG_TIER[b.tier.id]);
const attendreOuv = (ms) => new Promise(r => setTimeout(r, REDUCED_MOTION ? 0 : ms));

function prefOuv(cle, defaut){
  try { const v = localStorage.getItem(cle); return v === null ? defaut : v === '1'; }
  catch(e){ return defaut; }
}
function ecrirePrefOuv(cle, v){ try { localStorage.setItem(cle, v ? '1' : '0'); } catch(e){} }
let ouvSon = prefOuv('tf-son', true);
let ouvAnim = prefOuv('tf-anim', true) && !REDUCED_MOTION;

function majReglagesOuv(){
  const s = document.getElementById('ouvSon'), a = document.getElementById('ouvAnim');
  if(s) s.setAttribute('aria-pressed', String(ouvSon));
  if(a) a.setAttribute('aria-pressed', String(ouvAnim));
}
(function brancherReglagesOuv(){
  const s = document.getElementById('ouvSon'), a = document.getElementById('ouvAnim');
  if(s) s.addEventListener('click', () => {
    ouvSon = !ouvSon; ecrirePrefOuv('tf-son', ouvSon); majReglagesOuv();
    if(ouvSon) sonsOuverture.tick();
  });
  if(a) a.addEventListener('click', () => {
    ouvAnim = !ouvAnim; ecrirePrefOuv('tf-anim', ouvAnim); majReglagesOuv();
  });
  majReglagesOuv();
})();

// Sons generes dans le navigateur : aucun fichier, discrets.
const sonsOuverture = (() => {
  let ctx = null, maitre = null;
  const pret = () => {
    if(!ouvSon) return false;
    if(!ctx){
      const C = window.AudioContext || window.webkitAudioContext;
      if(!C) return false;
      ctx = new C(); maitre = ctx.createGain(); maitre.gain.value = 0.32; maitre.connect(ctx.destination);
    }
    if(ctx.state === 'suspended') ctx.resume();
    return true;
  };
  const note = (f, debut, duree, type, vol) => {
    const o = ctx.createOscillator(), g = ctx.createGain(), t = ctx.currentTime + debut;
    o.type = type; o.frequency.setValueAtTime(f, t);
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(vol, t + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, t + duree);
    o.connect(g); g.connect(maitre); o.start(t); o.stop(t + duree + 0.05);
  };
  const bruit = (duree, f1, f2, vol, type) => {
    const n = Math.floor(ctx.sampleRate * duree), b = ctx.createBuffer(1, n, ctx.sampleRate), d = b.getChannelData(0);
    for(let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1;
    const s = ctx.createBufferSource(), fl = ctx.createBiquadFilter(), g = ctx.createGain(), t = ctx.currentTime;
    s.buffer = b; fl.type = type || 'bandpass'; fl.Q.value = 0.8;
    fl.frequency.setValueAtTime(f1, t); fl.frequency.exponentialRampToValueAtTime(f2, t + duree);
    g.gain.setValueAtTime(vol, t); g.gain.exponentialRampToValueAtTime(0.0001, t + duree);
    s.connect(fl); fl.connect(g); g.connect(maitre); s.start(t);
  };
  return {
    charge(){ if(!pret()) return;
      const o = ctx.createOscillator(), g = ctx.createGain(), f = ctx.createBiquadFilter(), t = ctx.currentTime;
      o.type = 'sawtooth'; o.frequency.setValueAtTime(70, t); o.frequency.exponentialRampToValueAtTime(150, t + 0.62);
      f.type = 'lowpass'; f.frequency.value = 500;
      g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.12, t + 0.55); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.66);
      o.connect(f); f.connect(g); g.connect(maitre); o.start(t); o.stop(t + 0.7); },
    dechire(){ if(!pret()) return;
      bruit(0.62, 900, 3800, 0.45);
      [0.05, 0.16, 0.27, 0.36, 0.44].forEach(d => setTimeout(() => { if(pret()) bruit(0.035, 3500, 6000, 0.3, 'highpass'); }, d * 1000)); },
    sortie(){ if(pret()) bruit(0.45, 250, 1600, 0.3, 'lowpass'); },
    retourne(){ if(pret()) bruit(0.07, 2500, 5200, 0.35, 'highpass'); },
    tick(){ if(pret()) note(880, 0, 0.09, 'sine', 0.25); },
    tension(tier){ if(!pret()) return;
      const o = ctx.createOscillator(), g = ctx.createGain(), t = ctx.currentTime, k = tier === 'legendaire' ? 1 : 0.8;
      o.type = 'sine'; o.frequency.setValueAtTime(180 * k, t); o.frequency.exponentialRampToValueAtTime(360 * k, t + 0.9);
      g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.18, t + 0.5); g.gain.exponentialRampToValueAtTime(0.0001, t + 1.0);
      o.connect(g); g.connect(maitre); o.start(t); o.stop(t + 1.05); },
    revele(tier){ if(!pret()) return;
      if(tier === 'commun') note(660, 0, 0.12, 'sine', 0.3);
      else if(tier === 'peucommun'){ note(660, 0, 0.12, 'sine', 0.32); note(880, 0.08, 0.16, 'sine', 0.32); }
      else if(tier === 'rare') [523, 659, 784, 1047].forEach((f, i) => note(f, i * 0.07, 0.35, 'triangle', 0.35));
      else {
        [523, 659, 784].forEach(f => note(f, 0, 1.4, 'triangle', 0.28));
        note(1047, 0.12, 1.5, 'triangle', 0.3);
        [1568, 2093, 2637, 3136].forEach((f, i) => note(f, 0.2 + i * 0.09, 0.5, 'sine', 0.12));
      } }
  };
})();

function annoncerOuv(texte){
  const el = document.getElementById('ouvAnnonce');
  if(el) el.textContent = texte;
}

// La scene : la pile a gauche, la carte retournee a droite, la rangee dessous.
function sceneOuverture(zone){
  zone.innerHTML = `
    <div class="ouv-scene">
      <div class="ouv-slot-pile"><div class="ouv-echelle"></div></div>
      <div class="ouv-slot-carte"></div>
    </div>
    <p class="ouv-decouverte" aria-live="polite"></p>
    <div class="ouv-actions" hidden>
      <span class="ouv-consigne"></span>
      <button type="button" class="ouv-tout">Tout révéler</button>
    </div>
    <div class="ouv-rangee"></div>
    <p class="ouv-lecteur" id="ouvAnnonce" aria-live="polite"></p>`;
  return { scene: zone.querySelector('.ouv-scene'), echelle: zone.querySelector('.ouv-echelle') };
}

// La pile : la fin du tableau est la carte du dessus.
function construirePileOuv(pileDraws){
  const pile = document.createElement('button');
  pile.type = 'button';
  pile.className = 'ouv-pile';
  pile.setAttribute('aria-label', 'Retourner la carte suivante');
  pileDraws.forEach((d, i) => {
    const dos = makeCardEl(d, () => {});
    dos.classList.add('ouv-dos');
    const prof = pileDraws.length - 1 - i;
    dos.style.transform = `translate(${prof * 3}px, ${prof * -3}px) rotate(${(prof % 2 ? 1 : -1) * prof * 0.8}deg)`;
    pile.appendChild(dos);
  });
  const compte = document.createElement('span');
  compte.className = 'ouv-compte';
  compte.textContent = pileDraws.length > 1 ? `${pileDraws.length} cartes` : 'Dernière carte';
  pile.appendChild(compte);
  return pile;
}

function lancerRevelation(zone, scene, tries){
  const echelle = scene.querySelector('.ouv-echelle');
  const slotCarte = scene.querySelector('.ouv-slot-carte');
  const rangee = zone.querySelector('.ouv-rangee');
  const decouverte = zone.querySelector('.ouv-decouverte');
  const actions = zone.querySelector('.ouv-actions');
  const consigne = zone.querySelector('.ouv-consigne');
  const btnTout = zone.querySelector('.ouv-tout');
  const pile = tries.slice().reverse();          // la moins rare sur le dessus
  let enCours = null, verrou = false, fini = false;

  pendingFlips = tries.length;
  potRetirer(tries.length);
  // le gentile et les faits arrivent pendant qu'on retourne : rien n'attend
  tries.forEach(d => { detailsCommune(d.code).catch(() => {}); });

  const decouvrir = (draw) => {
    decouverte.textContent = '';
    detailsCommune(draw.code).then(d => {
      if(!enCours || enCours.draw !== draw) return;
      const gentile = d && d.gentile ? String(d.gentile).trim() : '';
      const fait = d ? (faitsTries(d.faits)[0] || {}).t : '';
      decouverte.textContent = gentile ? `${draw.nom} : ses habitants sont les ${gentile}.` : (fait || '');
    }).catch(() => {});
  };
  const versRangee = (el) => { el.classList.remove('ouv-scene-carte'); rangee.appendChild(el); };
  const redessinerPile = () => {
    const ancienne = echelle.querySelector('.ouv-pile');
    if(ancienne) ancienne.remove();
    if(!pile.length) return;
    const p = construirePileOuv(pile);
    const prochaine = pile[pile.length - 1];
    if(pile.length === 1 && RANG_TIER[prochaine.tier.id] >= 2){
      [...p.querySelectorAll('.ouv-dos')].pop().classList.add(prochaine.tier.id === 'legendaire' ? 'lueur-leg' : 'lueur-rare');
      setTimeout(() => sonsOuverture.tension(prochaine.tier.id), 450);
    }
    p.addEventListener('click', suivante);
    echelle.appendChild(p);
  };
  const terminer = async () => {
    if(fini) return;
    fini = true;
    actions.hidden = true;
    await attendreOuv(250);
    scene.remove();
    decouverte.remove();
    actions.remove();
  };

  async function suivante(){
    if(verrou || !pile.length) return;
    verrou = true;
    if(!scene.classList.contains('etalee')){
      // premiere carte : la pile glisse a gauche pour faire de la place
      scene.classList.add('etalee');
      await attendreOuv(480);
    }
    if(enCours){ versRangee(enCours.el); enCours = null; }
    const draw = pile.pop();
    const el = makeCardEl(draw, surCarteRetournee(draw));
    el.classList.add('ouv-scene-carte');
    slotCarte.appendChild(el);
    enCours = { draw, el };
    redessinerPile();
    sonsOuverture.retourne();
    requestAnimationFrame(() => requestAnimationFrame(async () => {
      el.click();                                  // retourne la carte et l'ajoute a la collection
      decouvrir(draw);
      await attendreOuv(420);
      sonsOuverture.revele(draw.tier.id);
      if(RANG_TIER[draw.tier.id] >= 2) el.classList.add('ouv-eclat');
      annoncerOuv(draw.nom + ', ' + draw.tier.label);
      verrou = false;
      if(!pile.length){
        consigne.textContent = '';
        btnTout.hidden = true;
        scene.classList.add('seule');            // la derniere carte se recentre
        await attendreOuv(draw.tier.id === 'legendaire' ? 1800 : 1100);
        if(enCours){ versRangee(enCours.el); enCours = null; }
        terminer();
      }
    }));
  }

  btnTout.addEventListener('click', async () => {
    if(btnTout.hidden || !pile.length) return;
    btnTout.hidden = true;
    // une carte est peut-etre en train de se retourner : on attend qu'elle ait fini
    while(verrou) await new Promise(r => setTimeout(r, 40));
    if(!pile.length) return;
    verrou = true;
    btnTout.hidden = true;
    if(enCours){ versRangee(enCours.el); enCours = null; }
    const reste = pile.splice(0).reverse();
    redessinerPile();
    reste.forEach((draw, i) => setTimeout(() => {
      const el = makeCardEl(draw, surCarteRetournee(draw));
      rangee.appendChild(el);
      el.click();
      if(i === reste.length - 1){ sonsOuverture.revele(draw.tier.id); terminer(); }
      else sonsOuverture.retourne();
    }, i * 110));
  });
  scene.addEventListener('keydown', (e) => {
    if((e.key === ' ' || e.key === 'Enter') && e.target === scene){ e.preventDefault(); suivante(); }
  });

  redessinerPile();
  consigne.textContent = 'Touche la pile pour retourner la carte suivante';
  actions.hidden = false;
  const p = echelle.querySelector('.ouv-pile');
  if(p) p.focus({ preventScroll: true });
}

// ---------- Communes libres : le compte a rebours de la saison ----------
let potLibres = null;   // copie locale : on la fait baisser a chaque paquet sans requete
function renderPot(){
  const bloc = document.getElementById('potLibres');
  if(!bloc) return;
  const s = (typeof saisonEtat !== 'undefined') ? saisonEtat : null;
  if(!s || s.libres == null || !s.total){ bloc.hidden = true; return; }
  if(potLibres === null) potLibres = Number(s.libres);
  const total = Number(s.total), seuil = Number(s.seuil) || 0;
  const libres = Math.max(0, potLibres);
  document.getElementById('potNombre').textContent = libres.toLocaleString('fr-FR');
  document.getElementById('potSeuil').textContent = seuil > 0
    ? `La fin de saison s'enclenche à ${seuil.toLocaleString('fr-FR')}` : '';
  const pct = total > seuil ? Math.max(0, Math.min(100, (total - libres) / (total - seuil) * 100)) : 100;
  document.getElementById('potBarre').style.width = pct.toFixed(1) + '%';
  document.getElementById('potJauge').setAttribute('aria-valuenow', String(Math.round(pct)));
  bloc.hidden = false;
}
function potRetirer(n){
  if(potLibres === null) return;
  potLibres -= n;
  renderPot();
}"""
js = rempl(js, ANCIEN_REVEAL, NOUVEAU_REVEAL, u'revealCards')

# --- le compteur se met a jour quand la saison est lue
js = rempl(js,
u"""    saisonEtat = (data && data[0]) || null;
  }
  renderSaison();""",
u"""    saisonEtat = (data && data[0]) || null;
  }
  potLibres = null;       // repart des chiffres du serveur
  renderPot();
  renderSaison();""",
u'compteur a la lecture de la saison')

ecrire('app.js', js)


# =========================================================================
#  style.css : ajoute a la fin, pour passer devant les anciennes regles
# =========================================================================
css = lire('style.css')
assert u'.ouv-scene' not in css, u'patch64 deja applique'
css += u"""

/* =====================================================================
   patch64 — La nouvelle ouverture de paquet (demo validee le 4 octobre)
   ===================================================================== */

/* compteur de communes libres */
.pot-libres{ background: var(--nuit-2); border:1px solid rgba(169,188,212,0.16); border-radius:14px;
  padding:12px 16px; margin: 0 0 16px; display:flex; flex-direction:column; gap:8px; }
.pot-ligne{ display:flex; flex-wrap:wrap; align-items:baseline; justify-content:space-between; gap:4px 16px; }
.pot-nombre{ color: var(--brume); font-size:.9rem; }
.pot-nombre b{ font-family: var(--titre); font-weight:900; font-size:1.7rem; color:#fff;
  font-variant-numeric: tabular-nums; margin-right:4px; }
.pot-seuil{ font-size:.78rem; color:#7F91AB; }
.pot-jauge{ height:7px; border-radius:7px; background: rgba(169,188,212,0.14); overflow:hidden; }
.pot-jauge i{ display:block; height:100%; width:0; border-radius:7px;
  background: linear-gradient(90deg, #B7791F, var(--c-legendaire)); transition: width .6s ease; }

/* reglages Son / Animation */
.ouv-reglages{ display:flex; gap:8px; align-items:center; margin-left:auto; }
.ouv-bascule{ font: inherit; font-size:.8rem; color: var(--brume); background:transparent; cursor:pointer;
  border:1px solid rgba(169,188,212,0.22); border-radius:20px; padding:5px 11px; display:inline-flex; align-items:center; gap:7px; }
.ouv-bascule::before{ content:""; width:8px; height:8px; border-radius:50%; background: var(--brume); opacity:.4; }
.ouv-bascule[aria-pressed="true"]{ color:#fff; border-color: rgba(240,180,41,0.5); }
.ouv-bascule[aria-pressed="true"]::before{ background: var(--c-legendaire); opacity:1; }
.ouv-bascule:focus-visible{ outline:2px solid var(--c-legendaire); outline-offset:3px; }

/* la zone du tirage : la scene au centre, la rangee dessous */
.pack-zone{ flex-direction:column; align-items:stretch; gap:14px; }
.ouv-scene{ --ech:1; --pw:200px; --ph:280px; --cw:188px; --ch:263px;
  display:flex; justify-content:center; align-items:center; gap:0; padding: 8px 0 34px;
  transition: gap .5s cubic-bezier(.3,.7,.3,1); outline:none; }
.ouv-scene.etalee{ gap: clamp(18px, 5vw, 40px); }
.ouv-slot-pile{ position:relative; flex:none; width: calc(var(--pw) * var(--ech)); height: calc(var(--ph) * var(--ech));
  transition: width .5s cubic-bezier(.3,.7,.3,1); }
.ouv-scene.seule{ gap:0; }
.ouv-scene.seule .ouv-slot-pile{ width:0; }
.ouv-echelle{ position:absolute; left:0; top:0; width: var(--pw); height: var(--ph);
  transform: scale(var(--ech)); transform-origin: 0 0; }
.ouv-slot-carte{ position:relative; flex:none; width:0; height: var(--ch);
  transition: width .5s cubic-bezier(.3,.7,.3,1); }
.ouv-scene.etalee .ouv-slot-carte{ width: var(--cw); }
.ouv-slot-carte .card{ position:absolute; left:0; top:0; }
.ouv-echelle .paquet{ position:absolute; left:0; top:0; z-index:2; }
.ouv-rangee{ display:flex; flex-wrap:wrap; gap:12px; justify-content:center; }
.ouv-rangee .card{ animation: ouvArrivee .35s ease-out; }
@keyframes ouvArrivee{ from{ opacity:0; transform: translateY(-14px); } to{ opacity:1; transform:none; } }
.ouv-rangee:empty{ display:none; }
.pack-zone .suivant-ligne{ flex-basis:auto; display:flex; justify-content:center; margin-top:4px; }
.ouv-decouverte{ text-align:center; color: var(--brume); font-size:.88rem; min-height:1.3em; margin:-18px auto 0; max-width:52ch; }
.ouv-decouverte:empty{ visibility:hidden; }
.ouv-actions[hidden], .ouv-tout[hidden]{ display:none; }
.ouv-actions{ display:flex; flex-wrap:wrap; align-items:center; justify-content:center; gap:10px 16px; }
.ouv-consigne{ color:#7F91AB; font-size:.82rem; }
.ouv-tout{ font: inherit; font-size:.82rem; font-weight:600; color: var(--brume); background:transparent; cursor:pointer;
  border:1px solid rgba(169,188,212,0.22); border-radius:9px; padding:6px 13px; }
.ouv-tout:hover{ color:#fff; border-color: var(--c-legendaire); }
.ouv-lecteur{ position:absolute; width:1px; height:1px; overflow:hidden; clip: rect(0 0 0 0); margin:0; }

/* la pile */
.ouv-pile{ position:absolute; left:6px; top:8px; width: 188px; height: 263px; z-index:1;
  border:none; padding:0; background:none; cursor:pointer; font: inherit; color: inherit; }
.ouv-pile:focus-visible{ outline:2px solid var(--c-legendaire); outline-offset:8px; border-radius:14px; }
.ouv-pile .card{ position:absolute; left:0; top:0; width:188px; height:263px; pointer-events:none; }
.ouv-pile .ouv-compte{ position:absolute; left:0; right:0; bottom:-26px; text-align:center; font-size:.8rem; color: var(--brume); }
.ouv-pile.dedans{ transform: translateY(12%) scale(.9); }
.ouv-pile.emerge{ animation: ouvEmerge .75s cubic-bezier(.2,.7,.3,1.15) forwards; }
@keyframes ouvEmerge{ 0%{ transform: translateY(12%) scale(.9); } 55%{ transform: translateY(-16%) scale(.97); } 100%{ transform:none; } }
.ouv-dos.lueur-rare .face-back{ box-shadow: 0 0 0 2px var(--c-rare), 0 0 26px 4px rgba(47,124,246,.75); animation: ouvPulse 1.1s ease-in-out infinite; }
.ouv-dos.lueur-leg .face-back{ box-shadow: 0 0 0 2px var(--c-legendaire), 0 0 34px 8px rgba(240,180,41,.8); animation: ouvPulse .8s ease-in-out infinite; }
@keyframes ouvPulse{ 50%{ filter: brightness(1.35); } }
.card.ouv-eclat .face-front{ animation: ouvEclat .7s ease-out; }
@keyframes ouvEclat{ 0%{ filter: brightness(2.2); } 100%{ filter: brightness(1); } }

/* la perforation : dents fines, trait dore qui la suit */
.paquet .paquet-perfo{ position:absolute; left:6px; right:6px; width: calc(100% - 12px); height:10px;
  top: calc(var(--h-languette) - 5px); z-index:3; overflow:visible; pointer-events:none; }
.paquet .perfo-lueur{ filter: drop-shadow(0 0 2px rgba(255,236,170,.9)) drop-shadow(0 0 5px rgba(240,180,41,.7)); }
/* le trait dore se devoile de gauche a droite : un cache dont la largeur grandit */
.paquet .perfo-masque{ position:absolute; left:6px; top: calc(var(--h-languette) - 12px); height:24px; width:0;
  overflow:hidden; z-index:3; pointer-events:none; transition: width .35s ease-in; }
.paquet .perfo-masque .paquet-perfo{ left:0; right:auto; top:7px; width:188px; }
.paquet-perfo polyline{ fill:none; vector-effect: non-scaling-stroke; stroke-linejoin:round; }
.paquet-perfo .perfo-base{ stroke: rgba(255,255,255,.32); stroke-width:1; }
.paquet.achete .paquet-perfo .perfo-base{ stroke: rgba(90,55,5,.45); }
.paquet-perfo .perfo-trace{ stroke:#FFE9A8; stroke-width:2; }
.paquet.achete .paquet-perfo .perfo-trace{ stroke:#fff; }
@media (hover: hover){
  .paquet:not(.charge):not(.dechire):hover .perfo-masque{ width:188px; transition: width 1.6s linear; }
}

/* 1. la charge */
.paquet.charge{ pointer-events:none; animation: ouvCharge .65s ease-in forwards; }
.paquet.charge .perfo-masque{ width:188px; transition: width .3s ease-out; }
.paquet.charge .perfo-lueur{ animation: ouvLueur .65s ease-in forwards; }
@keyframes ouvCharge{ 0%{ transform:none; } 20%{ transform: translateX(-1px) rotate(-.5deg) scale(1.01); }
  40%{ transform: translateX(1px) rotate(.8deg) scale(1.02); } 60%{ transform: translateX(-2px) rotate(-1.3deg) scale(1.03); }
  80%{ transform: translateX(2px) rotate(1.7deg) scale(1.04); } 100%{ transform: scale(1.05); } }
@keyframes ouvLueur{ to{ filter: drop-shadow(0 0 3px #fff6d6) drop-shadow(0 0 12px rgba(240,180,41,.95)); } }

/* 2. la dechirure : le coin droit part d'abord, le gauche tient, puis tout lache */
.ouv-echelle .paquet.dechire{ transform: scale(1.05); }
.ouv-echelle .paquet.dechire .paquet-languette{ transition:none; transform-origin: 0% 100%;
  animation: ouvDechirure .95s cubic-bezier(.35,.1,.3,1) forwards; }
.ouv-echelle .paquet.dechire .paquet-corps{ transition:none; transform:none; opacity:1; }
.ouv-echelle .paquet.dechire .perfo-masque{ width:0; transition: width .5s cubic-bezier(.4,0,.6,1); }
.ouv-echelle .paquet.dechire .perfo-base{ opacity:0; transition: opacity .3s; }
.ouv-echelle .paquet.dechire .perfo-lueur{ animation: ouvFlash .6s ease-out forwards; }
@keyframes ouvFlash{ 0%{ opacity:1; filter: drop-shadow(0 0 3px #fff6d6) drop-shadow(0 0 12px rgba(240,180,41,.95)); }
  40%{ opacity:1; filter: drop-shadow(0 0 6px #fff6d6) drop-shadow(0 0 26px rgba(255,236,170,.95)); } 100%{ opacity:0; } }
@keyframes ouvDechirure{ 0%{ transform:none; opacity:1; } 22%{ transform: rotate(-4deg); }
  48%{ transform: rotate(-11deg) translate(1%, -4%); } 62%{ transform: rotate(-14deg) translate(6%, -16%); }
  100%{ transform: rotate(30deg) translate(95%, -95%); opacity:0; } }

/* 3. la sortie : le paquet tombe, la pile monte */
.ouv-echelle .paquet.sortie .paquet-corps{ animation: ouvDescente .6s cubic-bezier(.5,0,.8,.5) forwards; }
.ouv-echelle .paquet.sortie .paquet-etiquette, .ouv-echelle .paquet.sortie .paquet-bande{ opacity:0; transition: opacity .3s; }
@keyframes ouvDescente{ to{ transform: translateY(70%) scale(.96); opacity:0; } }

/* telephone : le paquet et la pile se reduisent pour tenir a cote de la carte */
@media (max-width: 560px){
  .ouv-scene{ --ech:.82; --cw:164px; --ch:240px; }
  .ouv-reglages{ margin-left:0; }
}

@media (prefers-reduced-motion: reduce){
  .ouv-scene, .ouv-slot-pile, .ouv-slot-carte, .pot-jauge i, .perfo-masque{ transition:none !important; }
  .paquet.charge, .ouv-pile.emerge, .ouv-rangee .card, .ouv-dos .face-back, .card.ouv-eclat .face-front,
  .ouv-echelle .paquet.dechire .paquet-languette, .ouv-echelle .paquet.sortie .paquet-corps{ animation:none !important; }
}
"""
ecrire('style.css', css)

print(u'patch64 applique : index.html, app.js, style.css')
