# -*- coding: utf-8 -*-
u"""
patch179 — la carte en grand (aperçu validé le 25 octobre : « Je préfère le A »).
Toucher une carte de sa collection l'ouvre en grand : on l'incline au doigt
ou à la souris (la lumière glisse dessus), on la retourne d'un toucher pour
voir son dos de carte équipé ; les informations restent en dessous.
- Front : la fiche existante, avec la carte en 3D en haut.
- Terra : une fiche nouvelle (rien ne s'ouvrait jusqu'ici) : habitants,
  rareté, exemplaires, gentilé, le savais-tu, Ma vitrine, Échange.
Safari : l'autre face est cachée à mi-retournement (sinon le texte de la face
apparaît à l'envers au dos).
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
assert 'patch179' not in js

# Front : la carte de la fiche passe dans la scène 3D
js = rempl(js, u"""      <div class="fc-tete">
        <div class="fc-carte${auroreFront(entry.code) ? ' aurore ' + tier.id : ''}">""",
u"""      <div class="fc-tete">${carte3dDebut(190, 266, 1.3)}
        <div class="fc-carte${auroreFront(entry.code) ? ' aurore ' + tier.id : ''}">""", 'fiche debut')
js = rempl(js, u"""              <div class="carte-lisere"><span></span><span></span><span></span></div>
            </div>
          </div>
        </div>
      </div>
      <div class="fc-corps">""", u"""              <div class="carte-lisere"><span></span><span></span><span></span></div>
            </div>
          </div>
        </div>${carte3dFin(190, 266)}
      </div>
      <div class="fc-corps">""", 'fiche fin')
js = rempl(js, u"""  const boite = document.querySelector('#fenetre .fiche');
  if(!boite) return;
  boite.addEventListener('click', (e) => {
    const b = e.target.closest('[data-fc]');""", u"""  const boite = document.querySelector('#fenetre .fiche');
  if(!boite) return;
  armerCarte3d(boite.querySelector('.c3d'));   // patch179
  boite.addEventListener('click', (e) => {
    const b = e.target.closest('[data-fc]');""", 'fiche armer')

# Terra : les cartes de la grille s'ouvrent
js = rempl(js, u"""    ? liste.slice(0, terraLimite).map(miniTerra).join('')""",
u"""    ? liste.slice(0, terraLimite).map(e => miniTerra(e).replace('<div class="mini ', '<div data-tcode="' + echapperTexte(e.code) + '" tabindex="0" role="button" class="mini ')).join('')""", 'grille terra')
js = rempl(js, u"""function clicCollectionTerra(e){
  if(clicCollections(e)) return;   // patch112""", u"""function clicCollectionTerra(e){
  if(clicCollections(e)) return;   // patch112
  const carteT = e.target.closest('[data-tcode]');   // patch179
  if(carteT){ ouvrirCarteTerra(carteT.dataset.tcode); return; }""", 'clic terra')

js += u"""

// ---------- patch179 : la carte en grand, inclinable et retournable ----------
// La carte garde sa taille de base (bw x bh) et elle est agrandie d'un coup
// (--s) : textes et dessins restent ceux de la carte du jeu.
function carte3dDebut(bw, bh, s){
  return `<div class="c3d" style="--bw:${bw}px;--bh:${bh}px;--s:${s}">
    <div class="c3d-scene"><div class="c3d-carte" tabindex="0" role="button" aria-label="Retourner la carte"><div class="c3d-tourne">
      <div class="c3d-face c3d-devant"><div class="c3d-base">`;
}
function carte3dFin(){
  return `</div><span class="c3d-reflet"></span></div>
      <div class="c3d-face c3d-dos"><div class="c3d-base"><div class="face face-back c3d-dosint">${DOS_MOTIF_SVG}
        <span class="dos-coin hg"></span><span class="dos-coin hd"></span><span class="dos-coin bg"></span><span class="dos-coin bd"></span>
        <div class="dos-embleme">${ICONE_EPINGLE}</div></div></div><span class="c3d-reflet"></span></div>
    </div></div><div class="c3d-ombre"></div></div>
    <p class="c3d-aide">Fais glisser pour incliner · touche pour retourner</p></div>`;
}
function armerCarte3d(racine){
  if(!racine) return;
  const carte = racine.querySelector('.c3d-carte');
  const reduit = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let glisse = false, depart = null, bouge = false, dernier = 0;
  const incliner = (x, y) => {
    carte.style.setProperty('--ry', (x * 20).toFixed(2) + 'deg');
    carte.style.setProperty('--rx', (-y * 16).toFixed(2) + 'deg');
    carte.style.setProperty('--gx', (50 + x * 50).toFixed(1) + '%');
    carte.style.setProperty('--gy', (50 + y * 50).toFixed(1) + '%');
  };
  const pos = (e) => { const r = carte.getBoundingClientRect();
    return [Math.max(-1, Math.min(1, ((e.clientX - r.left) / r.width - .5) * 2)), Math.max(-1, Math.min(1, ((e.clientY - r.top) / r.height - .5) * 2))]; };
  const retourner = () => carte.classList.toggle('retournee');
  racine.addEventListener('pointermove', (e) => {
    if(e.pointerType !== 'mouse' && !glisse) return;
    const [x, y] = pos(e); incliner(x, y); dernier = performance.now();
    if(depart && Math.hypot(e.clientX - depart[0], e.clientY - depart[1]) > 8) bouge = true;
  });
  carte.addEventListener('pointerdown', (e) => { glisse = true; bouge = false; depart = [e.clientX, e.clientY]; try{ carte.setPointerCapture(e.pointerId); }catch(err){} });
  carte.addEventListener('pointerup', () => { glisse = false; if(!bouge) retourner(); depart = null; });
  carte.addEventListener('pointercancel', () => { glisse = false; depart = null; });
  racine.addEventListener('pointerleave', () => { if(!glisse) dernier = 0; });
  carte.addEventListener('keydown', (e) => { if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); retourner(); } });
  if(reduit) return;
  // au repos, la carte se balance doucement (s'arrête quand la fiche se ferme)
  const boucle = (t) => {
    if(!racine.isConnected) return;
    if(performance.now() - dernier > 1500) incliner(Math.sin(t / 1400) * .3, Math.sin(t / 1900 + 1) * .22);
    requestAnimationFrame(boucle);
  };
  requestAnimationFrame(boucle);
}

// Terra : la fiche d'une carte de la collection
async function ouvrirCarteTerra(code){
  const e = terraCollection.get(code);
  if(!e) return;
  const nb = (x) => Number(x || 0).toLocaleString('fr-FR');
  const rendre = (d) => {
    const gentile = d && d.gentile ? String(d.gentile).trim() : '';
    const faits = d ? faitsTries(d.faits) : null;
    const savais = faits === null ? '<p class="fc-attente">Recherche des faits…</p>'
      : !faits.length ? '' : '<h3>Le savais-tu ?</h3>' + faits.slice(0, 3).map((f, i) => `<div class="fc-fait${i ? '' : ' phare'}"><i>${i ? iconeFait(f.t) : '🏅'}</i><span>${i ? echapperTexte(f.t) : '<b>' + echapperTexte(f.t) + '</b>'}</span></div>`).join('');
    const dbl = libresTerra(e);
    return `
    <div class="fenetre fiche fiche-terra ${e.tier.id}" data-tcode="${echapperTexte(code)}" role="dialog" aria-modal="true" aria-labelledby="ftNom">
      <button class="fc-fermer" data-ft="fermer" aria-label="Fermer">✕</button>
      <div class="fc-tete">${carte3dDebut(150, 225, 1.65)}${miniTerra(e)}${carte3dFin()}</div>
      <div class="fc-corps">
        <h2 id="ftNom" class="fc-nom ${e.nom.length > 22 ? 'long' : ''}">${echapperTexte(e.nom)}</h2>
        <p class="fc-dep">${DEPT_NAMES[e.dept] ? echapperTexte(DEPT_NAMES[e.dept]) + ' (' + echapperTexte(e.dept) + ')' : echapperTexte(e.dept)}</p>
        ${gentile ? `<p class="fc-gent">les ${echapperTexte(gentile)}</p>` : ''}
        <div class="fc-chiffres">
          <div class="fc-ch"><b>${nb(e.pop)}</b><span>habitants</span></div>
          <div class="fc-ch"><b class="fc-rar">${e.tier.label}</b><span>${e.rank ? 'n° ' + nb(e.rank) + ' / ' + nb(e.tierSize) : 'rareté'}</span></div>
          <div class="fc-ch"><b>×${nb(e.exemplaires)}</b><span>${e.aurore > 0 ? 'dont Aurore' : dbl > 0 ? dbl + ' doublon' + (dbl > 1 ? 's' : '') : 'exemplaire'}</span></div>
        </div>
        ${savais}
        <div class="fc-actions">
          <button class="fc-btn" data-ft="vitrine">Ma vitrine</button>
          <button class="fc-btn principal" data-ft="echange">Échanger</button>
        </div>
      </div>
    </div>`;
  };
  const fermer = ouvrirFenetre(rendre(null));
  const brancher = () => {
    const boite = document.querySelector('#fenetre .fiche-terra');
    if(!boite) return;
    armerCarte3d(boite.querySelector('.c3d'));
    boite.addEventListener('click', async (ev) => {
      const b = ev.target.closest('[data-ft]');
      if(!b) return;
      if(b.dataset.ft === 'fermer'){ fermer(null); return; }
      if(b.dataset.ft === 'echange'){ fermer(null); const t = document.querySelector('.tab[data-tab="echange"]'); if(t) t.click(); return; }
      if(b.dataset.ft === 'vitrine'){ b.disabled = true; const vt = await chargerVitrine(window.__monId); fermer(null); setTimeout(() => ouvrirChoixVitrine(vt, 'panneau'), 200); }
    });
  };
  brancher();
  let d = {};
  try { d = await detailsCommune(code); } catch(err){ d = {}; }
  const ouverte = document.querySelector('#fenetre .fiche-terra[data-tcode="' + code + '"]');
  if(!ouverte) return;
  // on ne remplace que le bas : la carte garde sa position et son côté
  const tmp = document.createElement('div'); tmp.innerHTML = rendre(d);
  const neuf = tmp.querySelector('.fc-corps'), vieux = ouverte.querySelector('.fc-corps');
  if(neuf && vieux) vieux.replaceWith(neuf);
}
"""
ecrire('app.js', js)

css = lire('style.css')
assert 'patch179' not in css
css += u"""

/* ---------- patch179 : la carte en grand ---------- */
.c3d{ display: grid; justify-items: center; gap: 6px; }
.c3d-scene{ perspective: 1100px; display: grid; justify-items: center; touch-action: none; padding-top: 4px; }
.c3d-carte{ --rx: 0deg; --ry: 0deg; --gx: 50%; --gy: 50%;
  width: calc(var(--bw) * var(--s)); height: calc(var(--bh) * var(--s)); max-width: 100%;
  position: relative; cursor: grab; outline: none;
  transform: rotateX(var(--rx)) rotateY(var(--ry)); transform-style: preserve-3d; }
.c3d-carte:active{ cursor: grabbing; }
.c3d-carte:focus-visible{ outline: 2px solid var(--c-legendaire); outline-offset: 6px; border-radius: 16px; }
.c3d-tourne{ position: absolute; inset: 0; transform-style: preserve-3d; transition: transform .7s cubic-bezier(.45,.05,.2,1); }
.c3d-carte.retournee .c3d-tourne{ transform: rotateY(180deg); }
.c3d-face{ position: absolute; inset: 0; backface-visibility: hidden; -webkit-backface-visibility: hidden; border-radius: calc(14px * var(--s)); }
.c3d-dos{ transform: rotateY(180deg); }
/* Safari laisse parfois voir l'autre face à l'envers : on la cache à mi-retournement */
.c3d-devant{ visibility: visible; transition: visibility 0s linear .35s; }
.c3d-carte.retournee .c3d-devant{ visibility: hidden; }
.c3d-dos{ visibility: hidden; transition: visibility 0s linear .35s; }
.c3d-carte.retournee .c3d-dos{ visibility: visible; }
.c3d-base{ width: var(--bw); height: var(--bh); transform: scale(var(--s)); transform-origin: 0 0; position: relative; }
.c3d-base > .mini{ width: 100%; height: 100%; }
.c3d-base > .mini:hover{ transform: none; }
.c3d-base .c3d-dosint{ position: absolute; inset: 0; backface-visibility: visible; -webkit-backface-visibility: visible; }
.fiche .c3d .fc-carte{ margin: 0; }
.c3d-reflet{ position: absolute; inset: 0; z-index: 6; pointer-events: none; border-radius: inherit; mix-blend-mode: overlay;
  background: radial-gradient(farthest-corner circle at var(--gx) var(--gy), rgba(255,255,255,.45), rgba(255,255,255,.07) 30%, transparent 60%); }
.c3d-ombre{ width: 60%; height: 16px; border-radius: 50%; background: rgba(0,0,0,.5); filter: blur(12px); margin-top: 2px; }
.c3d-aide{ margin: 0; font-size: .74rem; color: var(--brume); text-align: center; }
[data-tcode].mini{ cursor: pointer; }
[data-tcode].mini:focus-visible{ outline: 2px solid var(--c-legendaire); outline-offset: 2px; }
.fiche-terra .fc-actions{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
@media (prefers-reduced-motion: reduce){ .c3d-tourne{ transition: none; } }
@media (max-width: 420px){ .c3d{ --s: 1.2 !important; } .fiche-terra .c3d{ --s: 1.5 !important; } }
"""
ecrire('style.css', css)

# la fiche Front affichait seulement le haut de la carte : on montre la carte entière, comme en Terra
js = lire('app.js')
i = js.index("${carte3dDebut(190, 266, 1.3)}")
j = js.index("${carte3dFin(190, 266)}") + len("${carte3dFin(190, 266)}")
js = js[:i] + "${carte3dDebut(150, 225, 1.65)}${miniTerra({ ...entry, exemplaires: 1, aurore: auroreFront(entry.code) ? 1 : 0 })}${carte3dFin()}" + js[j:]
ecrire('app.js', js)
print(u'patch179 applique')
