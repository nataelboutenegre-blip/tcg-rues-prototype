# -*- coding: utf-8 -*-
u"""
patch107 — saison 2 : la boutique (points Terra seulement)
CACHÉE tant que SAISON2 = false. SQL : s2-15-boutique.sql (avant le push).

Onglet Boutique dans Terra :
 - Paquet garanti (5 communes dont au moins une rare ou mieux)
 - Paquet du département (5 communes du département choisi)
   -> payés puis ouverts avec la même animation que les paquets Terra,
      3 par jour au maximum, ne comptent pas pour les quêtes ;
 - Dos de cartes : d'origine, Bocage, Terre cuite, Blé d'or. Un dos acheté
   est mis tout de suite, et s'applique à toutes les cartes du jeu.
Achat en deux temps (le bouton demande confirmation) pour éviter un clic
malheureux.
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

# ---------- index.html : onglet + panneau ---------------------------------------
html = lire('index.html')
assert 'panel-boutique' not in html, u'patch107 deja applique'

html = rempl(html, u"""        Échange
        <span class="tab-badge" id="echangeBadge" hidden></span>
      </div>
""", u"""        Échange
        <span class="tab-badge" id="echangeBadge" hidden></span>
      </div>

      <div class="tab" data-tab="boutique">
        <div class="icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 9.5h16l-1.2 10a1.6 1.6 0 0 1-1.6 1.5H6.8a1.6 1.6 0 0 1-1.6-1.5z"/>
            <path d="M8.5 9.5V7a3.5 3.5 0 0 1 7 0v2.5"/>
          </svg>
        </div>
        Boutique
      </div>
""", 'onglet')

html = rempl(html, u"""    <section class="tab-panel" id="panel-bourse">""", u"""    <section class="tab-panel" id="panel-boutique">
      <h1>Boutique</h1>
      <div class="sub">Dépense tes points Terra : paquets spéciaux et dos de cartes. Tout s'achète en points, rien en euros.</div>
      <div class="puces" id="bqStatut"><span class="puce">Chargement…</span></div>
      <div class="bourse-section bq-section">
        <h2>Paquets</h2>
        <div class="bq-grille" id="bqPaquets"></div>
      </div>
      <div class="bourse-section bq-section">
        <h2>Dos de cartes</h2>
        <div class="bq-grille bq-grille-dos" id="bqDos"></div>
      </div>
      <div class="note">3 paquets de boutique par jour au maximum. Ils ne comptent pas pour les quêtes. Un dos de carte change l'arrière de toutes tes cartes, et tu peux revenir au dos d'origine quand tu veux.</div>
    </section>

    <section class="tab-panel" id="panel-bourse">""", 'panneau')
ecrire('index.html', html)

# ---------- app.js ----------------------------------------------------------------
js = lire('app.js')

# l'onglet appartient a Terra
js = rempl(js, u"""           propres: ['tirage', 'collection', 'qg', 'contrat', 'monuments', 'bourse', 'echange'] },""",
           u"""           propres: ['tirage', 'collection', 'qg', 'contrat', 'monuments', 'bourse', 'echange', 'boutique'] },""", 'mode terra')

# en saison 1, la boutique n'apparait pas dans le menu Plus
js = rempl(js, u"""  .filter((id) => ONGLETS_BARRE.indexOf(id) < 0 && ONGLETS_FUSIONNES.indexOf(id) < 0);""",
           u"""  .filter((id) => ONGLETS_BARRE.indexOf(id) < 0 && ONGLETS_FUSIONNES.indexOf(id) < 0)
  .filter((id) => SAISON2 || id !== 'boutique');   // patch107""", 'menu s1')

# chargement a l'ouverture de l'onglet
js = rempl(js, u"""    if(tab.dataset.tab === 'bourse') loadBourse();
""", u"""    if(tab.dataset.tab === 'bourse') loadBourse();
    if(tab.dataset.tab === 'boutique') loadBoutique();
""", 'onglet charge')

# le dos choisi s'applique des l'arrivee
js = rempl(js, u"""  if(SAISON2) initModes();
""", u"""  if(SAISON2) initModes();
  if(SAISON2) loadBoutique(true);   // patch107 : le dos de carte choisi
""", 'init dos')

# un paquet de boutique se paie par sa propre fonction
js = rempl(js, u"""  if(enTerra()){
    // Terra : le serveur paie et tire les 5 cartes en un seul appel
    const { data, error } = await sb.rpc('terra_ouvrir_paquet', { p_paye: type === 'achete' });""",
u"""  if(boutiqueAchat){
    // patch107 : paquet de la boutique, paye et tire en un seul appel
    const achat = boutiqueAchat;
    boutiqueAchat = null;
    const { data, error } = await sb.rpc('boutique_ouvrir_paquet', { p_article: achat.id, p_departement: achat.dep });
    terraPaquet = error ? null : (data || []);
    boutiqueOuvert = !error;
    viderBilanTerra();
    return error;
  }
  if(enTerra()){
    // Terra : le serveur paie et tire les 5 cartes en un seul appel
    const { data, error } = await sb.rpc('terra_ouvrir_paquet', { p_paye: type === 'achete' });""", 'payer')

# messages lisibles
js = rempl(js, u"""    [/rate limit|too many requests/i, 'Trop de tentatives. Réessaie dans quelques minutes.'],
  ];""", u"""    [/rate limit|too many requests/i, 'Trop de tentatives. Réessaie dans quelques minutes.'],
    [/deja achete 3 paquets en boutique/i, 'Tu as déjà acheté 3 paquets en boutique aujourd\\'hui. Reviens demain.'],
    [/^Choisis un departement$/i, 'Choisis d\\'abord un département.'],
    [/^Tu l'as deja$/i, 'Tu l\\'as déjà.'],
    [/^Tu ne l'as pas encore$/i, 'Achète-le d\\'abord.'],
    [/La boutique ouvre avec la saison 2/i, 'La boutique ouvre avec la saison 2.'],
  ];""", 'messages')

js += u"""

// ---------- patch107 : la boutique (points Terra) ----------
let boutiqueAchat = null;     // { id, dep } : le prochain paquet ouvert vient de la boutique
let boutiqueOuvert = false;   // le dernier paiement de boutique a reussi
let boutiqueCache = null;
const BQ_DOS = [
  { id: null, nom: 'D\\'origine', description: 'Nuit et or, le dos de toujours' },
];
function dosCle(id){ return id ? id.replace(/^dos-/, '') : 'origine'; }
function appliquerDos(id){
  document.body.dataset.dos = dosCle(id);
}
function dosApercuHtml(id){
  return `<div class="bq-dos-apercu" data-dos="${dosCle(id)}" aria-hidden="true"><div class="bq-dos-echelle">
      <div class="face face-back">
        ${DOS_MOTIF_SVG}
        <span class="dos-coin hg"></span><span class="dos-coin hd"></span><span class="dos-coin bg"></span><span class="dos-coin bd"></span>
        <div class="dos-embleme">${ICONE_EPINGLE}</div>
      </div></div></div>`;
}
async function loadBoutique(silencieux){
  if(!SAISON2) return;
  const { data, error } = await sb.rpc('boutique');
  if(error){
    if(!silencieux){
      const st = document.getElementById('bqStatut');
      if(st) st.innerHTML = `<span class="puce">${echapperTexte(messageLisible(error.message))}</span>`;
    }
    return;
  }
  boutiqueCache = data;
  appliquerDos(data.dos);
  renderBoutique();
}
function bqPrix(n){ return Number(n).toLocaleString('fr-FR') + ' pts'; }
function renderBoutique(){
  const b = boutiqueCache;
  if(!b) return;
  const st = document.getElementById('bqStatut');
  const paq = document.getElementById('bqPaquets');
  const dos = document.getElementById('bqDos');
  if(!st || !paq || !dos) return;
  const restants = Math.max(0, b.paquets_max - b.paquets_du_jour);
  st.innerHTML = `<span class="puce solde">Solde <b>${Number(b.solde).toLocaleString('fr-FR')}</b></span>`
               + `<span class="puce">Paquets de boutique aujourd'hui <b>${b.paquets_du_jour} sur ${b.paquets_max}</b></span>`;

  const deps = Object.keys(DEPT_NAMES).sort((x, y) => x.localeCompare(y, 'fr', { numeric: true }));
  paq.innerHTML = b.articles.filter(a => a.type === 'paquet').map(a => {
    const choixDep = a.id === 'paquet-departement'
      ? `<select class="bq-dep" id="bqDep" aria-label="Département"><option value="">Choisis un département</option>${
          deps.map(d => `<option value="${d}">${d} · ${echapperTexte(DEPT_NAMES[d])}</option>`).join('')}</select>` : '';
    const bouton = restants < 1
      ? `<button class="bq-btn" disabled>Revient demain</button>`
      : `<button class="bq-btn" data-bq-paquet="${a.id}" data-prix="${a.prix}"${b.solde < a.prix ? ' data-court="1"' : ''}>${bqPrix(a.prix)}</button>`;
    return `<div class="bq-article bq-paquet ${a.id}">
        <div class="bq-paquet-icone" aria-hidden="true">${ICONE_EPINGLE}</div>
        <b>${echapperTexte(a.nom)}</b>
        <p>${echapperTexte(a.description)}</p>
        ${choixDep}
        ${bouton}
      </div>`;
  }).join('');

  const liste = BQ_DOS.map(d => ({ ...d, prix: 0, possede: true }))
    .concat(b.articles.filter(a => a.type === 'dos'));
  dos.innerHTML = liste.map(a => {
    const equipe = (b.dos || null) === a.id;
    let action;
    if(equipe) action = `<span class="bq-equipe">Sur tes cartes</span>`;
    else if(a.possede) action = `<button class="bq-btn secondaire" data-bq-mettre="${a.id || ''}">Mettre</button>`;
    else action = `<button class="bq-btn" data-bq-dos="${a.id}" data-prix="${a.prix}"${b.solde < a.prix ? ' data-court="1"' : ''}>${bqPrix(a.prix)}</button>`;
    return `<div class="bq-article bq-dos${equipe ? ' equipe' : ''}">
        ${dosApercuHtml(a.id)}
        <b>${echapperTexte(a.nom)}</b>
        <p>${echapperTexte(a.description)}</p>
        ${action}
      </div>`;
  }).join('');
}

// achat en deux temps : le premier clic demande confirmation pendant 4 s
function bqConfirmer(btn){
  if(btn.dataset.court){
    notifier({ type: 'erreur', titre: 'Solde insuffisant', texte: 'Il te faut ' + bqPrix(btn.dataset.prix) + '.' });
    return false;
  }
  if(btn.classList.contains('confirmer')) return true;
  document.querySelectorAll('.bq-btn.confirmer').forEach(x => { x.classList.remove('confirmer'); x.textContent = bqPrix(x.dataset.prix); });
  btn.classList.add('confirmer');
  btn.textContent = 'Confirmer l\\'achat';
  clearTimeout(btn._bqMinuteur);
  btn._bqMinuteur = setTimeout(() => {
    if(btn.isConnected && btn.classList.contains('confirmer')){
      btn.classList.remove('confirmer');
      btn.textContent = bqPrix(btn.dataset.prix);
    }
  }, 4000);
  return false;
}

async function acheterPaquetBoutique(id){
  if(paquetEnCours){
    notifier({ type: 'erreur', titre: 'Un paquet t\\'attend déjà', texte: 'Ouvre d\\'abord celui qui est sur la table.' });
    return;
  }
  let dep = null;
  if(id === 'paquet-departement'){
    const sel = document.getElementById('bqDep');
    dep = sel ? sel.value : '';
    if(!dep){
      notifier({ type: 'erreur', titre: 'Choisis d\\'abord un département' });
      if(sel) sel.focus();
      return;
    }
  }
  boutiqueAchat = { id, dep };
  boutiqueOuvert = false;
  const tirage = document.querySelector('.tab[data-tab="tirage"]');
  if(tirage) tirage.click();
  await openPack('achete');
  boutiqueAchat = null;
  if(!boutiqueOuvert) return;
  const bande = document.querySelector('#packZone .paquet .paquet-bande');
  if(bande) bande.textContent = id === 'paquet-departement'
    ? (DEPT_NAMES[dep] || dep) + ' (' + dep + ')'
    : '1 rare ou mieux';
  const titre = document.querySelector('#packZone .paquet .paquet-titre');
  if(titre) titre.textContent = id === 'paquet-departement' ? 'Département' : 'Garanti';
}

async function acheterDosBoutique(id){
  const { data, error } = await sb.rpc('boutique_acheter', { p_article: id });
  if(error){ notifier({ type: 'erreur', titre: 'Achat impossible', texte: messageLisible(error.message) }); return loadBoutique(); }
  boutiqueCache = data;
  appliquerDos(data.dos);
  renderBoutique();
  const a = data.articles.find(x => x.id === id);
  notifier({ type: 'succes', titre: 'Nouveau dos de carte', texte: (a ? a.nom : 'Ton dos') + ' est sur toutes tes cartes.' });
}

async function mettreDosBoutique(id){
  const { data, error } = await sb.rpc('boutique_equiper', { p_article: id || null });
  if(error){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible(error.message) }); return; }
  boutiqueCache = data;
  appliquerDos(data.dos);
  renderBoutique();
}

document.getElementById('panel-boutique').addEventListener('click', (e) => {
  const btn = e.target.closest('button.bq-btn');
  if(!btn || btn.disabled) return;
  if(btn.dataset.bqMettre !== undefined) return mettreDosBoutique(btn.dataset.bqMettre);
  if(!bqConfirmer(btn)) return;
  btn.disabled = true;
  if(btn.dataset.bqPaquet) acheterPaquetBoutique(btn.dataset.bqPaquet).finally(() => { btn.disabled = false; });
  else if(btn.dataset.bqDos) acheterDosBoutique(btn.dataset.bqDos).finally(() => { btn.disabled = false; });
});
"""
ecrire('app.js', js)

# ---------- style.css ---------------------------------------------------------------
css = lire('style.css')
assert '.bq-article' not in css
css += u"""
/* patch107 : la boutique (saison 2) */
html:not(.saison-2) .tab[data-tab="boutique"]{ display:none !important; }
.bq-section{ max-width: 860px; }
.bq-grille{ display:grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 12px; }
.bq-article{
  background: rgba(15,31,56,0.55); border: 1px solid rgba(169,188,212,0.18); border-radius: 12px;
  padding: 14px; display:flex; flex-direction:column; gap: 6px; color:#fff;
}
.bq-article b{ font-family: var(--titre); font-size: 1.15rem; letter-spacing: .02em; }
.bq-article p{ margin:0; font-size: .8rem; color: var(--brume); line-height: 1.4; flex: 1; }
.bq-paquet-icone{
  width: 40px; height: 40px; border-radius: 50%; display:flex; align-items:center; justify-content:center;
  background: var(--nuit); box-shadow: 0 0 0 2px var(--c-rare);
}
.bq-paquet-icone svg{ width: 20px; height: 20px; stroke: var(--c-rare); }
.bq-paquet.paquet-departement .bq-paquet-icone{ box-shadow: 0 0 0 2px var(--c-peucommun); }
.bq-paquet.paquet-departement .bq-paquet-icone svg{ stroke: var(--c-peucommun); }
.bq-dep{
  width: 100%; padding: 8px; border-radius: 8px; font: inherit; font-size: .85rem;
  background: var(--nuit); color: #fff; border: 1px solid rgba(169,188,212,0.3);
}
.bq-btn{
  margin-top: 4px; padding: 9px 12px; border-radius: 9px; border: 0; cursor: pointer;
  font-family: var(--titre); font-weight: 800; font-size: 1.02rem; letter-spacing: .02em;
  background: var(--c-legendaire); color: var(--encre);
}
.bq-btn.secondaire{ background: transparent; color:#fff; box-shadow: inset 0 0 0 2px rgba(169,188,212,0.35); }
.bq-btn.confirmer{ background: var(--c-peucommun); color:#fff; }
.bq-btn[data-court]{ opacity: .55; }
.bq-btn:disabled{ opacity: .45; cursor: default; }
.bq-equipe{ margin-top: 4px; text-align:center; padding: 9px 0; font-size: .85rem; color: var(--c-peucommun); font-weight: 600; }
.bq-dos.equipe{ border-color: var(--c-peucommun); }
.bq-grille-dos{ grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); }
.bq-dos-apercu{ width: 94px; height: 131.5px; margin: 0 auto 4px; position: relative; }
.bq-dos-echelle{ width: 188px; height: 263px; transform: scale(.5); transform-origin: 0 0; position: absolute; left:0; top:0; }

/* les dos de cartes : variables lues par le dos de toutes les cartes */
.face-back{ background: var(--dos-fond, radial-gradient(circle at 50% 42%, #24446F 0%, #13284A 55%, #0B1830 100%)); }
.face-back::before{ border-color: var(--dos-liseret, rgba(240,180,41,0.55)); }
.face-back .dos-embleme{
  background: var(--dos-embleme, var(--nuit));
  box-shadow: 0 0 0 2px var(--dos-or, var(--c-legendaire)), 0 0 0 7px var(--dos-anneau, rgba(15,31,56,0.9)), 0 0 0 8.5px var(--dos-liseret, rgba(240,180,41,0.4));
}
.face-back .dos-embleme svg{ stroke: var(--dos-or, var(--c-legendaire)); }
.face-back .dos-coin{ background: var(--dos-or, var(--c-legendaire)); }
.bq-dos-apercu[data-dos="origine"]{
  --dos-fond: radial-gradient(circle at 50% 42%, #24446F 0%, #13284A 55%, #0B1830 100%);
  --dos-liseret: rgba(240,180,41,0.55); --dos-embleme: var(--nuit); --dos-or: var(--c-legendaire); --dos-anneau: rgba(15,31,56,0.9);
}
body[data-dos="bocage"], .bq-dos-apercu[data-dos="bocage"]{
  --dos-fond: radial-gradient(circle at 50% 42%, #2F6142 0%, #1B3D29 55%, #0E2417 100%);
  --dos-liseret: rgba(205,133,78,0.6); --dos-embleme: #12291B; --dos-or: #D08A52; --dos-anneau: rgba(14,36,23,0.9);
}
body[data-dos="terre-cuite"], .bq-dos-apercu[data-dos="terre-cuite"]{
  --dos-fond: radial-gradient(circle at 50% 42%, #B35C40 0%, #833A27 55%, #4F1F15 100%);
  --dos-liseret: rgba(243,227,195,0.55); --dos-embleme: #5A2618; --dos-or: #F3E3C3; --dos-anneau: rgba(79,31,21,0.9);
}
body[data-dos="ble-or"], .bq-dos-apercu[data-dos="ble-or"]{
  --dos-fond: radial-gradient(circle at 50% 42%, #F2C85A 0%, #C9952A 55%, #85600F 100%);
  --dos-liseret: rgba(19,35,59,0.55); --dos-embleme: #13233B; --dos-or: #F6D77A; --dos-anneau: rgba(133,96,15,0.9);
}
@media (max-width: 560px){ .bq-grille{ grid-template-columns: 1fr 1fr; } .bq-grille-dos{ grid-template-columns: 1fr 1fr; } }
"""
ecrire('style.css', css)
print(u'patch107 applique')
