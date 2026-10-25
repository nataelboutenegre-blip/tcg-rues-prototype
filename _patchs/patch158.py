# -*- coding: utf-8 -*-
u"""
patch158 — choisir la couleur de son territoire (apercu valide le 25 octobre,
« parfait comme ca »). SQL : _sql/couleur-territoire.sql (a passer AVANT).
- Profil : bloc « Ma couleur sur la carte », 24 pastilles, un clic enregistre.
  Le petit chiffre = joueurs qui l'ont deja prise.
- « Me voir en dore » (par appareil, active par defaut) : decoche, ton
  territoire s'affiche dans ta couleur aussi pour toi.
- colorForPlayer lit d'abord la couleur choisie ; sans choix, l'ancienne
  couleur automatique. Sans le SQL : rien ne change, le bloc dit « bientot ».
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
assert 'PALETTE_TERRITOIRE' not in js, u'patch158 deja applique'
js = rempl(js, u"""const COULEUR_MOI = '#F0B429';

function colorForPlayer(id){
""", u"""const COULEUR_DORE = '#F0B429';
let COULEUR_MOI = COULEUR_DORE;
// patch158 : 24 couleurs au choix (Profil > Ma couleur). Meme liste que
// palette_territoire() en base. Le dore n'y est pas : c'est « moi ».
const PALETTE_TERRITOIRE = ['#E5484D','#8E7CF6','#2EC4B6','#F76B15','#E93D82','#3DD68C','#5EB1EF','#FF977D',
  '#9EB1FF','#12A594','#D6409F','#C2A383','#B42318','#6E56CF','#0090A8','#A4D63A',
  '#F2E8D5','#7A4B2A','#00C2FF','#C77DFF','#8A9A5B','#FF5C8A','#4C6EF5','#B07A54'];
const NOMS_COULEURS = ['Rouge','Violet','Turquoise','Orange','Rose','Vert','Ciel','Corail','Lavande','Émeraude','Fuchsia','Sable',
  'Bordeaux','Indigo','Pétrole','Citron vert','Ivoire','Chocolat','Cyan','Mauve','Olive','Framboise','Bleu roi','Caramel'];
const COULEURS_CHOISIES = new Map();
let maCouleurChoisie = null, couleursDispo = null;   // null = pas encore su
const CLE_DORE = 'tf-me-voir-dore';
function meVoirDore(){ try{ return localStorage.getItem(CLE_DORE) !== '0'; }catch(e){ return true; } }
function appliquerCouleurMoi(){ COULEUR_MOI = (!meVoirDore() && maCouleurChoisie) ? maCouleurChoisie : COULEUR_DORE; }
async function chargerCouleursTerritoire(){
  try{
    const { data, error } = await sb.rpc('couleurs_territoire');
    if(error){ if(fonctionAbsente(error)) couleursDispo = false; return; }
    couleursDispo = true;
    COULEURS_CHOISIES.clear();
    for(const r of data || []) if(r.couleur) COULEURS_CHOISIES.set(r.joueur_id, r.couleur);
    maCouleurChoisie = window.__monId ? (COULEURS_CHOISIES.get(window.__monId) || null) : null;
    appliquerCouleurMoi();
  }catch(e){}
}
function couleurAuto(id){
  let hash = 0;
  for(let i = 0; i < id.length; i++){
    hash = (hash * 31 + id.charCodeAt(i)) >>> 0;
  }
  return OPPONENT_COLORS[hash % OPPONENT_COLORS.length];
}

function colorForPlayer(id){
  const choisie = id && COULEURS_CHOISIES.get(id);
  if(choisie) return choisie;
""", 'couleurs')

js = rempl(js, u"""  const uid = userData.user.id;
  window.__monId = uid;
""", u"""  const uid = userData.user.id;
  window.__monId = uid;
  await chargerCouleursTerritoire();   // patch158
""", 'chargement')

js = rempl(js, u"""    ${blocParrainage(p.parrainage)}
    ${blocsProfil(p)}""", u"""    ${blocParrainage(p.parrainage)}
    ${blocCouleur()}
    ${blocsProfil(p)}""", 'bloc')

js = rempl(js, u"""  if(e.target.closest('[data-pf="titre"]')) ouvrirChoixTitre();
""", u"""  if(e.target.closest('[data-pf="titre"]')) ouvrirChoixTitre();
  const pc = e.target.closest('[data-pf="couleur"]');   // patch158
  if(pc) choisirCouleur(pc.dataset.couleur);
  const dr = e.target.closest('[data-pf="dore"]');
  if(dr){
    try{ localStorage.setItem(CLE_DORE, dr.checked ? '1' : '0'); }catch(err){}
    appliquerCouleurMoi();
    try{ renderMapOverlay(); }catch(err){}
  }
""", 'clic')

js = rempl(js, u"""function blocParrainage(d){""", u"""// ---------- patch158 : ma couleur sur la carte ----------
function blocCouleur(){
  if(couleursDispo === false) return `<div class="pf-bloc pf-couleur"><h3>Ma couleur sur la carte</h3>
    <p class="mc-aide">Bientôt : tu pourras choisir la couleur de ton territoire.</p></div>`;
  const moi = window.__monId || '';
  const compte = new Map();
  for(const [id, c] of COULEURS_CHOISIES) if(id !== moi) compte.set(c, (compte.get(c) || 0) + 1);
  const actuelle = maCouleurChoisie || (moi ? couleurAuto(moi) : null);
  const nom = (c) => NOMS_COULEURS[PALETTE_TERRITOIRE.indexOf(c)] || '';
  const pastilles = PALETTE_TERRITOIRE.map((c, i) => {
    const n = compte.get(c) || 0, ici = c === actuelle;
    return `<button type="button" class="mc-pastille${ici ? ' choisie' : ''}" data-pf="couleur" data-couleur="${c}"
      style="background:${c}" title="${NOMS_COULEURS[i]}" aria-label="${NOMS_COULEURS[i]}" aria-pressed="${ici}">${n ? `<span class="mc-nb">${n}</span>` : ''}</button>`;
  }).join('');
  return `<div class="pf-bloc pf-couleur">
      <h3>Ma couleur sur la carte</h3>
      <div class="mc-nuancier">${pastilles}</div>
      <p class="mc-aide">${maCouleurChoisie
        ? `Les autres joueurs te voient en <b>${echapperTexte(nom(maCouleurChoisie))}</b>.`
        : `Pour l'instant, ta couleur est choisie automatiquement${actuelle ? ` (<b>${echapperTexte(nom(actuelle))}</b>)` : ''}. Touche une pastille pour choisir la tienne.`}
        Le petit chiffre : joueurs qui l'ont déjà prise.</p>
      <label class="mc-dore"><span><b>Me voir en doré</b><small>Sur ta carte, ton territoire reste doré.</small></span>
        <input type="checkbox" data-pf="dore" ${meVoirDore() ? 'checked' : ''}></label>
    </div>`;
}
async function choisirCouleur(c){
  if(!c || c === maCouleurChoisie) return;
  const { error } = await sb.rpc('choisir_couleur', { p_couleur: c });
  if(error){ notifier({ type: 'erreur', titre: 'Couleur', texte: messageLisible(error.message) }); return; }
  if(window.__monId) COULEURS_CHOISIES.set(window.__monId, c);
  maCouleurChoisie = c;
  appliquerCouleurMoi();
  rendreProfilPanneau();
  try{ renderMapOverlay(); }catch(err){}
  notifier({ type: 'succes', titre: 'Couleur enregistrée', texte: 'Les autres joueurs te voient maintenant en ' + (NOMS_COULEURS[PALETTE_TERRITOIRE.indexOf(c)] || 'couleur') + '.' });
}

function blocParrainage(d){""", 'fonctions')
ecrire('app.js', js)

css = lire('style.css')
css = rempl(css, u"  /* ---------- patch156 : glisser pour acheter ---------- */", u"""  /* ---------- patch158 : ma couleur sur la carte ---------- */
  .mc-nuancier{ display:grid; grid-template-columns:repeat(8, minmax(0, 1fr)); gap:8px; margin-top:10px; }
  @media (max-width:420px){ .mc-nuancier{ grid-template-columns:repeat(6, minmax(0, 1fr)); } }
  .mc-pastille{ aspect-ratio:1; max-width:100%; border:none; border-radius:10px; cursor:pointer; position:relative; padding:0;
    box-shadow: inset 0 0 0 2px rgba(0,0,0,.25); }
  .mc-pastille:hover{ filter:brightness(1.08); }
  .mc-pastille.choisie{ box-shadow: 0 0 0 3px var(--nuit-2), 0 0 0 5px #fff; }
  .mc-pastille.choisie::after{ content:"✓"; position:absolute; inset:0; display:grid; place-items:center; color:#0B1628; font-weight:800; font-size:1.05rem; }
  .mc-nb{ position:absolute; right:3px; bottom:1px; font-size:.6rem; font-weight:700; color:rgba(11,22,40,.75); }
  .mc-aide{ color:#A9BCD4; font-size:.82rem; line-height:1.5; margin:12px 0 0; }
  .mc-aide b{ color:#fff; }
  .mc-dore{ display:flex; align-items:center; justify-content:space-between; gap:12px; margin-top:12px; padding:10px 12px;
    border-radius:10px; background:rgba(7,16,31,.5); cursor:pointer; }
  .mc-dore b{ display:block; font-size:.9rem; } .mc-dore small{ color:#A9BCD4; font-size:.78rem; }
  .mc-dore input{ width:20px; height:20px; accent-color: var(--c-legendaire); flex:none; }
  /* ---------- patch156 : glisser pour acheter ---------- */""", 'css')
ecrire('style.css', css)
print(u'patch158 applique. Lancer : python3 maj-version.py')
