# -*- coding: utf-8 -*-
u"""
patch51 — Les deux bandeaux de la Collection se ferment.

LE PROBLEME
  Le rappel du Contrat et la barre des cinq communes gardees occupent
  ensemble presque un tiers de l'ecran sur telephone, au-dessus de la
  grille. Un joueur qui a compris le message les subit a chaque visite.

CE QUE JE N'AI PAS FAIT
  Une fermeture definitive. Un bandeau qu'on ferme une fois et qu'on ne
  revoit jamais finit par manquer : le joueur qui ferme « 3 / 5 » en
  septembre ne saura pas, en novembre, qu'il en est a 4.

CE QUE J'AI FAIT
  La fermeture retient la SITUATION, pas le bandeau. Tant que rien ne
  change, il reste ferme. Des que la situation evolue, il revient une fois.

    — Contrat : revient quand le joueur passe un palier de dix de plus,
      donc quand il peut signer un contrat de plus qu'avant.
    — Cinq gardees : revient quand le nombre d'etoiles change.

  C'est ce qui donne un bandeau qu'on ferme sans le perdre : il ne parle
  que quand il a quelque chose de neuf a dire.

OU C'EST GARDE
  Dans le navigateur, par joueur. Changer d'appareil remet les bandeaux,
  ce qui est le bon defaut : mieux vaut les revoir une fois de trop que
  rater sa saison.
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
#  index.html — les deux croix
# ===========================================================================
html = lire('index.html')

html = rempl(html,
u"""          <button class="ct-rappel-b" id="ctRappelB">Voir</button>""",
u"""          <button class="ct-rappel-b" id="ctRappelB">Voir</button>
          <button class="bandeau-fermer" id="ctRappelX" aria-label="Masquer ce rappel" title="Masquer">&#10005;</button>""",
u'croix du rappel contrat')

html = rempl(html,
u"""          <span class="fav-txt" id="favTxt"></span>
        </div>""",
u"""          <span class="fav-txt" id="favTxt"></span>
          <button class="bandeau-fermer" id="favBarreX" aria-label="Masquer ce rappel" title="Masquer">&#10005;</button>
        </div>""",
u'croix de la barre des favoris')

ecrire('index.html', html)


# ===========================================================================
#  app.js
# ===========================================================================
js = lire('app.js')

# --- le mecanisme ----------------------------------------------------------
js = rempl(js,
u"""// Le rappel en haut de la Collection. C'est la porte d'entree : un onglet
// dans « Plus » ne se trouve pas tout seul.""",
u"""// ---------- Bandeaux qu'on peut fermer ----------
// Fermer ne fait pas taire le bandeau pour toujours : on retient la
// SITUATION au moment de la fermeture. Tant qu'elle ne change pas, il reste
// ferme ; des qu'elle change, il revient une fois. Un rappel qu'on ferme
// definitivement finit par manquer, un rappel qui revient a chaque visite
// finit par etre ignore — celui-ci ne parle que s'il a du neuf a dire.
function cleBandeau(id){
  return 'tf-bandeau-' + id + '-' + (ID_MOI || 'anon');
}

function bandeauMasque(id, signature){
  try{ return localStorage.getItem(cleBandeau(id)) === String(signature); }
  catch(e){ return false; }   // navigation privee : le bandeau s'affiche, tant pis
}

function masquerBandeau(id, signature, element){
  try{ localStorage.setItem(cleBandeau(id), String(signature)); }catch(e){}
  if(element) element.hidden = true;
}

// Le rappel en haut de la Collection. C'est la porte d'entree : un onglet
// dans « Plus » ne se trouve pas tout seul.""",
u'mecanisme des bandeaux fermables')

# --- rappel contrat --------------------------------------------------------
js = rempl(js,
u"""  const c = CONTRATS.find(x => (parTier[x.de] || 0) >= x.n);
  if(!c){ bloc.hidden = true; return; }
  const n = parTier[c.de];
  bloc.hidden = false;""",
u"""  const c = CONTRATS.find(x => (parTier[x.de] || 0) >= x.n);
  if(!c){ bloc.hidden = true; return; }
  const n = parTier[c.de];
  // la situation, c'est le nombre de contrats signables : le rappel revient
  // quand le joueur peut en signer un de plus qu'au moment ou il l'a ferme
  bloc.dataset.signature = c.de + ':' + Math.floor(n / c.n);
  if(bandeauMasque('contrat', bloc.dataset.signature)){ bloc.hidden = true; return; }
  bloc.hidden = false;""",
u'signature du rappel contrat')

# --- barre des favoris -----------------------------------------------------
js = rempl(js,
u"""  if(!favorisCharges || vueCollection === 'france'){ barre.hidden = true; return; }
  barre.hidden = false;
  const n = favorisSet.size;""",
u"""  if(!favorisCharges || vueCollection === 'france'){ barre.hidden = true; return; }
  const n = favorisSet.size;
  // la situation, c'est le nombre d'etoiles posees
  barre.dataset.signature = String(n);
  if(bandeauMasque('favoris', barre.dataset.signature)){ barre.hidden = true; return; }
  barre.hidden = false;""",
u'signature de la barre des favoris')

# --- les deux boutons ------------------------------------------------------
js = rempl(js,
u"""document.getElementById('ctRappelB').addEventListener('click', () => {""",
u"""document.getElementById('ctRappelX').addEventListener('click', () => {
  const bloc = document.getElementById('ctRappel');
  masquerBandeau('contrat', bloc.dataset.signature, bloc);
});
document.getElementById('favBarreX').addEventListener('click', () => {
  const barre = document.getElementById('favBarre');
  masquerBandeau('favoris', barre.dataset.signature, barre);
});

document.getElementById('ctRappelB').addEventListener('click', () => {""",
u'les deux boutons de fermeture')

ecrire('app.js', js)


# ===========================================================================
#  style.css
# ===========================================================================
css = lire('style.css')

css = rempl(css,
u"""  .fav-barre[hidden]{ display:none; }""",
u"""  .fav-barre[hidden]{ display:none; }

  /* La croix des bandeaux. Discrete au repos — elle ne doit pas attirer
     l'oeil plus que le message — mais 30 px de zone touchable, soit de quoi
     la viser au pouce sans zoomer. */
  /* En coin, hors du flux : la barre des favoris passe a la ligne quand elle
     est etroite, et un bouton dans le flux y creait une rangee vide — le
     bandeau devenait plus haut qu'avant au lieu de se faire oublier. */
  .ct-rappel, .fav-barre{ position:relative; padding-right:38px; }
  .bandeau-fermer{
    position:absolute; top:4px; right:4px;
    width:30px; height:30px; padding:0; border:0; background:none; cursor:pointer;
    color: var(--brume); opacity:0.45; font-size:0.9rem; line-height:1;
    border-radius:8px; transition: opacity .15s, background .15s;
  }
  .bandeau-fermer:hover, .bandeau-fermer:focus-visible{
    opacity:1; background: rgba(169,188,212,0.12);
  }""",
u'style de la croix')

ecrire('style.css', css)
print(u'patch51 applique.')
