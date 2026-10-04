# -*- coding: utf-8 -*-
u"""
patch66 — La Commune du jour : une commune mystere par jour, la meme pour
tout le monde, six essais pour la trouver.

POURQUOI
  Donner une raison de revenir chaque jour qui ne passe ni par les points
  ni par les paquets. Maquette jouable validee par Natael le 4 octobre,
  puis l'emplacement dans le jeu (apercu « parfait »).

CE QUE LE JOUEUR VOIT
  - Tirage : une carte compacte au-dessus des paquets. « Jouer » tant que
    la partie du jour n'est pas faite ; ensuite « Trouvee en 3 essais »,
    la serie de jours et combien l'ont trouvee, en vert et discret.
  - Un onglet « Commune du jour » : dans la colonne sur ordinateur, en
    tete du menu Plus sur telephone, avec une pastille tant qu'on n'a pas
    joue (repetee sur le bouton Plus).
  - L'ecran du jeu : la silhouette, cinq indices qui s'ouvrent un par un
    (population, region, habitants, departement, anecdote), la saisie
    avec suggestions, la carte de France avec les essais, et a la fin le
    resultat a copier pour Discord.
  - Lien direct : terrafront.fr/?onglet=cdj

D'OU VIENNENT LES DONNEES
  - Tout passe par deux fonctions serveur (fichier cdj-1-fonctions.sql) :
    cdj_partie() et cdj_essayer(code). La reponse ne quitte jamais le
    serveur avant la fin de la partie ; les indices arrivent un par un.
  - Les suggestions viennent de data/noms-communes.json (nom,
    departement, code : 1 Mo, 290 Ko compresses), servi par GitHub Pages et
    charge seulement a l'ouverture de l'onglet.
  - La carte reutilise le contour de France deja charge par le jeu.

SI LE SQL N'EST PAS ENCORE PASSE
  La carte du Tirage reste cachee et l'onglet affiche « pas disponible ».
  Rien d'autre ne change.

CE QUI NE CHANGE PAS
  Aucun gain : ni points, ni paquets, ni cartes. Le reste du jeu.
"""
import io, os, json

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
#  data/noms-communes.json : la liste des suggestions
# =========================================================================
communes = json.loads(lire('data/communes.json'))
vus = set()
noms = []
for r in communes:
    if r[6] in vus:
        continue
    vus.add(r[6])
    noms.append([r[0], r[1], r[6]])
ecrire('data/noms-communes.json', json.dumps(noms, ensure_ascii=False, separators=(',', ':')))


# =========================================================================
#  index.html
# =========================================================================
html = lire('index.html')

# l'onglet, juste avant Monuments : dans la colonne sur ordinateur, et en
# tete du menu Plus sur telephone (le menu suit l'ordre de la page)
html = rempl(html,
u"""      <div class="tab" data-tab="monuments">""",
u"""      <div class="tab" data-tab="cdj">
        <div class="icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.6"/></svg>
        </div>
        Commune du jour
        <span class="tab-badge" id="cdjBadge" hidden></span>
      </div>

      <div class="tab" data-tab="monuments">""", 'onglet cdj')

# la carte du Tirage
html = rempl(html,
u"""      <div class="puces" id="packStatus"><span class="puce">Chargement…</span></div>""",
u"""      <button type="button" class="cdj-carte" id="cdjCarte" hidden></button>
      <div class="puces" id="packStatus"><span class="puce">Chargement…</span></div>""", 'carte tirage')

# le panneau
html = rempl(html,
u"""    <section class="tab-panel" id="panel-collection">""",
u"""    <section class="tab-panel" id="panel-cdj">
      <h1>Commune du jour <span class="cdj-numero" id="cdjNumero"></span></h1>
      <div class="sub">La même commune pour tout le monde, six essais pour la trouver. Chaque erreur dévoile un indice, et chaque essai dit à quelle distance tu es et dans quelle direction chercher. Nouvelle commune chaque jour à minuit.</div>
      <p class="cdj-indispo" id="cdjIndispo" hidden>La commune du jour n'est pas disponible pour le moment.</p>
      <div class="cdj-grille" id="cdjJeu" hidden>
        <div class="cdj-bloc">
          <div class="cdj-tete">
            <svg class="cdj-sil" id="cdjSil" viewBox="0 0 100 100" role="img" aria-label="Silhouette de la commune mystère"></svg>
            <div><small>Commune mystère</small><b>Quelle est cette commune&nbsp;?</b></div>
          </div>
          <ul class="cdj-indices" id="cdjIndices"></ul>
          <div class="cdj-saisie" id="cdjSaisie">
            <label for="cdjChamp">Ta proposition</label>
            <div class="cdj-ligne">
              <input id="cdjChamp" type="text" autocomplete="off" spellcheck="false" placeholder="Tape le nom d'une commune…" aria-autocomplete="list" aria-controls="cdjListe">
              <button type="button" id="cdjValider" disabled>Valider</button>
            </div>
            <ul class="cdj-liste" id="cdjListe" role="listbox" hidden></ul>
          </div>
          <div class="cdj-fin" id="cdjFin" hidden></div>
        </div>
        <div class="cdj-bloc">
          <svg class="cdj-france" id="cdjFrance" role="img" aria-label="Carte de France avec tes essais"></svg>
          <div class="cdj-legende">
            <span><i class="trouvee"></i>trouvée</span>
            <span><i class="proche"></i>moins de 50 km</span>
            <span><i class="moyen"></i>moins de 150 km</span>
            <span><i class="loin"></i>plus loin</span>
          </div>
          <ol class="cdj-essais" id="cdjEssais" aria-label="Tes essais"></ol>
        </div>
      </div>
    </section>

    <section class="tab-panel" id="panel-collection">""", 'panneau cdj')

ecrire('index.html', html)


# =========================================================================
#  app.js
# =========================================================================
js = lire('app.js')

# au demarrage : la carte du Tirage et la pastille
js = rempl(js,
u"""  chargerSaison();
  verifierVersion();""",
u"""  chargerSaison();
  chargerCdj();
  verifierVersion();""", 'demarrage')

# a l'ouverture de l'onglet
js = rempl(js,
u"""    if(tab.dataset.tab === 'monuments') loadMonuments();""",
u"""    if(tab.dataset.tab === 'monuments') loadMonuments();
    if(tab.dataset.tab === 'cdj') ouvrirCdj();""", 'ouverture onglet')

# lien direct ?onglet=cdj
js = rempl(js,
u"""const ONGLETS_CONNUS = ['tirage', 'collection', 'territoire', 'bourse', 'combat', 'defense', 'regles'];""",
u"""const ONGLETS_CONNUS = ['tirage', 'collection', 'territoire', 'bourse', 'combat', 'defense', 'regles', 'cdj'];""", 'liens')

# la pastille du bouton Plus : Combat (s'il est dans le menu) ou la commune du jour
js = rempl(js,
u"""  const dansLeMenu = surTelephone() && ONGLETS_MENU.includes('combat');
  cible.hidden = !dansLeMenu || source.hidden;
  cible.textContent = source.textContent;""",
u"""  const dansLeMenu = surTelephone() && ONGLETS_MENU.includes('combat');
  const cdj = document.getElementById('cdjBadge');
  const cdjAJouer = surTelephone() && cdj && !cdj.hidden;
  if(dansLeMenu && !source.hidden){
    cible.hidden = false;
    cible.textContent = source.textContent;
  } else {
    cible.hidden = !cdjAJouer;
    cible.textContent = cdjAJouer ? '1' : '';
  }""", 'badge plus')

js = rempl(js,
u"""
initAuth();
""",
u"""
// ---------- Commune du jour ----------
// Tout ce qui compte se decide sur le serveur (cdj_partie, cdj_essayer) :
// le navigateur n'a jamais la reponse avant la fin. Ici, on affiche.
let cdjEtat = null;
let cdjNoms = null, cdjNomsEnCours = null;
let cdjChoix = null, cdjResultats = [], cdjSurligne = -1, cdjMinuteur = null;
let cdjEnvoi = false, cdjDernierIndice = null;   // null : premier affichage, rien a souligner
const CDJ_LIBELLES = { population: 'Population', region: 'Région', gentile: 'Habitants', departement: 'Département', anecdote: 'Anecdote' };
const CDJ_FLECHES = ['⬆️', '↗️', '➡️', '↘️', '⬇️', '↙️', '⬅️', '↖️'];
const CDJ_DIRECTIONS = ['vers le nord', 'vers le nord-est', 'vers l’est', 'vers le sud-est', 'vers le sud', 'vers le sud-ouest', 'vers l’ouest', 'vers le nord-ouest'];
const cdjCouleur = (km) => km === 0 ? 'trouvee' : km < 50 ? 'proche' : km < 150 ? 'moyen' : 'loin';
const cdjCarre = (km) => km === 0 ? '🟩' : km < 50 ? '🟨' : km < 150 ? '🟧' : '🟥';
const cdjCle = (s) => sansAccents(s).replace(/[-'’\\s]+/g, ' ').trim();
const cdjJourParis = () => new Date().toLocaleDateString('en-CA', { timeZone: 'Europe/Paris' });

async function chargerCdj(){
  const { data, error } = await sb.rpc('cdj_partie');
  if(error){
    console.warn('TERRAFRONT commune du jour indisponible', error);
    cdjEtat = null;
  } else {
    cdjEtat = data;
  }
  renderCdjCarte();
  renderCdj();
}

function ouvrirCdj(){
  // a minuit la partie change : on la redemande si le jour n'est plus le meme
  if(!cdjEtat || cdjEtat.jour !== cdjJourParis()) chargerCdj();
  else renderCdj();
  cdjChargerNoms();
}

document.addEventListener('visibilitychange', () => {
  if(!document.hidden && cdjEtat && cdjEtat.jour !== cdjJourParis()) chargerCdj();
});

function cdjSilhouette(points){
  return (points || []).map(r => 'M' + r.map(p => p[0] + ',' + p[1]).join('L') + 'Z').join('');
}

function renderCdjCarte(){
  const carte = document.getElementById('cdjCarte');
  const badge = document.getElementById('cdjBadge');
  if(!carte) return;
  const e = cdjEtat;
  if(!e){
    carte.hidden = true;
    if(badge) badge.hidden = true;
    majBadgePlus();
    return;
  }
  const serie = e.serie > 0 ? `série de ${e.serie} jour${e.serie > 1 ? 's' : ''}` : '';
  const nb = e.essais.length;
  let titre, texte, bouton;
  if(e.fini){
    titre = e.trouve ? `Trouvée en ${nb} essai${nb > 1 ? 's' : ''}` : 'Pas trouvée aujourd’hui';
    const qui = e.trouves > 0 ? `${e.trouves} l’${e.trouves > 1 ? 'ont' : 'a'} trouvée` : '';
    texte = [serie && serie.charAt(0).toUpperCase() + serie.slice(1), qui].filter(Boolean).join(' · ') || 'Nouvelle commune à minuit';
    bouton = 'Revoir';
  } else if(nb > 0){
    titre = 'Commune du jour';
    texte = `Partie en cours · ${nb} essai${nb > 1 ? 's' : ''} sur 6`;
    bouton = 'Continuer';
  } else {
    titre = 'Commune du jour';
    texte = ['6 essais', serie].filter(Boolean).join(' · ');
    bouton = 'Jouer';
  }
  carte.className = 'cdj-carte' + (e.fini ? ' faite' : '');
  carte.innerHTML = `<svg viewBox="0 0 100 100" aria-hidden="true"><path d="${cdjSilhouette(e.silhouette)}"/></svg>
    <span class="cdj-carte-txt"><b>${titre}</b><span>${texte}</span></span>
    <span class="cdj-carte-btn">${bouton}</span>`;
  carte.hidden = false;
  if(badge){
    badge.hidden = e.fini;
    badge.textContent = '1';
  }
  majBadgePlus();
}

document.getElementById('cdjCarte').addEventListener('click', () => {
  const tab = document.querySelector('.tab[data-tab="cdj"]');
  if(tab) tab.click();
});

// ----- le panneau -----
let cdjBornes = null;
const CDJ_K = Math.cos(46.5 * Math.PI / 180);
function cdjPx(lon, lat){
  return [(lon * CDJ_K - cdjBornes.x0).toFixed(3), (-lat - cdjBornes.y0).toFixed(3)];
}

function renderCdjFrance(){
  const svg = document.getElementById('cdjFrance');
  if(!svg || !FRANCE_OUTLINE || !cdjEtat) return;
  if(!cdjBornes){
    let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    for(const anneau of FRANCE_OUTLINE) for(const [lo, la] of anneau){
      x0 = Math.min(x0, lo * CDJ_K); x1 = Math.max(x1, lo * CDJ_K);
      y0 = Math.min(y0, -la); y1 = Math.max(y1, -la);
    }
    const m = 0.3;
    cdjBornes = { x0: x0 - m, y0: y0 - m, w: x1 - x0 + 2 * m, h: y1 - y0 + 2 * m };
  }
  svg.setAttribute('viewBox', `0 0 ${cdjBornes.w.toFixed(2)} ${cdjBornes.h.toFixed(2)}`);
  const rayon = cdjBornes.w / 90;
  let h = '';
  for(const anneau of FRANCE_OUTLINE){
    h += `<path class="cdj-fr" d="M${anneau.map(([lo, la]) => cdjPx(lo, la).join(',')).join('L')}Z"/>`;
  }
  const rep = cdjEtat.reponse;
  if(rep){
    const [cx, cy] = cdjPx(+rep.lon, +rep.lat);
    for(const e of cdjEtat.essais){
      if(e.km === 0) continue;
      const [x, y] = cdjPx(+e.lon, +e.lat);
      h += `<line class="cdj-trait" x1="${x}" y1="${y}" x2="${cx}" y2="${cy}" stroke-width="${rayon / 3}" stroke-dasharray="${rayon / 2} ${rayon / 2}"/>`;
    }
  }
  cdjEtat.essais.forEach((e, n) => {
    const [x, y] = cdjPx(+e.lon, +e.lat);
    h += `<circle class="cdj-point ${cdjCouleur(e.km)}" cx="${x}" cy="${y}" r="${rayon}" stroke-width="${rayon / 4}"/>`;
    h += `<text class="cdj-num" x="${x}" y="${(+y - rayon * 1.6).toFixed(3)}" font-size="${rayon * 1.9}">${n + 1}</text>`;
  });
  if(rep){
    const [x, y] = cdjPx(+rep.lon, +rep.lat);
    h += `<circle class="cdj-cible" cx="${x}" cy="${y}" r="${rayon * 2.4}" stroke-width="${rayon / 2.5}"/>`;
    h += `<circle class="cdj-cible-c" cx="${x}" cy="${y}" r="${rayon * 0.9}"/>`;
  }
  svg.innerHTML = h;
}

function renderCdj(){
  const jeu = document.getElementById('cdjJeu');
  const indispo = document.getElementById('cdjIndispo');
  if(!jeu) return;
  const e = cdjEtat;
  jeu.hidden = !e;
  indispo.hidden = !!e;
  if(!e) return;

  document.getElementById('cdjNumero').textContent = '#' + e.numero;
  document.getElementById('cdjSil').innerHTML = `<path d="${cdjSilhouette(e.silhouette)}"/>`;

  // les indices : le serveur n'envoie que ceux deja gagnes
  const ouverts = e.indices.filter(i => i.valeur !== null).length;
  document.getElementById('cdjIndices').innerHTML = e.indices.map((i, n) => {
    const ouvert = i.valeur !== null;
    const neuf = ouvert && cdjDernierIndice !== null && n === ouverts - 1 && n > cdjDernierIndice && !e.fini;
    let valeur = i.valeur;
    if(ouvert && i.cle === 'departement') valeur = `${DEPT_NAMES[i.valeur] || i.valeur} (${i.valeur})`;
    if(ouvert && i.cle === 'gentile') valeur = 'les ' + i.valeur;
    return `<li class="${ouvert ? '' : 'ferme'}${neuf ? ' neuf' : ''}"><span class="cdj-lab">${CDJ_LIBELLES[i.cle] || i.cle}</span>
      <span class="cdj-val">${ouvert ? echapperTexte(valeur) : `après ${n + 1} essai${n ? 's' : ''}`}</span></li>`;
  }).join('');
  cdjDernierIndice = ouverts - 1;

  // les essais
  let h = '';
  for(let n = 0; n < 6; n++){
    const x = e.essais[n];
    if(!x){ h += '<li class="vide" aria-hidden="true"></li>'; continue; }
    const dist = x.km === 0 ? 'trouvée' : x.km.toLocaleString('fr-FR') + ' km';
    const dir = x.km === 0 ? '🎯' : CDJ_FLECHES[x.cap];
    h += `<li><span class="cdj-pastille ${cdjCouleur(x.km)}"></span>
      <span class="cdj-nom">${echapperTexte(x.nom)} <small>(${echapperTexte(x.dept)})</small></span>
      <span class="cdj-dist">${dist}</span>
      <span class="cdj-dir" title="${x.km === 0 ? '' : CDJ_DIRECTIONS[x.cap]}" aria-label="${x.km === 0 ? 'trouvée' : CDJ_DIRECTIONS[x.cap]}">${dir}</span></li>`;
  }
  document.getElementById('cdjEssais').innerHTML = h;

  document.getElementById('cdjSaisie').hidden = e.fini;
  renderCdjFin();
  renderCdjFrance();
}

function cdjTextePartage(){
  const e = cdjEtat;
  const ligne = e.essais.map(x => cdjCarre(x.km) + (x.km === 0 ? '🎯' : CDJ_FLECHES[x.cap])).join(' ');
  return `TerraFront · Commune du jour #${e.numero}\\n${e.trouve ? e.essais.length : 'X'}/6  ${ligne}\\nterrafront.fr`;
}

function renderCdjFin(){
  const z = document.getElementById('cdjFin');
  const e = cdjEtat;
  z.hidden = !e.fini;
  if(!e.fini) return;
  const r = e.reponse;
  const nb = e.essais.length;
  const qui = e.joueurs > 0
    ? `${e.joueurs} joueur${e.joueurs > 1 ? 's ont' : ' a'} joué aujourd’hui, ${e.trouves} l’${e.trouves > 1 ? 'ont' : 'a'} trouvée.`
    : '';
  const serie = e.serie > 0 ? ` Série en cours : <b>${e.serie} jour${e.serie > 1 ? 's' : ''}</b>.` : '';
  z.innerHTML = `<h2 class="${e.trouve ? 'gagne' : ''}">${e.trouve ? `Trouvée en ${nb}` : 'Pas trouvée'}</h2>
    <p>C’était <b>${echapperTexte(r.nom)}</b>, ${echapperTexte(DEPT_NAMES[r.dept] || r.dept)}, ${Number(r.pop).toLocaleString('fr-FR')} habitants.</p>
    <p>${qui}${serie} Nouvelle commune à minuit.</p>
    <pre class="cdj-partage" id="cdjPartage">${echapperTexte(cdjTextePartage())}</pre>
    <button type="button" class="cdj-copier" id="cdjCopier">Copier le résultat pour Discord</button>`;
  document.getElementById('cdjCopier').onclick = async (ev) => {
    const b = ev.currentTarget;
    try{
      await navigator.clipboard.writeText(cdjTextePartage());
      b.textContent = 'Copié';
    } catch(err){
      const sel = getSelection(), plage = document.createRange();
      plage.selectNodeContents(document.getElementById('cdjPartage'));
      sel.removeAllRanges(); sel.addRange(plage);
      b.textContent = 'Sélectionné : copie-le';
    }
  };
}

// ----- la saisie -----
function cdjChargerNoms(){
  if(cdjNoms || cdjNomsEnCours) return cdjNomsEnCours;
  const champ = document.getElementById('cdjChamp');
  champ.disabled = true;
  champ.placeholder = 'Chargement des communes…';
  cdjNomsEnCours = fetch('data/noms-communes.json', { cache: 'force-cache' })
    .then(r => r.json())
    .then(liste => {
      cdjNoms = liste.map(([nom, dept, code]) => ({ nom, dept, code, cle: cdjCle(nom) }));
      champ.disabled = false;
      champ.placeholder = 'Tape le nom d’une commune…';
    })
    .catch(err => {
      console.warn('TERRAFRONT liste des communes indisponible', err);
      cdjNomsEnCours = null;
      champ.disabled = false;
      champ.placeholder = 'Liste indisponible, recharge la page';
    });
  return cdjNomsEnCours;
}

function cdjChercher(q){
  const k = cdjCle(q);
  if(!cdjNoms || k.length < 2) return [];
  const debut = [], dedans = [];
  for(const c of cdjNoms){
    if(c.cle.startsWith(k)) debut.push(c);
    else if(dedans.length < 40 && c.cle.includes(k)) dedans.push(c);
    if(debut.length > 200) break;
  }
  debut.sort((a, b) => a.cle.length - b.cle.length || a.nom.localeCompare(b.nom, 'fr'));
  return [...debut, ...dedans].slice(0, 8);
}

function cdjMajListe(){
  const champ = document.getElementById('cdjChamp');
  const liste = document.getElementById('cdjListe');
  cdjResultats = cdjChercher(champ.value);
  cdjSurligne = cdjResultats.length ? 0 : -1;
  liste.hidden = !cdjResultats.length;
  liste.innerHTML = cdjResultats.map((c, n) =>
    `<li role="option" data-n="${n}" aria-selected="${n === cdjSurligne}"><span>${echapperTexte(c.nom)}</span><small>${echapperTexte(DEPT_NAMES[c.dept] || '')} (${echapperTexte(c.dept)})</small></li>`).join('');
}

function cdjMajBouton(){
  document.getElementById('cdjValider').disabled = !cdjChoix || cdjEnvoi;
}

function cdjChoisir(c){
  cdjChoix = c;
  document.getElementById('cdjChamp').value = `${c.nom} (${c.dept})`;
  document.getElementById('cdjListe').hidden = true;
  cdjMajBouton();
  document.getElementById('cdjValider').focus();
}

async function cdjValider(){
  if(!cdjChoix || cdjEnvoi || !cdjEtat || cdjEtat.fini) return;
  const champ = document.getElementById('cdjChamp');
  if(cdjEtat.essais.some(x => x.code === cdjChoix.code)){
    notifier({ type: 'info', titre: 'Déjà proposée', texte: 'Essaie une autre commune.' });
    return;
  }
  cdjEnvoi = true;
  cdjMajBouton();
  try{
    const { data, error } = await sb.rpc('cdj_essayer', { p_code: cdjChoix.code });
    if(error) throw error;
    cdjEtat = data;
    cdjChoix = null;
    champ.value = '';
    renderCdjCarte();
    renderCdj();
    if(!cdjEtat.fini) champ.focus();
  } catch(err){
    notifier({ type: 'erreur', titre: 'Essai refusé', texte: messageLisible(err.message) });
    // la partie a pu changer ailleurs (autre appareil, minuit) : on la relit
    chargerCdj();
  } finally {
    cdjEnvoi = false;
    cdjMajBouton();
  }
}

(function brancherCdj(){
  const champ = document.getElementById('cdjChamp');
  const liste = document.getElementById('cdjListe');
  champ.addEventListener('input', () => { clearTimeout(cdjMinuteur); cdjChoix = null; cdjMajBouton(); cdjMajListe(); });
  champ.addEventListener('focus', () => clearTimeout(cdjMinuteur));
  champ.addEventListener('blur', () => { cdjMinuteur = setTimeout(() => { liste.hidden = true; }, 150); });
  champ.addEventListener('keydown', (e) => {
    if(liste.hidden){
      if(e.key === 'Enter' && cdjChoix){ e.preventDefault(); cdjValider(); }
      return;
    }
    if(e.key === 'ArrowDown' || e.key === 'ArrowUp'){
      e.preventDefault();
      cdjSurligne = (cdjSurligne + (e.key === 'ArrowDown' ? 1 : -1) + cdjResultats.length) % cdjResultats.length;
      liste.querySelectorAll('li').forEach((li, n) => li.setAttribute('aria-selected', n === cdjSurligne));
    } else if(e.key === 'Enter' && cdjSurligne >= 0){
      e.preventDefault();
      cdjChoisir(cdjResultats[cdjSurligne]);
    } else if(e.key === 'Escape'){
      liste.hidden = true;
    }
  });
  // mousedown plutot que click : le clic arrive apres le blur du champ
  liste.addEventListener('mousedown', (e) => {
    const li = e.target.closest('li');
    if(!li) return;
    e.preventDefault();
    cdjChoisir(cdjResultats[+li.dataset.n]);
  });
  document.getElementById('cdjValider').addEventListener('click', cdjValider);
})();

initAuth();
""", 'module cdj')

ecrire('app.js', js)


# =========================================================================
#  style.css
# =========================================================================
css = lire('style.css')
css += u"""

/* ---------- Commune du jour (patch66) ---------- */
.cdj-carte{
  box-sizing:border-box; width:100%; max-width:100%; min-width:0;
  display:flex; align-items:center; gap:12px;
  margin:12px 0 14px; padding:10px 12px; border-radius:12px;
  background:linear-gradient(100deg, rgba(240,180,41,.13), rgba(240,180,41,.03) 60%);
  border:1px solid rgba(240,180,41,.45);
  color:#fff; font:inherit; text-align:left; cursor:pointer;
}
.cdj-carte[hidden]{ display:none; }
.cdj-carte:focus-visible{ outline:2px solid #fff; outline-offset:2px; }
.cdj-carte svg{ width:46px; height:46px; flex:none; }
.cdj-carte svg path{ fill: var(--c-legendaire); }
.cdj-carte-txt{ flex:1; min-width:0; display:flex; flex-direction:column; gap:1px; }
.cdj-carte-txt b{ font-family: var(--titre); font-size:19px; font-weight:800; letter-spacing:.01em; text-transform:uppercase; line-height:1.05; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.cdj-carte-txt span{ font-size:13px; color: var(--brume); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.cdj-carte-btn{ flex:none; font-family: var(--titre); font-weight:800; font-size:17px; letter-spacing:.04em; text-transform:uppercase; background: var(--c-legendaire); color: var(--nuit); border-radius:9px; padding:8px 12px; }
.cdj-carte.faite{ background: rgba(255,255,255,.04); border-color: rgba(169,188,212,.25); }
.cdj-carte.faite svg path{ fill: var(--c-peucommun); }
.cdj-carte.faite .cdj-carte-btn{ background:transparent; color: var(--brume); border:1px solid rgba(169,188,212,.3); font-family: var(--texte); font-size:12.5px; font-weight:600; text-transform:none; letter-spacing:0; }

.cdj-numero{ color: var(--brume); }
.cdj-indispo{ color: var(--brume); }
.cdj-grille{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:18px; align-items:start; margin-top:16px; }
.cdj-grille[hidden]{ display:none; }
@media (max-width: 900px){ .cdj-grille{ grid-template-columns:minmax(0,1fr); } }
.cdj-bloc{ background: var(--nuit-2); border:1px solid rgba(169,188,212,.18); border-radius:14px; padding:16px; min-width:0; }
.cdj-tete{ display:flex; gap:16px; align-items:center; }
.cdj-sil{ width:96px; height:96px; flex:none; border-radius:12px; background:radial-gradient(circle at 50% 45%, var(--nuit-3), transparent 70%); }
.cdj-sil path{ fill: var(--c-legendaire); }
.cdj-tete small{ display:block; text-transform:uppercase; letter-spacing:.08em; font-size:11.5px; color: var(--brume); }
.cdj-tete b{ font-family: var(--titre); font-size:22px; font-weight:800; letter-spacing:.01em; line-height:1.15; }
.cdj-indices{ list-style:none; margin:14px 0 0; padding:0; display:flex; flex-direction:column; gap:6px; }
.cdj-indices li{ display:flex; gap:10px; align-items:baseline; padding:8px 10px; border-radius:9px; background:rgba(255,255,255,.03); border:1px solid transparent; font-size:14px; }
.cdj-lab{ flex:none; width:96px; font-size:11.5px; text-transform:uppercase; letter-spacing:.07em; color: var(--brume); }
.cdj-indices li.ferme .cdj-val{ color: var(--brume); opacity:.55; }
.cdj-indices li.neuf{ border-color: rgba(240,180,41,.6); animation: cdjNeuf 1.2s ease-out; }
@keyframes cdjNeuf{ from{ background: rgba(240,180,41,.22); } }
.cdj-saisie{ position:relative; margin-top:14px; }
.cdj-saisie[hidden]{ display:none; }
.cdj-saisie label{ display:block; font-size:12.5px; color: var(--brume); margin-bottom:6px; }
.cdj-ligne{ display:flex; gap:8px; }
#cdjChamp{ flex:1; min-width:0; font:inherit; font-size:16px; padding:11px 12px; border-radius:10px; border:1px solid rgba(169,188,212,.25); background: var(--nuit); color:#fff; }
#cdjChamp:focus-visible{ outline:2px solid var(--c-legendaire); outline-offset:1px; }
#cdjValider{ font-family: var(--titre); font-weight:800; font-size:18px; letter-spacing:.04em; text-transform:uppercase; padding:0 18px; border-radius:10px; border:0; background: var(--c-legendaire); color: var(--nuit); cursor:pointer; }
#cdjValider:disabled{ opacity:.4; cursor:default; }
.cdj-liste{ position:absolute; left:0; right:0; top:100%; margin-top:4px; background: var(--nuit-3); border:1px solid rgba(169,188,212,.2); border-radius:10px; list-style:none; padding:4px; z-index:20; max-height:280px; overflow:auto; box-shadow:0 14px 30px rgba(0,0,0,.45); }
.cdj-liste[hidden]{ display:none; }
.cdj-liste li{ padding:8px 10px; border-radius:7px; cursor:pointer; display:flex; justify-content:space-between; gap:10px; }
.cdj-liste li small{ color: var(--brume); white-space:nowrap; }
.cdj-liste li[aria-selected="true"], .cdj-liste li:hover{ background: rgba(255,255,255,.08); }
.cdj-fin{ display:flex; flex-direction:column; gap:10px; margin-top:18px; }
.cdj-fin[hidden]{ display:none; }
.cdj-fin h2{ font-family: var(--titre); font-weight:900; font-size:32px; text-transform:uppercase; margin:0; line-height:1; }
.cdj-fin h2.gagne{ color: var(--c-legendaire); }
.cdj-fin p{ margin:0; color: var(--brume); }
.cdj-fin p b{ color:#fff; }
.cdj-partage{ margin:0; font-family:inherit; font-size:15px; background: var(--nuit); border:1px solid rgba(169,188,212,.2); border-radius:10px; padding:10px 12px; white-space:pre-wrap; }
.cdj-copier{ align-self:flex-start; font:inherit; font-weight:600; padding:9px 14px; border-radius:9px; border:1px solid var(--c-legendaire); background:transparent; color: var(--c-legendaire); cursor:pointer; }
.cdj-france{ width:100%; height:auto; display:block; }
.cdj-fr{ fill: var(--nuit-3); stroke: rgba(169,188,212,.45); stroke-width:.6; vector-effect:non-scaling-stroke; }
.cdj-trait{ stroke: var(--brume); stroke-opacity:.35; }
.cdj-point{ stroke: var(--nuit); }
.cdj-num{ fill:#fff; font-weight:600; text-anchor:middle; }
.cdj-cible{ fill:none; stroke: var(--c-legendaire); }
.cdj-cible-c{ fill: var(--c-legendaire); }
.cdj-point.trouvee, .cdj-pastille.trouvee, .cdj-legende i.trouvee{ fill:#22A06B; background:#22A06B; }
.cdj-point.proche, .cdj-pastille.proche, .cdj-legende i.proche{ fill:#E8C547; background:#E8C547; }
.cdj-point.moyen, .cdj-pastille.moyen, .cdj-legende i.moyen{ fill:#E8873A; background:#E8873A; }
.cdj-point.loin, .cdj-pastille.loin, .cdj-legende i.loin{ fill:#E5484D; background:#E5484D; }
.cdj-legende{ display:flex; flex-wrap:wrap; gap:6px 14px; font-size:12px; color: var(--brume); margin-top:8px; }
.cdj-legende i{ display:inline-block; width:10px; height:10px; border-radius:3px; margin-right:5px; vertical-align:-1px; }
.cdj-essais{ list-style:none; margin:14px 0 0; padding:0; display:flex; flex-direction:column; gap:6px; }
.cdj-essais li{ display:grid; grid-template-columns:20px minmax(0,1fr) auto 26px; gap:10px; align-items:center; padding:8px 10px; border-radius:9px; background:rgba(255,255,255,.04); font-variant-numeric:tabular-nums; }
.cdj-essais li.vide{ background:transparent; border:1px dashed rgba(169,188,212,.18); height:38px; }
.cdj-pastille{ width:14px; height:14px; border-radius:4px; }
.cdj-nom{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.cdj-nom small{ color: var(--brume); }
.cdj-dist{ font-weight:600; }
.cdj-dir{ font-size:18px; text-align:center; line-height:1; }
@media (prefers-reduced-motion: reduce){ .cdj-indices li.neuf{ animation:none; } }
"""
ecrire('style.css', css)

print(u'patch66 applique : index.html, app.js, style.css, data/noms-communes.json')
