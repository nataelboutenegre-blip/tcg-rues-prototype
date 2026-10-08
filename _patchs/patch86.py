# -*- coding: utf-8 -*-
u"""
patch86 — Combats épiques : l'assaut mis en scène (aperçu validé le 8 octobre).

- Chaque attaque (depuis la carte ou l'onglet Combat) ouvre un écran
  d'assaut : ta commune la plus proche face à la cible (avec la distance,
  ou « attaque à distance » au-delà de 20 km), la jauge de tes chances, une
  aiguille qui ralentit et s'arrête sur le résultat, puis le verdict.
  Le résultat est celui du serveur, inchangé ; seule la mise en scène est
  nouvelle.
- La série : 3 pastilles sous la commune attaquée, vertes pour chaque
  victoire, rouges à la défaite.
- La conquête : les pastilles tombent, le drapeau se plante, le bonus et
  le monument éventuel s'affichent (remplace l'ancienne fenêtre).
- Durée : ~1,2 s pour commun / peu commun, ~2,5 s pour rare / légendaire.
  Un clic passe l'animation ; le réglage « Animation » des paquets la coupe.
- Bandeau pour tous : quand une LÉGENDAIRE est conquise, les autres joueurs
  connectés voient « X a pris Lyon à Y » (vérifié toutes les minutes via la
  fonction journal existante, aucun SQL).
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

# --- sons d'assaut, dans la meme usine a sons que les paquets -------------------
js = rempl(js,
u'''    tick(){ if(pret()) note(880, 0, 0.09, 'sine', 0.25); },''',
u'''    tick(){ if(pret()) note(880, 0, 0.09, 'sine', 0.25); },
    // patch86 : l'assaut
    assautChoc(){ if(pret()){ note(90, 0, 0.32, 'sine', 0.5); bruit(0.18, 300, 120, 0.25, 'lowpass'); } },
    assautTic(){ if(pret()) note(1700, 0, 0.025, 'square', 0.05); },
    assautGagne(){ if(pret()){ note(523, 0, 0.18, 'triangle', 0.3); note(784, 0.1, 0.32, 'triangle', 0.3); } },
    assautPerdu(){ if(pret()){ note(330, 0, 0.25, 'sawtooth', 0.16); note(220, 0.15, 0.42, 'sawtooth', 0.14); } },
    assautConquete(){ if(pret()) [523, 659, 784, 1047].forEach((f, i) => note(f, i * 0.12, 0.5, 'triangle', 0.3)); },''',
'sons')

# --- l'ecran d'assaut ---------------------------------------------------------
js = rempl(js,
u'''function celebrerConquete({ nom, tier, dept, bonus, code }){''',
u'''// ---------- L'assaut mis en scene (patch86) ----------
function kmEntre(la1, lo1, la2, lo2){
  const R = 6371, r = (x) => x * Math.PI / 180;
  const h = Math.sin(r(la2 - la1) / 2) ** 2 + Math.cos(r(la1)) * Math.cos(r(la2)) * Math.sin(r(lo2 - lo1) / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}
// Ma commune la plus proche d'un point : celle qu'on montre a l'assaut.
// C'est la regle de proximite du serveur (20 km) rendue visible.
function maCommuneLaPlusProche(lat, lon, saufCode){
  let meilleure = null, km = Infinity;
  if(lat == null || lon == null) return null;
  for(const e of collectionMap.values()){
    if(e.code === saufCode || e.lat == null || e.lon == null) continue;
    const d = kmEntre(lat, lon, e.lat, e.lon);
    if(d < km){ km = d; meilleure = e; }
  }
  return meilleure ? { entry: meilleure, km } : null;
}
function carteAssaut(e, qui){
  const t = e.tier && e.tier.id ? e.tier : (TIERS.find(x => x.id === e.tier) || TIERS[0]);
  return `<div class="as-carte ${t.id}">
    <div class="as-h"><span class="as-pill">${t.label}</span></div>
    <div class="as-art">${artCommune(e, t.id)}<span class="as-dep">${echapperTexte(e.dept || '')}</span></div>
    <p class="as-nom ${String(e.nom).length > 13 ? 'long' : ''}">${echapperTexte(e.nom)}</p>
    <p class="as-dpt">${echapperTexte(DEPT_NAMES[e.dept] || '')}${e.dept ? ` (${echapperTexte(e.dept)})` : ''}</p>
    <p class="as-qui">${qui}</p>
    <div class="as-lis"><i></i><i></i><i></i></div>
  </div>`;
}

// cible : { code, nom, dept, tier (id), pseudo, lat, lon } — capturee AVANT
// le rechargement des possessions. r : la reponse de attaquer().
function mettreEnSceneAssaut(cible, r){
  const tierId = cible.tier && cible.tier.id ? cible.tier.id : cible.tier;
  const grand = tierId === 'rare' || tierId === 'legendaire';
  const anim = ouvAnim && !REDUCED_MOTION;
  const proche = maCommuneLaPlusProche(cible.lat, cible.lon, cible.code);
  const chances = Math.max(1, Math.min(99, Number(r.chances) || 50));
  const serieAvant = r.conquise ? 2 : (r.gagne ? Math.max(0, Number(r.victoires_consecutives) - 1) : null);
  const res = r.conquise ? 'conq' : (r.gagne ? 'ok' : 'ko');
  // ou l'aiguille s'arrete : dans le vert si gagne, dans le rouge sinon
  const arret = res === 'ko' ? chances + (100 - chances) * (0.25 + Math.random() * 0.6)
                             : chances * (0.15 + Math.random() * 0.7);
  const nomCible = echapperTexte(cible.nom);
  const bonus = r.conquise ? Math.floor((PRIX_RACHAT[tierId] || 0) * BONUS_CONQUETE_PART) : 0;
  const mon = r.conquise && typeof monumentDe === 'function' ? monumentDe(cible.code) : null;
  const ligneProche = !proche ? '<span class="as-loin">Tu n’as pas encore de commune</span>'
    : proche.km <= 20 ? `Ta commune la plus proche<br><b>à ${Math.max(1, Math.round(proche.km))} km de ${nomCible}</b>`
    : `<span class="as-loin">Attaque à distance · ${Math.round(proche.km).toLocaleString('fr-FR')} km</span>`;
  const pastilles = [0, 1, 2].map(i => `<i class="${serieAvant != null && i < serieAvant ? 'gagne' : ''}"></i>`).join('');
  const intens = (INTENSITES.find(x => x.id === intensiteChoisie) || INTENSITES[1]).label.toLowerCase();

  const fermer = ouvrirFenetre(`
    <div class="fenetre assaut ${grand ? 'grand' : ''}" role="dialog" aria-modal="true" aria-labelledby="asVerdict">
      <p class="as-surtitre">Assaut · intensité ${intens}</p>
      <div class="as-duel">
        <div class="as-cote as-att">${proche ? carteAssaut(proche.entry, 'à toi') : '<div class="as-carte vide"></div>'}<p class="as-proche">${ligneProche}</p></div>
        <div class="as-vs">VS</div>
        <div class="as-cote as-cib">
          <div class="as-drapeau" aria-hidden="true"><svg viewBox="0 0 40 56"><path d="M6 4v50" stroke="#e8edf5" stroke-width="3" stroke-linecap="round"/><path d="M7 5 C18 1, 24 11, 37 6 L37 24 C24 29, 18 19, 7 23 Z" fill="#F0B429" stroke="#9a6a10" stroke-width="1"/></svg></div>
          ${carteAssaut(cible, 'à ' + echapperTexte(cible.pseudo || 'un joueur'))}
          <div class="as-pastilles" aria-hidden="true">${pastilles}</div>
          <div class="as-onde" aria-hidden="true"></div>
        </div>
      </div>
      <div class="as-jauge"><div class="as-cadran"><div class="as-zone" style="width:${chances}%"></div><div class="as-aiguille"></div></div>
        <div class="as-jleg"><span>Tes chances : <b>${chances} %</b></span>${r.cout ? `<span>Coût : <b class="blanc">${Number(r.cout).toLocaleString('fr-FR')} pts</b></span>` : ''}</div></div>
      <h2 class="as-verdict" id="asVerdict"></h2>
      <p class="as-detail"></p>
      <div class="as-actions"></div>
    </div>`);
  const fen = document.querySelector('#fenetre .assaut');
  if(!fen) return;
  const $q = (s) => fen.querySelector(s);
  let passe = !anim;
  fen.addEventListener('click', (e) => { if(!e.target.closest('button')) passe = true; });
  const att = (ms) => new Promise(ok => { if(passe) return ok(); const t0 = performance.now();
    const pas = () => (passe || performance.now() - t0 >= ms) ? ok() : requestAnimationFrame(pas); requestAnimationFrame(pas); });
  const jouer = (el, kf, opt) => { if(!el) return; if(passe){ Object.assign(el.style, kf[kf.length - 1]); return; }
    el.animate(kf, Object.assign({ fill: 'forwards' }, opt)); };

  (async () => {
    const att1 = $q('.as-att .as-carte'), cib1 = $q('.as-cib .as-carte'), vs = $q('.as-vs');
    jouer(att1, [{ opacity: 0, transform: 'translateX(-50px) rotate(-6deg)' }, { opacity: 1, transform: 'none' }], { duration: 420, easing: 'cubic-bezier(.2,.8,.3,1.2)' });
    await att(100);
    jouer(cib1, [{ opacity: 0, transform: 'translateX(50px) rotate(6deg)' }, { opacity: 1, transform: 'none' }], { duration: 420, easing: 'cubic-bezier(.2,.8,.3,1.2)' });
    await att(grand ? 380 : 250);
    jouer(vs, [{ opacity: 0, transform: 'scale(.4)' }, { opacity: 1, transform: 'scale(1.25)' }, { opacity: 1, transform: 'scale(1)' }], { duration: 340 });
    if(!passe) sonsOuverture.assautChoc();
    await att(grand ? 320 : 150);
    // l'aiguille balaie la jauge, ralentit, se pose sur le resultat
    const ag = $q('.as-aiguille'), duree = grand ? 1500 : 650, debut = performance.now();
    await new Promise(fin => {
      const pas = (now) => {
        const x = passe ? 1 : Math.min(1, (now - debut) / duree), e = 1 - Math.pow(1 - x, 3);
        const tri = Math.abs((((e * 2.5) % 2) + 2) % 2 - 1);
        ag.style.left = (x < 1 ? (1 - tri) * 100 * (1 - e) + arret * e : arret) + '%';
        if(!passe && x < 0.9 && Math.random() < 0.22) sonsOuverture.assautTic();
        x < 1 ? requestAnimationFrame(pas) : fin();
      };
      requestAnimationFrame(pas);
    });
    await att(180);
    const v = $q('.as-verdict'), d = $q('.as-detail'), bl = [...fen.querySelectorAll('.as-pastilles i')];
    const tas = $q('.as-actions');
    if(res === 'ok'){
      v.className = 'as-verdict ok'; v.textContent = 'Victoire !';
      if(serieAvant != null && bl[serieAvant]) bl[serieAvant].className = 'gagne';
      jouer(cib1, [{ transform: 'translateX(-6px) rotate(-1deg)' }, { transform: 'translateX(5px) rotate(1deg)' }, { transform: 'none' }], { duration: 380 });
      const reste = 3 - Number(r.victoires_consecutives || 0);
      d.innerHTML = `${nomCible} vacille <span class="as-serie">${[0, 1, 2].map(i => `<i class="${i < r.victoires_consecutives ? 'plein' : ''}"></i>`).join('')}</span><br>`
        + (reste <= 1 ? 'Encore une victoire pour la prendre.' : `Encore ${reste} victoires pour la prendre.`)
        + ` <span class="as-petit">Prochain assaut dans ${Math.round((DELAI_ATTAQUE_MS[tierId] || 0) / 60000) >= 60 ? Math.round(DELAI_ATTAQUE_MS[tierId] / 3600000) + ' h' : Math.round((DELAI_ATTAQUE_MS[tierId] || 0) / 60000) + ' min'}.</span>`;
      if(!passe) sonsOuverture.assautGagne();
    } else if(res === 'ko'){
      v.className = 'as-verdict ko'; v.textContent = 'Repoussé';
      bl.forEach(b => b.className = 'perdu');
      jouer(att1, [{ transform: 'translateX(-6px) rotate(-1deg)' }, { transform: 'translateX(5px) rotate(1deg)' }, { transform: 'none' }], { duration: 380 });
      d.innerHTML = `${nomCible} tient bon : ta série repart à zéro.`;
      if(!passe) sonsOuverture.assautPerdu();
    } else {
      v.className = 'as-verdict conq'; v.textContent = `${cible.nom} est à toi !`;
      bl.forEach((b, i) => { b.className = 'gagne'; setTimeout(() => b.classList.add('tombe'), passe ? 0 : i * 110); });
      const qui = $q('.as-cib .as-qui'); if(qui) qui.textContent = 'à toi';
      if(!passe) sonsOuverture.assautConquete();
      await att(320);
      jouer($q('.as-drapeau'), [{ opacity: 0, transform: 'translateY(-40px)' }, { opacity: 1, transform: 'translateY(4px)' }, { opacity: 1, transform: 'none' }], { duration: 420, easing: 'ease-in' });
      if(!passe) jouer($q('.as-onde'), [{ opacity: .9, transform: 'scale(1)' }, { opacity: 0, transform: 'scale(14)' }], { duration: 1100, easing: 'ease-out' });
      d.innerHTML = `+${bonus.toLocaleString('fr-FR')} pts de bonus · protégée 3 h · revente au jeu dans 12 h`
        + (mon ? `<span class="as-mon">${ICONE_MONUMENT}Monument conquis : <b>${echapperTexte(mon.nom)}</b></span>` : '');
    }
    jouer(v, [{ opacity: 0, transform: 'scale(1.6)' }, { opacity: 1, transform: 'scale(1)' }], { duration: 300, easing: 'cubic-bezier(.2,.8,.3,1.3)' });
    tas.innerHTML = res === 'conq'
      ? '<button type="button" class="open-btn" data-as="carte">Voir sur la carte</button><button type="button" class="open-btn secondary" data-as="fermer">Fermer</button>'
      : '<button type="button" class="open-btn" data-as="fermer">OK</button>';
    jouer(tas, [{ opacity: 0 }, { opacity: 1 }], { duration: 250 });
    tas.addEventListener('click', (e) => {
      const b = e.target.closest('[data-as]'); if(!b) return;
      fermer(true);
      if(b.dataset.as === 'carte'){
        const t = document.querySelector('.tab[data-tab="territoire"]'); if(t) t.click();
        setTimeout(() => centrerSurCommune(cible.lat, cible.lon), 250);
      }
    });
    const premier = tas.querySelector('button'); if(premier) premier.focus();
  })();
}

// Ce qu'on sait de la cible avant que l'attaque ne change les possessions
function cibleAssaut(code, repli){
  const c = othersMap.get(code) || {};
  return {
    code, nom: c.nom || (repli && repli.nom) || 'la commune',
    dept: c.dept || (repli && repli.departement) || '',
    tier: c.tier || (repli && repli.tier) || 'commun',
    pseudo: c.pseudo || (repli && repli.pseudo) || '',
    lat: c.lat, lon: c.lon, pop: c.pop, photo: c.photo || '', rank: c.rank,
  };
}

// ---------- Le bandeau des grandes conquetes (patch86) ----------
// Une legendaire qui change de mains, c'est un evenement : les joueurs
// connectes le voient. Verifie toutes les minutes avec la fonction journal.
let conquetesVues = null;
async function surveillerGrandesConquetes(){
  if(document.hidden) return;
  const { data, error } = await sb.rpc('journal', { p_mode: 'tous', p_type: 'conquete', p_limite: 8 });
  if(error || !Array.isArray(data)) return;
  const ids = data.map(x => Number(x.id));
  if(conquetesVues === null){ conquetesVues = Math.max(0, ...ids); return; }   // premier passage : rien d'ancien
  const neuves = data.filter(x => Number(x.id) > conquetesVues && x.tier === 'legendaire' && !x.je_suis_acteur)
                     .sort((a, b) => Number(a.id) - Number(b.id));
  conquetesVues = Math.max(conquetesVues, ...ids);
  neuves.forEach((x, i) => setTimeout(() => afficherGrandeConquete(x), i * 6500));
}
function afficherGrandeConquete(x){
  const el = document.createElement('div');
  el.className = 'grande-conquete';
  el.setAttribute('role', 'status');
  const victime = x.je_suis_cible ? 'toi' : (x.cible_pseudo || '');
  el.innerHTML = `<span class="gc-ico">⚔️</span><span class="gc-tx"><b><em>${echapperTexte(x.acteur_pseudo || 'Un joueur')}</em> a pris ${echapperTexte(x.commune_nom || '')}${victime ? ' à ' + echapperTexte(victime) : ''}</b><small>Légendaire · à l’instant</small></span>`;
  el.addEventListener('click', () => el.remove());
  document.body.appendChild(el);
  requestAnimationFrame(() => el.classList.add('visible'));
  setTimeout(() => { el.classList.remove('visible'); setTimeout(() => el.remove(), 400); }, 6000);
}
setInterval(surveillerGrandesConquetes, 60000);
setTimeout(surveillerGrandesConquetes, 5000);

function celebrerConquete({ nom, tier, dept, bonus, code }){''', 'ecran assaut')

# --- depuis la carte ------------------------------------------------------------
js = rempl(js,
u'''    const nom = c.nom, tier = c.tier.id, dept = c.dept;
    const { data, error } = await sb.rpc('attaquer', { p_commune_code: code, p_intensite: intensiteChoisie });
    if(error) throw error;
    const r = data[0];
    if(r.conquise){
      await loadMyCollection();
      await loadOthersPossessions();
      fermerPanneau();
      celebrerConquete({ nom, tier, dept, code, bonus: Math.floor(PRIX_RACHAT[tier] * BONUS_CONQUETE_PART) });
    } else if(r.gagne){
      notifier({ type: 'victoire', titre: `Victoire contre ${nom} (−${r.cout} pts)`,
        texte: r.victoires_consecutives >= 2 ? 'Encore une victoire pour la conquérir.' : `Série : ${r.victoires_consecutives} sur 3`,
        serie: r.victoires_consecutives });
    } else {
      notifier({ type: 'defaite', titre: `Défaite contre ${nom} (−${r.cout} pts)`,
        texte: `À ${r.chances} % : la série repart à zéro.`, serie: 0 });
    }''',
u'''    const cibleVue = cibleAssaut(code);
    const { data, error } = await sb.rpc('attaquer', { p_commune_code: code, p_intensite: intensiteChoisie });
    if(error) throw error;
    const r = data[0];
    // patch86 : l'assaut mis en scene remplace les notifications
    mettreEnSceneAssaut(cibleVue, r);
    if(r.conquise){
      await loadMyCollection();
      await loadOthersPossessions();
      fermerPanneau();
    }''', 'carte')

# --- depuis l'onglet Combat --------------------------------------------------------
js = rempl(js,
u'''        if(error) throw error;
        const result = data[0];
        const cible = combatCibles.find(x => x.commune_code === code);
        const nomCible = cible ? cible.communes.nom : 'la commune';
        if(result.conquise){
          await loadMyCollection();
          await loadOthersPossessions();
          celebrerConquete({
            nom: nomCible,
            code,
            tier: cible ? cible.communes.tier : '',
            dept: cible ? cible.communes.departement : '',
            bonus: cible ? Math.floor(PRIX_RACHAT[cible.communes.tier] * BONUS_CONQUETE_PART) : 0
          });
        } else if(result.gagne){
          notifier({
            type: 'victoire',
            titre: `Victoire contre ${nomCible}${result.cout ? ` (−${result.cout} pts)` : ''}`,
            texte: result.victoires_consecutives >= 2 ? 'Encore une victoire pour la conquérir.' : `Série : ${result.victoires_consecutives} sur 3`,
            serie: result.victoires_consecutives
          });
        } else {
          notifier({ type: 'defaite', titre: `Défaite contre ${nomCible}${result.cout ? ` (−${result.cout} pts)` : ''}`, texte: `${result.chances != null ? 'À ' + result.chances + ' % : la' : 'La'} série repart à zéro.`, serie: 0 });
        }''',
u'''        if(error) throw error;
        const result = data[0];
        const cible = combatCibles.find(x => x.commune_code === code);
        // patch86 : l'assaut mis en scene remplace les notifications
        mettreEnSceneAssaut(cibleVueCombat, result);
        if(result.conquise){
          await loadMyCollection();
          await loadOthersPossessions();
        }''', 'combat')
js = rempl(js,
u'''      combatActionEnCours = true;
      try{
        let { data, error } = await sb.rpc('attaquer', { p_commune_code: code, p_intensite: intensiteChoisie });''',
u'''      combatActionEnCours = true;
      try{
        const ciblePrevue = combatCibles.find(x => x.commune_code === code);
        const cibleVueCombat = cibleAssaut(code, ciblePrevue ? Object.assign({}, ciblePrevue.communes,
          { pseudo: ciblePrevue.pseudo || ciblePrevue.proprietaire_pseudo || (ciblePrevue.joueurs && ciblePrevue.joueurs.pseudo) }) : null);
        let { data, error } = await sb.rpc('attaquer', { p_commune_code: code, p_intensite: intensiteChoisie });''', 'combat avant')
ecrire('app.js', js)

css = lire('style.css')
css += u'''

/* ---------- patch86 : l'assaut mis en scene ---------- */
.fenetre.assaut{ width:min(470px, 100%); padding:22px 16px 18px; overflow:hidden;
  background: radial-gradient(90% 70% at 50% 40%, #1c3a68, #0b1830 78%); border:1px solid rgba(240,180,41,.35); }
.fenetre.assaut::before{ content:''; position:absolute; inset:0; opacity:.16; pointer-events:none;
  background: repeating-radial-gradient(circle at 50% 38%, transparent 0 34px, rgba(169,188,212,.5) 35px 36px); }
.as-surtitre{ position:relative; margin:0 0 14px; font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; color: var(--brume); }
.as-duel{ position:relative; display:flex; align-items:flex-start; justify-content:center; gap:clamp(8px, 4vw, 26px); margin-bottom:46px; }
.as-cote{ position:relative; display:flex; flex-direction:column; align-items:center; }
.as-vs{ align-self:center; font-family: var(--titre); font-weight:900; font-size:2rem; color: var(--c-legendaire); opacity:0; }
.as-carte{ width:clamp(118px, 34vw, 150px); aspect-ratio:188/263; border-radius:13px; background:#EEF2F7; color: var(--encre);
  border:4px solid var(--as-c, var(--c-commun)); padding:6px 0 0; display:flex; flex-direction:column; overflow:hidden; text-align:left;
  box-shadow:0 16px 36px rgba(0,0,0,.45); opacity:0; }
.as-carte.vide{ background: rgba(255,255,255,.05); border-style:dashed; border-color: rgba(169,188,212,.3); }
.as-carte.commun{ --as-c: var(--c-commun); } .as-carte.peucommun{ --as-c: var(--c-peucommun); }
.as-carte.rare{ --as-c: var(--c-rare); } .as-carte.legendaire{ --as-c: var(--c-legendaire); }
.as-h{ padding:0 7px 4px; }
.as-pill{ font-size:.58rem; font-weight:700; padding:2px 7px; border-radius:999px; background: var(--as-c); color:#fff; }
.as-carte.legendaire .as-pill{ color: var(--encre); }
.as-art{ position:relative; margin:0 6px; height:42%; border-radius:7px; overflow:hidden; }
.as-art > svg, .as-art > img{ width:100%; height:100%; display:block; object-fit:cover; }
.as-art > *:not(svg):not(.art-photo):not(.art-voile){ z-index:3; }
.as-dep{ position:absolute; right:5px; bottom:-5px; font-family: var(--titre); font-weight:900; font-size:2.3rem; line-height:1; color: rgba(255,255,255,.3); }
.as-nom{ font-family: var(--titre); font-weight:800; font-size:1.25rem; line-height:1.06; padding-bottom:.06em; margin:5px 7px 0; overflow-wrap:anywhere; }
.as-nom.long{ font-size:1rem; }
.as-dpt{ font-size:.64rem; color:#5A6B82; margin:1px 7px 0; }
.as-qui{ font-size:.66rem; font-weight:700; color:#3a4a62; margin:2px 7px 0; }
.as-lis{ margin-top:auto; display:flex; height:4px; } .as-lis i{ flex:1; }
.as-lis i:nth-child(1){ background:#2B4A9A; } .as-lis i:nth-child(2){ background:#fff; } .as-lis i:nth-child(3){ background:#E05252; }
.as-proche{ position:absolute; top:100%; margin:10px 0 0; width:max-content; max-width:46vw; text-align:center; font-size:.7rem; line-height:1.3; color: var(--brume); }
.as-proche b{ color: var(--vert, #2BD48B); font-weight:700; }
.as-loin{ color:#F0566A; font-weight:600; }
.as-pastilles{ position:absolute; top:100%; left:0; right:0; margin-top:16px; display:flex; gap:7px; justify-content:center; }
.as-pastilles i{ width:26%; height:11px; border-radius:999px; background: rgba(169,188,212,.28); border:1px solid rgba(169,188,212,.45); transition: background .3s, box-shadow .3s; }
.as-pastilles i.gagne{ background:#2BD48B; border-color:#7ff0c0; box-shadow:0 0 12px rgba(43,212,139,.6); }
.as-pastilles i.perdu{ background:#F0566A; border-color:#ff9aa8; box-shadow:0 0 12px rgba(240,86,106,.6); }
.as-pastilles i.tombe{ animation: asTombe .6s ease-in forwards; }
@keyframes asTombe{ to{ transform: translateY(24px) rotate(18deg); opacity:0; } }
.as-drapeau{ position:absolute; left:50%; top:-12px; width:38px; height:54px; margin-left:-6px; z-index:4; opacity:0; }
.as-drapeau svg{ width:100%; height:100%; overflow:visible; }
.as-onde{ position:absolute; left:50%; top:42%; width:20px; height:20px; margin:-10px 0 0 -10px; border-radius:50%; border:2px solid var(--c-legendaire); opacity:0; pointer-events:none; }
.as-jauge{ position:relative; width:min(330px, 100%); margin:0 auto; }
.as-cadran{ position:relative; height:15px; border-radius:999px; overflow:hidden; background: rgba(240,86,106,.35); border:1px solid rgba(255,255,255,.18); }
.as-zone{ position:absolute; left:0; top:0; bottom:0; background: linear-gradient(90deg, rgba(43,212,139,.75), rgba(43,212,139,.45)); }
.as-aiguille{ position:absolute; top:-7px; left:0; width:3px; height:29px; margin-left:-1.5px; background:#fff; border-radius:2px; box-shadow:0 0 10px rgba(255,255,255,.9); }
.as-jleg{ display:flex; justify-content:space-between; font-size:.74rem; color: var(--brume); margin-top:8px; }
.as-jleg b{ color:#2BD48B; } .as-jleg b.blanc{ color:#fff; }
.fenetre .as-verdict{ position:relative; margin:24px 0 8px; min-height:1.1em; font-family: var(--titre); font-weight:900; font-size:clamp(1.9rem, 8vw, 2.6rem); line-height:1; opacity:0; }
.as-verdict.ok{ color:#2BD48B; text-shadow:0 0 22px rgba(43,212,139,.5); }
.as-verdict.ko{ color:#F0566A; text-shadow:0 0 22px rgba(240,86,106,.45); }
.as-verdict.conq{ color: var(--c-legendaire); text-shadow:0 0 28px rgba(240,180,41,.65); }
.as-detail{ position:relative; margin:0 0 14px; min-height:1.3em; color: var(--brume); font-size:.86rem; line-height:1.45; }
.as-petit{ display:block; font-size:.74rem; opacity:.85; margin-top:4px; }
.as-serie{ display:inline-flex; gap:5px; vertical-align:middle; margin-left:6px; }
.as-serie i{ width:10px; height:10px; border-radius:50%; border:1.5px solid #2BD48B; }
.as-serie i.plein{ background:#2BD48B; }
.as-mon{ display:flex; align-items:center; justify-content:center; gap:6px; margin-top:6px; color:#FFE7A8; }
.as-mon svg{ width:16px; height:16px; color: var(--c-legendaire); }
.as-actions{ position:relative; display:flex; gap:10px; justify-content:center; opacity:0; }
.as-actions .open-btn{ flex:1; max-width:220px; }
/* le bandeau des grandes conquetes, chez tous les joueurs connectes */
.grande-conquete{ position:fixed; left:50%; top:calc(12px + env(safe-area-inset-top, 0px)); z-index:80; transform:translate(-50%, -160%);
  width:min(520px, calc(100% - 24px)); display:flex; align-items:center; gap:12px; padding:10px 16px; border-radius:14px; cursor:pointer;
  background: linear-gradient(90deg, #3d3519, #13284A 45%); border:1px solid rgba(240,180,41,.65); color:#fff;
  box-shadow:0 14px 40px rgba(0,0,0,.5), 0 0 30px rgba(240,180,41,.25); transition: transform .45s cubic-bezier(.2,.8,.3,1.15); }
.grande-conquete.visible{ transform:translate(-50%, 0); }
.gc-ico{ font-size:1.5rem; }
.gc-tx b{ display:block; font-family: var(--titre); font-weight:800; font-size:1.15rem; }
.gc-tx b em{ font-style:normal; color: var(--c-legendaire); }
.gc-tx small{ display:block; font-size:.76rem; color: var(--brume); }
@media (prefers-reduced-motion: reduce){ .grande-conquete{ transition:none; } .as-pastilles i.tombe{ animation:none; opacity:0; } }
'''
ecrire('style.css', css)
print(u'patch86 : OK')
