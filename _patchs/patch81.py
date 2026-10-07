# -*- coding: utf-8 -*-
u"""
patch81 — Les monuments se voient quand on les obtient.

Avant : une commune à monument sortait d'un paquet, d'une conquête ou d'un
contrat exactement comme les autres. Rien ne disait « tu as aussi le viaduc
de Millau ».

Maintenant :
- Tirage : la carte porte un bandeau doré avec le nom du monument, elle sort
  en dernier dans son palier, la ligne sous la carte annonce le monument et
  une notification dorée le confirme (aussi quand l'animation est coupée).
- Conquête : la fenêtre « Commune conquise » montre le monument, avec sa
  photo quand il en a une.
- Contrat : la notification de fin nomme le monument reçu. Et dans le lot à
  sacrifier, une commune à monument porte le badge, avec un avertissement :
  avant, on pouvait donner le Mont-Saint-Michel sans le savoir.
- L'album des monuments est relu après chacun de ces gains.
Corrigé au passage : le bas des y, g, p, j coupé dans le nom des cartes.\nAucun changement SQL.
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

def rempl(src, avant, apres, etiquette, nb=1):
    n = src.count(avant)
    assert n == nb, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)

js = lire('app.js')

# --- 1. la notification dorée ------------------------------------------------
js = rempl(js,
u'''    <span class="notif-icone">${ICONES_NOTIF[type] || ICONES_NOTIF.info}</span>''',
u'''    <span class="notif-icone">${ICONES_NOTIF[type] || (type === 'monument' ? ICONE_MONUMENT : ICONES_NOTIF.info)}</span>''',
'notif icone')

# --- 2. les noms ET les photos des monuments ---------------------------------
js = rempl(js,
u'''let monumentsNoms = new Map();
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
}''',
u'''let monumentsNoms = new Map();
let monumentsPhotos = new Map();
let monumentsNomsPromesse = null;
function chargerNomsMonuments(){
  if(monumentsNomsPromesse) return monumentsNomsPromesse;
  const lireListe = (colonnes) => Promise.resolve(sb.from('monuments').select(colonnes));
  monumentsNomsPromesse = lireListe('commune_code, nom, photo')
    // sans la colonne photo, on se contente des noms
    .then((r) => r.error ? lireListe('commune_code, nom') : r)
    .then(({ data, error }) => {
      // monuments.sql pas encore passe : on repart avec une liste vide et le
      // jeu se comporte exactement comme avant
      if(!error){
        monumentsNoms = new Map((data || []).map(m => [m.commune_code, m.nom]));
        monumentsPhotos = new Map((data || []).filter(m => m.photo).map(m => [m.commune_code, m.photo]));
      }
      return monumentsNoms;
    })
    .catch(() => monumentsNoms);
  return monumentsNomsPromesse;
}

// Le monument d'une commune, ou null. Sert au tirage, a la conquete et au
// contrat : un monument obtenu doit se voir au moment ou on l'obtient.
function monumentDe(code){
  const nom = monumentsNoms.get(code);
  return nom ? { nom, photo: monumentsPhotos.get(code) || '' } : null;
}
function annoncerMonument(code, nomCommune){
  const m = monumentDe(code);
  if(!m) return;
  monumentsLe = 0;                 // l'album a change : on le relira
  notifier({ type: 'monument', titre: 'Monument obtenu : ' + m.nom,
    texte: `Il est à toi tant que tu gardes ${nomCommune}.`, duree: 6000 });
}''', 'chargerNomsMonuments')

# --- 3. la carte tiree porte son monument ------------------------------------
js = rempl(js,
u'''function makeCardEl(draw, onFlip){
  const wrap = document.createElement('div');
  wrap.className = 'card ' + draw.tier.id;''',
u'''function makeCardEl(draw, onFlip){
  const wrap = document.createElement('div');
  const mon = monumentDe(draw.code);
  wrap.className = 'card ' + draw.tier.id + (mon ? ' a-monument' : '');''', 'makeCardEl classe')
js = rempl(js,
u'''            <div class="carte-art">${carteArtSvg(draw.code, draw.tier.id)}<span class="carte-dept">${draw.dept}</span></div>''',
u'''            <div class="carte-art">${carteArtSvg(draw.code, draw.tier.id)}<span class="carte-dept">${draw.dept}</span>${mon ? `<span class="carte-monument" title="Monument de la commune">${ICONE_MONUMENT}<b>${echapperTexte(mon.nom)}</b></span>` : ''}</div>''',
'makeCardEl bandeau')

js = rempl(js,
u'''    collectionMap.set(draw.code, draw);
    session[draw.tier.id]++;''',
u'''    collectionMap.set(draw.code, draw);
    annoncerMonument(draw.code, draw.nom);
    session[draw.tier.id]++;''', 'surCarteRetournee')

# dans un palier, la carte a monument sort en dernier
js = rempl(js,
u'''const trierPourRevelation = (draws) =>
  draws.slice().sort((a, b) => RANG_TIER[a.tier.id] - RANG_TIER[b.tier.id]);''',
u'''const trierPourRevelation = (draws) =>
  draws.slice().sort((a, b) => RANG_TIER[a.tier.id] - RANG_TIER[b.tier.id]
    || (monumentsNoms.has(a.code) ? 1 : 0) - (monumentsNoms.has(b.code) ? 1 : 0));''', 'tri')

# la ligne sous la carte annonce le monument plutot que le gentile
js = rempl(js,
u'''  const decouvrir = (draw) => {
    decouverte.textContent = '';
    detailsCommune(draw.code).then(d => {''',
u'''  const decouvrir = (draw) => {
    decouverte.textContent = '';
    decouverte.classList.remove('monument');
    const mon = monumentDe(draw.code);
    if(mon){
      decouverte.classList.add('monument');
      decouverte.innerHTML = `${ICONE_MONUMENT}<span>Monument : <b>${echapperTexte(mon.nom)}</b>. Il te suit tant que tu gardes ${echapperTexte(draw.nom)}.</span>`;
      return;
    }
    detailsCommune(draw.code).then(d => {''', 'decouvrir')
js = rempl(js,
u'''      if(RANG_TIER[draw.tier.id] >= 2) el.classList.add('ouv-eclat');''',
u'''      if(RANG_TIER[draw.tier.id] >= 2 || monumentsNoms.has(draw.code)) el.classList.add('ouv-eclat');''', 'eclat')

# les noms doivent etre la avant la premiere carte
js = rempl(js,
u'''async function openPack(type){
  document.getElementById('openFreeBtn').disabled = true;''',
u'''async function openPack(type){
  chargerNomsMonuments();
  document.getElementById('openFreeBtn').disabled = true;''', 'openPack')

# --- 4. la conquete --------------------------------------------------------
js = rempl(js,
u'''function celebrerConquete({ nom, tier, dept, bonus }){
  const t = TIERS.find(x => x.id === tier);''',
u'''function celebrerConquete({ nom, tier, dept, bonus, code }){
  const t = TIERS.find(x => x.id === tier);
  const mon = code ? monumentDe(code) : null;
  const photoMon = mon && mon.photo ? urlPhoto(mon.photo) : '';
  if(mon) monumentsLe = 0;''', 'celebrer debut')
js = rempl(js,
u'''      <p class="conquete-bonus">+${Number(bonus).toLocaleString('fr-FR')} pts de bonus</p>
      <p class="conquete-note">''',
u'''      <p class="conquete-bonus">+${Number(bonus).toLocaleString('fr-FR')} pts de bonus</p>
      ${mon ? `<div class="conquete-monument">
        <span class="cm-art">${photoMon ? `<img src="${echapperTexte(photoMon)}" alt="" onerror="this.remove()">` : ''}${ICONE_MONUMENT}</span>
        <span class="cm-tx"><i>Monument conquis avec la commune</i><b>${echapperTexte(mon.nom)}</b></span>
      </div>` : ''}
      <p class="conquete-note">''', 'celebrer bloc')
js = rempl(js,
u'''      celebrerConquete({ nom, tier, dept, bonus: Math.floor(PRIX_RACHAT[tier] * BONUS_CONQUETE_PART) });''',
u'''      celebrerConquete({ nom, tier, dept, code, bonus: Math.floor(PRIX_RACHAT[tier] * BONUS_CONQUETE_PART) });''', 'celebrer carte')
js = rempl(js,
u'''          celebrerConquete({
            nom: nomCible,''',
u'''          celebrerConquete({
            nom: nomCible,
            code,''', 'celebrer combat')

# --- 5. le contrat ----------------------------------------------------------
js = rempl(js,
u'''  if(carte && carte.nom){
    notifier({ type: 'succes', titre: 'Contrat honoré',
      texte: `${carte.nom} rejoint ta collection.` });
  }''',
u'''  if(carte && carte.nom){
    notifier({ type: 'succes', titre: 'Contrat honoré',
      texte: `${carte.nom} rejoint ta collection.` });
    if(carte.code) annoncerMonument(carte.code, carte.nom);
  }''', 'contrat fin')
js = rempl(js,
u'''      <span class="tx"><span class="nm"><i>${echapperTexte(x.nom || x.commune_code)}</i>${badgeDept(x.departement)}</span><span class="hb">${ctNb(x.population || 0)} hab.</span></span>''',
u'''      <span class="tx"><span class="nm"><i>${echapperTexte(x.nom || x.commune_code)}</i>${badgeDept(x.departement)}</span><span class="hb">${ctNb(x.population || 0)} hab.${monumentsNoms.has(x.commune_code) ? `<span class="jr-monument ct-mon" title="Ce monument partirait avec la commune">${ICONE_MONUMENT}<span>${echapperTexte(monumentsNoms.get(x.commune_code))}</span></span>` : ''}</span></span>''',
'contrat lot (le lot et la liste « changer »)', nb=2)
js = rempl(js,
u'''  if(avert) avert.textContent =
    `Les ${contratChoisi.n} communes sacrifiées retournent au pot. C'est définitif.`;''',
u'''  const nbMon = contratLot.filter(x => monumentsNoms.has(x.commune_code)).length;
  if(avert) avert.textContent =
    `Les ${contratChoisi.n} communes sacrifiées retournent au pot. C'est définitif.`
    + (nbMon ? ` Attention : ${nbMon > 1 ? nbMon + ' monuments partent' : 'un monument part'} avec elles — « changer » ou le cadenas pour ${nbMon > 1 ? 'les' : 'le'} garder.` : '');''',
'contrat avert')
ecrire('app.js', js)

css = lire('style.css')
css += u'''

/* ---------- patch81 : les monuments se voient quand on les obtient ---------- */
.carte-monument{
  position:absolute; left:6px; right:6px; bottom:6px;
  display:flex; align-items:center; gap:5px;
  padding:4px 8px 4px 6px; border-radius:7px;
  background: rgba(10,22,41,0.92);
  border:1px solid rgba(240,180,41,0.75);
  color: var(--c-legendaire);
  font-size:0.68rem; line-height:1.15;
  box-shadow: 0 2px 8px rgba(10,22,41,0.35);
}
.carte-monument svg{ width:14px; height:14px; flex-shrink:0; }
.carte-monument b{ font-weight:700; color:#FFE7A8; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.card.a-monument .carte-cadre{ box-shadow: 0 0 0 2px rgba(240,180,41,0.85), 0 0 22px rgba(240,180,41,0.35); }
/* le dos ne trahit rien : le bandeau est sur la face */

.ouv-decouverte.monument{
  display:flex; align-items:center; justify-content:center; gap:8px;
  color:#FFE7A8;
}
.ouv-decouverte.monument svg{ width:18px; height:18px; flex-shrink:0; color: var(--c-legendaire); }
.ouv-decouverte.monument b{ color: var(--c-legendaire); }

.notif.monument{ border-color: rgba(240,180,41,0.6); }
.notif.monument .notif-icone{ color: var(--c-legendaire); }

.conquete-monument{
  position:relative; display:flex; align-items:center; gap:12px;
  margin:12px auto 14px; padding:8px 12px 8px 8px; max-width:340px;
  border-radius:12px; text-align:left;
  background: rgba(240,180,41,0.10); border:1px solid rgba(240,180,41,0.45);
}
.cm-art{
  position:relative; width:56px; height:56px; flex-shrink:0;
  border-radius:9px; overflow:hidden; background: rgba(240,180,41,0.16);
  display:flex; align-items:center; justify-content:center; color: var(--c-legendaire);
}
.cm-art svg{ width:26px; height:26px; }
.cm-art img{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }
.cm-tx i{ display:block; font-style:normal; font-size:0.72rem; color: var(--brume); }
.cm-tx b{ display:block; font-size:1rem; font-weight:700; color:#FFE7A8; line-height:1.2; margin-top:2px; }

.ct-mon{ margin-left:8px; font-size:0.68rem; max-width:calc(100% - 70px); vertical-align:middle; }
.ct-mon > span{ overflow:hidden; text-overflow:ellipsis; }
@media (max-width: 760px){
  .carte-monument{ font-size:0.6rem; padding:3px 6px 3px 5px; left:4px; right:4px; bottom:4px; }
  .carte-monument svg{ width:12px; height:12px; }
  .ouv-decouverte.monument{ display:block; font-size:.8rem; padding:0 16px; }
  .ouv-decouverte.monument svg{ display:inline-block; width:15px; height:15px; vertical-align:-2px; margin-right:4px; }
}
'''
css += u'''
/* les jambages (y, g, p, j) etaient coupes : interligne a 0,95-0,98 et
   overflow:hidden du line-clamp. Un peu d'air sous la derniere ligne. */
.carte-nom, .mini-nom{ line-height:1.06; padding-bottom:0.08em; }
'''
ecrire('style.css', css)
print(u'patch81 : OK')
