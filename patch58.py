# -*- coding: utf-8 -*-
u"""
patch58 — Le panneau de la carte annonce les echanges proposes.

CE QUE TU AS DEMANDE
  En cliquant une commune sur la carte, voir « on te propose un echange pour
  cette carte », et pouvoir aller a l'echange d'un clic.

CE QUE J'AI TROUVE EN LE FAISANT
  Les propositions en attente n'etaient chargees qu'a l'ouverture de l'onglet
  Echange. Consequence : la pastille de l'onglet, celle qui annonce « 2
  propositions », ne s'allumait QUE si on ouvrait l'onglet. Un joueur qui ne
  va jamais sur Echange n'apprenait jamais qu'on lui proposait quelque chose.

  C'est le meme defaut que celui des monuments ce matin, au meme endroit : une
  information n'existe que si on va la chercher. Les propositions sont donc
  chargees au demarrage, comme le reste. Une requete de plus a l'ouverture du
  jeu, et la pastille dit enfin la verite.

CE QUE LE PANNEAU AFFICHE
  Une bande cliquable, seulement s'il y a une proposition en attente sur cette
  commune, et elle dit laquelle des quatre situations :
    — Maroli veut cette commune en echange   (on te la demande)
    — Maroli te propose cette commune        (on te l'offre)
    — Tu as propose cette commune en echange
    — Tu as demande cette commune en echange

  Dire « on te propose un echange » dans les quatre cas aurait ete plus court
  et faux trois fois sur quatre.

  Un clic ferme le panneau et ouvre l'onglet Echange, ou les propositions sont
  listees en haut.

CE QUE JE N'AI PAS FAIT
  Pas de rafraichissement automatique du panneau quand une proposition arrive
  pendant qu'il est ouvert. Il se remplit a l'ouverture, ce qui suffit : on ne
  reste pas une minute devant un panneau de carte.
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


# ===========================================================================
#  app.js
# ===========================================================================
js = lire('app.js')

# --- 1. les propositions se chargent au demarrage --------------------------
js = rempl(js,
u"""async function loadEchanges(){
  const { data, error } = await sb.rpc('mes_echanges');
  if(error) console.error(error);
  echangesEnCours = error ? [] : (data || []);
  renderEchangePropositions();
  majBadgeEchange();
  signalerNouveauxEchanges();
  renderEchangeMien();""",
u"""// Les propositions seules, sans rien dessiner : le demarrage en a besoin pour
// la pastille de l'onglet et pour le panneau de la carte, bien avant que le
// joueur n'ouvre Echange.
async function chargerEchangesEnCours(){
  const { data, error } = await sb.rpc('mes_echanges');
  if(error){ console.warn('TERRAFRONT echanges indisponibles', error); return; }
  echangesEnCours = data || [];
  majBadgeEchange();
  signalerNouveauxEchanges();
}

async function loadEchanges(){
  await chargerEchangesEnCours();
  renderEchangePropositions();
  renderEchangeMien();""",
u'chargement des echanges separe du rendu')

js = rempl(js,
u"""  loadJournal();
  loadAmis();
  verifierVersion();""",
u"""  loadJournal();
  loadAmis();
  // la pastille de l'onglet Echange ne s'allumait qu'apres avoir ouvert
  // l'onglet : on ne savait qu'on avait une proposition qu'en allant voir
  chargerEchangesEnCours();
  verifierVersion();""",
u'les echanges charges au demarrage')

# --- 2. la bande dans le panneau de la carte -------------------------------
js = rempl(js,
u"""function ouvrirPanneau(code, xCss, yCss){""",
u"""// La proposition en attente qui concerne cette commune, s'il y en a une.
// Quatre situations, et elles ne se disent pas pareil : on te la demande, on
// te l'offre, tu l'as proposee, tu l'as demandee. Une seule phrase pour les
// quatre serait fausse trois fois.
function echangeSurCommune(code){
  for(const e of (echangesEnCours || [])){
    if(e.je_donne_code === code){
      return e.sens === 'recu'
        ? (e.autre_pseudo || 'Un joueur') + ' veut cette commune en échange'
        : 'Tu as proposé cette commune en échange';
    }
    if(e.je_recois_code === code){
      return e.sens === 'recu'
        ? (e.autre_pseudo || 'Un joueur') + ' te propose cette commune'
        : 'Tu as demandé cette commune en échange';
    }
  }
  return null;
}

function ouvrirPanneau(code, xCss, yCss){""",
u'echangeSurCommune')

js = rempl(js,
u"""    ${alerte}
    <div class="pc-lignes">""",
u"""    ${alerte}
    ${propose ? `<button class="pc-echange" data-pc="voir-echange">${ICONES_PC.echange}<span>${echapperHtml(propose)}</span><i>Voir</i></button>` : ''}
    <div class="pc-lignes">""",
u'la bande dans le panneau')

js = rempl(js,
u"""  let note = '';
  if(!mienne && protegee) note = 'Protégée par un bouclier : impossible de l’attaquer pour l’instant.';""",
u"""  const propose = echangeSurCommune(code);

  let note = '';
  if(!mienne && protegee) note = 'Protégée par un bouclier : impossible de l’attaquer pour l’instant.';""",
u'propose calcule avant le rendu')

# --- 3. le clic ------------------------------------------------------------
js = rempl(js,
u"""  if(quoi === 'attaque'){ ouvrirAttaque(code); return; }
  // les actions restantes quittent la carte pour l'onglet concerne""",
u"""  if(quoi === 'attaque'){ ouvrirAttaque(code); return; }
  if(quoi === 'voir-echange'){
    // les propositions sont listees en haut de l'onglet : inutile de remplir
    // une recherche, il n'y a rien a chercher
    fermerPanneau();
    const onglet = document.querySelector('.tab[data-tab="echange"]');
    if(onglet) onglet.click();
    return;
  }
  // les actions restantes quittent la carte pour l'onglet concerne""",
u'le clic sur la bande')

ecrire('app.js', js)


# ===========================================================================
#  style.css
# ===========================================================================
css = lire('style.css')

css = rempl(css,
u"""  .pc-alerte{""",
u"""  /* La bande des echanges proposes. Elle n'est pas rouge : ce n'est pas une
     alerte, c'est une proposition — et le rouge est deja pris par « on
     t'attaque », qui ne se confond avec rien. */
  .pc-echange{
    display:flex; align-items:center; gap:8px; width:100%;
    margin: 0 0 8px; padding: 8px 10px;
    border:1px solid rgba(143,179,255,0.38); border-radius:10px;
    background: rgba(143,179,255,0.12); color:#C9DBFF;
    font: inherit; font-size:0.82rem; text-align:left; cursor:pointer;
  }
  .pc-echange:hover{ background: rgba(143,179,255,0.2); }
  .pc-echange svg{ width:16px; height:16px; flex-shrink:0; }
  .pc-echange span{ flex:1; min-width:0; }
  .pc-echange i{
    flex-shrink:0; font-style:normal; font-weight:700; font-size:0.74rem;
    color:#8FB3FF; text-decoration:underline;
  }
  .pc-alerte{""",
u'style de la bande')

ecrire('style.css', css)
print(u'patch58 applique.')
