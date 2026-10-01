# -*- coding: utf-8 -*-
u"""
patch53 — Un onglet Monuments, en album.

CE QUE C'EST
  239 lieux que tout le monde connait, un par commune. Qui possede la
  commune possede le monument ; qui la lui prend le prend avec.

POURQUOI CA CHANGE QUELQUE CHOSE
  Aujourd'hui une commune vaut par sa population. Deux communes de 4 000
  habitants sont interchangeables, donc aucune n'est desirable en
  particulier. Avec les monuments, Millau vaut parce qu'il y a le viaduc —
  la premiere raison d'attaquer une commune PRECISE.

  Et ca ne sort aucune carte du pot : c'est une couche posee sur ce qui
  existe deja, pas une economie de plus.

LA FORME : UN ALBUM, PAS UNE LISTE
  Les 239 cartes sont toutes la, tout le temps. Celles qu'on possede sont
  en couleur, les autres en gris. On voit ses trous d'un coup d'oeil, sans
  rien lire — c'est ce qui donne envie d'aller les chercher. Une liste de
  lignes aurait dit la meme chose en moins fort.

  Sous chaque carte grise, le nom de celui qui l'a. Savoir que le viaduc de
  Millau est chez Maroli vaut toutes les explications.

CE QUE JE N'AI PAS FAIT
  Aucune recompense en points. Les departements se terminent et paient ;
  les monuments, non. Deux raisons : un monument se perd avec sa commune,
  donc une recompense serait a reprendre, ce qui est injouable ; et le pot
  n'a pas besoin d'une source de points de plus — il a besoin de raisons de
  se battre. La recompense, c'est ton pseudo affiche sous le viaduc.

  Je n'ai pas non plus remplace la photo des cartes de communes par celle du
  monument. L'album leur donne deja leur propre place, et echanger les deux
  images obligerait a echanger aussi l'auteur et la licence affiches —
  crediter la mauvaise personne n'est pas une negligence rattrapable.

CE QUI SE PASSE QUAND ON CLIQUE UNE CARTE
  — a toi : sa fiche s'ouvre
  — chez un autre joueur : l'onglet Combat s'ouvre, la recherche deja
    remplie avec le nom de la commune
  — libre : rien. Une commune libre ne s'attaque pas, elle sort d'un paquet
    ou d'un contrat ; faire croire le contraire serait un mensonge
    d'interface.

AILLEURS DANS LE JEU
  Un petit badge en bas a gauche de la vignette d'une commune a monument, et
  un bandeau sur sa fiche. C'est ce qui relie l'album au reste : sans ca,
  on ne saurait pas, en ouvrant un paquet, qu'on vient de gagner le viaduc.

  Et dans le journal : « Maroli a conquis Millau sur toi » devient la meme
  phrase suivie du viaduc. C'est la ligne qui donne envie d'aller le
  reprendre, et elle est publique — tout le monde voit le monument changer
  de mains.

  Cette derniere partie demande journal-code.sql, qui ajoute le code INSEE a
  ce que renvoie le journal. Sans lui, les lignes restent telles quelles :
  rapprocher le monument du nom de la commune serait faux, il y a seize
  Saint-Martin.

DEUX CHARGEMENTS, PAS UN
  Le badge n'a besoin que des noms : deux colonnes, 239 lignes, demandees en
  arriere-plan pendant que la collection s'affiche. L'album, lui, a besoin
  des proprietaires : il demande le catalogue complet a l'ouverture de
  l'onglet, et le redemande s'il a plus d'une minute.

  Si monuments.sql n'a pas encore ete passe, les deux requetes echouent
  proprement : pas de badge, album vide avec un message, et le reste du jeu
  ne voit pas la difference.
"""
import io, os

BASE = os.path.dirname(os.path.abspath(__file__))

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


ICONE = (u'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"'
         u' stroke-linecap="round" stroke-linejoin="round">'
         u'<path d="M3 20.5h18M4.5 20.5V10L12 4.5 19.5 10v10.5"/>'
         u'<path d="M9.5 20.5v-5.5h5v5.5"/></svg>')


# ===========================================================================
#  index.html — l'onglet et son panneau
# ===========================================================================
html = lire('index.html')

# --- le bouton d'onglet, juste apres Succes --------------------------------
html = rempl(html,
u"""        Succès
      </div>

      <button class="tab tab-plus" id="btnPlus\"""",
u"""        Succès
      </div>

      <div class="tab" data-tab="monuments">
        <div class="icon">
          %s
        </div>
        Monuments
      </div>

      <button class="tab tab-plus" id="btnPlus\"""" % ICONE,
u'bouton de l\'onglet Monuments')

# --- le panneau, juste apres celui de Succes -------------------------------
html = rempl(html,
u"""    <section class="tab-panel" id="panel-profil">""",
u"""    <section class="tab-panel" id="panel-monuments">
      <h1>Monuments <span class="mon-compteur" id="monCompteur">—</span></h1>
      <div class="sub">Un lieu connu par commune : qui possède la commune possède son monument, et le perd avec elle. Les cartes en gris sont celles que tu n'as pas, avec le nom de celui qui les a.</div>
      <div class="coll-filtres" id="monFiltres"></div>
      <input type="text" id="monRech" class="bourse-search" placeholder="Rechercher un monument, une commune, un département…">
      <div class="mon-grille" id="monGrille"><p class="collection-empty">Chargement…</p></div>
    </section>

    <section class="tab-panel" id="panel-profil">""",
u'panneau Monuments')

ecrire('index.html', html)


# ===========================================================================
#  app.js
# ===========================================================================
js = lire('app.js')

js = rempl(js,
u"""const ONGLETS_MENU = ['territoire', 'communaute', 'bourse', 'echange', 'contrat', 'succes', 'profil'];""",
u"""const ONGLETS_MENU = ['territoire', 'communaute', 'bourse', 'echange', 'contrat', 'succes', 'monuments', 'profil'];""",
u'Monuments dans le menu Plus')

js = rempl(js,
u"""    if(tab.dataset.tab === 'succes') loadSucces();""",
u"""    if(tab.dataset.tab === 'succes') loadSucces();
    if(tab.dataset.tab === 'monuments') loadMonuments();""",
u'chargement a l\'ouverture de l\'onglet')

# --- le bloc complet --------------------------------------------------------
js = rempl(js,
u"""// ---------- Succes : completion par departement ----------""",
u"""// ---------- Les monuments ----------
// Un lieu connu par commune : qui possede la commune possede le monument.
// L'album montre les 239, celles qu'on n'a pas en gris. Voir le trou est ce
// qui donne envie d'aller le combler ; un album qui ne montrerait que ses
// propres cartes n'apprendrait rien a personne.

const ICONE_MONUMENT = '%s';

// Les noms seuls, pour le badge des vignettes et de la fiche : deux colonnes,
// table en lecture libre. Une seule requete par session, en arriere-plan.
let monumentsNoms = new Map();
let monumentsNomsPromesse = null;
function chargerNomsMonuments(){
  if(monumentsNomsPromesse) return monumentsNomsPromesse;
  monumentsNomsPromesse = Promise.resolve(sb.from('monuments').select('commune_code, nom'))
    .then(({ data, error }) => {
      // monuments.sql pas encore passe : on repart avec une liste vide et le
      // jeu se comporte exactement comme avant
      if(!error) monumentsNoms = new Map((data || []).map(m => [m.commune_code, m.nom]));
      return monumentsNoms;
    })
    .catch(() => monumentsNoms);
  return monumentsNomsPromesse;
}

// Le catalogue complet : il porte les proprietaires, donc il vieillit.
let monuments = [];
let monumentsLe = 0;
let monumentFiltre = 'tous';
const MONUMENTS_FRAIS = 60000;          // au-dela, on redemande

async function loadMonuments(){
  const grille = document.getElementById('monGrille');
  if(!grille) return;
  if(monuments.length && Date.now() - monumentsLe < MONUMENTS_FRAIS){
    renderMonuments(); return;
  }
  const { data, error } = await sb.rpc('monuments_catalogue');
  if(error){
    console.error(error);
    grille.innerHTML = '<p class="collection-empty">L\\'album des monuments n\\'est pas encore disponible.</p>';
    return;
  }
  monuments = data || [];
  monumentsLe = Date.now();
  renderMonuments();
}

function carteMonument(m){
  const u = urlPhoto(m.photo);
  const dept = m.departement || '';
  const etat = m.a_moi ? 'amoi' : (m.libre ? 'libre' : 'pris');
  const qui = m.a_moi ? 'à toi'
            : (m.libre ? 'personne ne l\\'a' : echapperTexte(m.proprietaire || 'un joueur'));
  // une commune libre ne s'attaque pas : elle sort d'un paquet ou d'un
  // contrat. Pas d'action, donc pas d'apparence cliquable.
  const action = m.a_moi ? 'fiche' : (m.libre ? '' : 'attaquer');
  return `
    <article class="mon ${etat}"
             ${action ? 'data-mon="' + action + '" data-code="' + echapperTexte(m.commune_code) + '" role="button" tabindex="0"' : ''}
             title="${echapperTexte(m.embleme)} — ${echapperTexte(m.nom)}, connu en ${Number(m.langues) || 0} langues">
      <div class="mon-int">
        <div class="mon-art">
          ${u ? '<img src="' + echapperTexte(u) + '" alt="" loading="lazy" decoding="async" onerror="this.remove()">'
              : '<span class="mon-sans">' + ICONE_MONUMENT + '</span>'}
          <span class="mon-dept">${echapperTexte(dept)}</span>
        </div>
        <div class="mon-infos">
          <p class="mon-nom ${(m.embleme || '').length > 24 ? 'long' : ''}">${echapperTexte(m.embleme)}</p>
          <p class="mon-ou">${echapperTexte(m.nom)}</p>
        </div>
        <p class="mon-qui">${qui}</p>
      </div>
    </article>`;
}

function renderMonuments(){
  const grille = document.getElementById('monGrille');
  const filtres = document.getElementById('monFiltres');
  if(!grille) return;

  const compte = {
    tous: monuments.length,
    moi: monuments.filter(m => m.a_moi).length,
    libres: monuments.filter(m => m.libre).length,
    pris: monuments.filter(m => !m.a_moi && !m.libre).length,
  };
  const cpt = document.getElementById('monCompteur');
  if(cpt) cpt.textContent = compte.moi.toLocaleString('fr-FR') + ' / ' + compte.tous.toLocaleString('fr-FR');

  if(filtres){
    filtres.innerHTML = [['tous', 'Tous'], ['moi', 'À toi'],
                         ['pris', 'Chez les autres'], ['libres', 'Libres']]
      .map(([id, lab]) => `<button class="coll-filtre ${monumentFiltre === id ? 'actif' : ''}" data-monf="${id}">${lab} <span class="nb">${compte[id].toLocaleString('fr-FR')}</span></button>`)
      .join('');
  }

  let vus = monuments;
  if(monumentFiltre === 'moi') vus = vus.filter(m => m.a_moi);
  else if(monumentFiltre === 'libres') vus = vus.filter(m => m.libre);
  else if(monumentFiltre === 'pris') vus = vus.filter(m => !m.a_moi && !m.libre);

  const champ = document.getElementById('monRech');
  const t = sansAccents(champ ? champ.value.trim() : '');
  if(t){
    vus = vus.filter(m => sansAccents(m.embleme || '').indexOf(t) >= 0
                       || correspondRecherche(m.nom, m.departement, t));
  }

  if(!vus.length){
    grille.innerHTML = '<p class="collection-empty">'
      + (monuments.length ? 'Aucun monument ne correspond.' : 'Aucun monument pour le moment.')
      + '</p>';
    return;
  }
  afficherParLots(grille, vus, carteMonument,
                  [monumentFiltre, t, vus.length].join('|'), 40);
}

document.getElementById('monFiltres').addEventListener('click', (e) => {
  const b = e.target.closest('[data-monf]');
  if(!b) return;
  monumentFiltre = b.dataset.monf;
  renderMonuments();
});
document.getElementById('monRech').addEventListener('input', renderMonuments);
document.getElementById('monGrille').addEventListener('click', (e) => {
  const c = e.target.closest('[data-mon]');
  if(!c) return;
  if(c.dataset.mon === 'fiche'){ ouvrirFicheCommune(c.dataset.code); return; }
  if(c.dataset.mon === 'attaquer'){
    // on emmene le joueur la ou il peut agir, recherche deja remplie
    const m = monuments.find(x => x.commune_code === c.dataset.code);
    const tab = document.querySelector('.tab[data-tab="combat"]');
    if(tab) tab.click();
    const champ = document.getElementById('combatSearch');
    if(champ && m){ champ.value = m.nom; renderCombatGrid(); }
  }
});
document.getElementById('monGrille').addEventListener('keydown', (e) => {
  if(e.key !== 'Enter' && e.key !== ' ') return;
  const c = e.target.closest('[data-mon]');
  if(!c) return;
  e.preventDefault();
  c.click();
});


// ---------- Succes : completion par departement ----------""" % ICONE,
u'le bloc des monuments')

# --- la collection demande les noms en arriere-plan ------------------------
js = rempl(js,
u"""  renderStats();
  if(!favorisCharges) await chargerFavoris();
  renderCollection();""",
u"""  renderStats();
  if(!favorisCharges) await chargerFavoris();
  // les monuments arrivent en arriere-plan : la collection s'affiche sans
  // attendre, et les badges apparaissent quand la liste est la
  chargerNomsMonuments().then((noms) => { if(noms.size) renderCollection(); });
  renderCollection();""",
u'les noms demandes au chargement de la collection')

# --- le badge sur la vignette ----------------------------------------------
# Place AVANT l'etiquette : les deux vivent en bas a gauche, et le CSS decale
# l'etiquette quand un monument la precede.
js = rempl(js,
u"""${badgeSiege}${entry.etiquette ?""",
u"""${badgeSiege}${monumentsNoms.has(entry.code) ? `<span class="mini-monument" title="Monument : ${echapperTexte(monumentsNoms.get(entry.code))}">${ICONE_MONUMENT}</span>` : ''}${entry.etiquette ?""",
u'badge monument sur la vignette')

# --- le bandeau sur la fiche ------------------------------------------------
# --- la ligne du journal nomme le monument ----------------------------------
js = rempl(js,
u"""  const perso = e.je_suis_cible && (e.type === 'conquete' || e.type === 'achat');""",
u"""  // Le monument change de mains avec la commune : quand la ligne en concerne
  // une, on le nomme. C'est ce qui transforme « Maroli a conquis Millau » en
  // une raison d'aller la reprendre, et c'est public : tout le monde le voit
  // changer de mains. commune_code n'arrive qu'une fois journal-code.sql
  // passe ; avant, la ligne reste exactement telle qu'elle etait.
  const mon = monumentsNoms.get(e.commune_code);
  if(mon) texte += ` <span class="jr-monument" title="Monument de la commune">${ICONE_MONUMENT}${echapperTexte(mon)}</span>`;
  const perso = e.je_suis_cible && (e.type === 'conquete' || e.type === 'achat');""",
u'le monument dans le journal')

js = rempl(js,
u"""        ${gentile ? `<p class="fc-gent">les ${echapperTexte(gentile)}</p>` : ''}""",
u"""        ${gentile ? `<p class="fc-gent">les ${echapperTexte(gentile)}</p>` : ''}
        ${monumentsNoms.has(entry.code) ? `<div class="fc-monument"><span class="fc-mon-ic">${ICONE_MONUMENT}</span><span><b>${echapperTexte(monumentsNoms.get(entry.code))}</b><i>monument de la commune — il te suit tant que tu la gardes</i></span></div>` : ''}""",
u'bandeau monument sur la fiche')

ecrire('app.js', js)


# ===========================================================================
#  style.css
# ===========================================================================
css = lire('style.css')

css = rempl(css,
u"""  .obj-fait{ font-size:0.76rem; color: var(--c-peucommun); font-weight:600; white-space:nowrap; }""",
u"""  .obj-fait{ font-size:0.76rem; color: var(--c-peucommun); font-weight:600; white-space:nowrap; }

  /* ---------- L'album des monuments ---------- */
  .mon-compteur{
    font-family: var(--texte); font-size:1rem; font-weight:600;
    color: var(--brume); margin-left:8px; vertical-align:middle;
  }
  /* .tab-panel est une colonne flex en align-items:flex-start : un enfant
     direct se dimensionne sur son contenu, pas sur la largeur disponible.
     La barre de filtres refuse de passer a la ligne sur telephone, donc
     sans cette largeur imposee elle rendait toute la page plus large que
     l'ecran. Les filtres de la Collection y echappent parce qu'ils sont
     ranges dans un bloc intermediaire. */
  #monFiltres{ width:100%; min-width:0; }
  .mon-grille{
    width:100%; display:grid; grid-template-columns: repeat(auto-fill, minmax(178px, 1fr));
    gap:14px; margin-top:4px;
  }
  .mon-grille > .collection-empty{ grid-column: 1 / -1; }
  .mon{
    border-radius:12px; padding:2px;
    background: rgba(169,188,212,0.22);
    box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    transition: transform .12s ease-out;
    content-visibility: auto; contain-intrinsic-size: auto 210px;
  }
  /* Possede : cadre dore, image en couleur. C'est la seule difference qui
     compte, et elle se voit sans lire. */
  .mon.amoi{ background: linear-gradient(135deg, #FFF1B8, var(--c-legendaire) 40%, #B7791F 75%, #FCE38A); }
  .mon[data-mon]{ cursor:pointer; }
  .mon[data-mon]:hover{ transform: translateY(-2px); }
  .mon-int{
    border-radius:10px; overflow:hidden;
    background: var(--papier); color: var(--encre);
    display:flex; flex-direction:column; height:100%;
  }
  .mon-art{
    position:relative; aspect-ratio: 16 / 10; margin:4px 4px 0;
    border-radius:6px; overflow:hidden; flex-shrink:0;
    background: #C7CEDA; display:flex; align-items:center; justify-content:center;
  }
  .mon-art img{ width:100%; height:100%; object-fit:cover; display:block; }
  .mon-sans{ width:34px; height:34px; color: rgba(31,39,51,0.35); }
  .mon-sans svg{ width:100%; height:100%; display:block; }
  .mon-dept{
    position:absolute; right:5px; bottom:-4px;
    font-family: var(--titre); font-weight:900; font-size:1.5rem; line-height:1;
    color: rgba(255,255,255,0.45);
  }
  .mon-infos{ flex:1; min-height:0; padding:6px 8px 2px; }
  .mon-nom{ margin:0; font-size:0.9rem; font-weight:700; line-height:1.2; }
  .mon-nom.long{ font-size:0.78rem; }
  .mon-ou{ margin:3px 0 0; font-size:0.74rem; color: var(--ink-soft); }
  .mon-qui{
    margin:0; padding:5px 8px 7px;
    font-size:0.72rem; font-weight:600; color: var(--ink-soft);
    overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
  }
  .mon.amoi .mon-qui{ color: var(--peucommun); }
  /* Pas possede : tout passe en gris. Le joueur voit ses trous d'un coup
     d'oeil, sans avoir a lire une seule ligne. */
  .mon.libre, .mon.pris{ opacity:0.74; }
  .mon.libre .mon-int, .mon.pris .mon-int{ background:#CFD7E2; }
  .mon.libre .mon-art img, .mon.pris .mon-art img{ filter: grayscale(1) contrast(0.92); opacity:0.62; }
  .mon.libre .mon-nom, .mon.pris .mon-nom{ color: rgba(31,39,51,0.62); }
  .mon.libre .mon-qui{ font-style:italic; opacity:0.8; }
  @media (max-width: 560px){
    .mon-grille{ grid-template-columns: repeat(auto-fill, minmax(146px, 1fr)); gap:10px; }
    .mon-nom{ font-size:0.84rem; }
    .mon-nom.long{ font-size:0.72rem; }
    .mon-dept{ font-size:1.25rem; }
  }

  /* ---------- Le monument sur la vignette et sur la fiche ---------- */
  .mini-monument{
    position:absolute; bottom:4px; left:4px;
    width:19px; height:19px; padding:2px;
    border-radius:5px; background: rgba(10,22,41,0.82);
    color: var(--c-legendaire);
  }
  .mini-monument svg{ width:100%; height:100%; display:block; }
  /* les deux vivent en bas a gauche : l'etiquette se decale quand il y a un
     monument, et ne le recouvre donc jamais */
  .mini-monument ~ .mini-etiq{ left:27px; max-width:calc(78% - 23px); }
  .fc-monument{
    display:flex; align-items:center; gap:10px; margin:10px 0 2px;
    padding:9px 12px; border-radius:12px;
    background: rgba(240,180,41,0.09); border:1px solid rgba(240,180,41,0.32);
    text-align:left;
  }
  .fc-mon-ic{ width:22px; height:22px; flex-shrink:0; color: var(--c-legendaire); }
  .fc-mon-ic svg{ width:100%; height:100%; display:block; }
  .fc-monument b{ display:block; font-size:0.92rem; font-weight:600; }
  .fc-monument i{ display:block; font-size:0.72rem; color: var(--brume); font-style:normal; margin-top:1px; }
  .jr-monument{
    display:inline-flex; align-items:center; gap:4px;
    margin-left:6px; padding:1px 8px 1px 6px; border-radius:999px;
    background: rgba(240,180,41,0.14); color: var(--c-legendaire);
    font-size:0.74rem; font-weight:600; white-space:nowrap;
  }
  .jr-monument svg{ width:12px; height:12px; flex-shrink:0; }""",
u'styles des monuments')

ecrire('style.css', css)
print(u'patch53 applique.')
