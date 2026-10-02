# -*- coding: utf-8 -*-
u"""
patch59 — variante B du panneau : l'info en haut, l'action avec les actions.

TA REMARQUE
  Mettre l'echange propose a cote d'Attaquer et de Proposer un echange,
  plutot qu'en bandeau tout en haut.

CE QUE JE RETIENS, ET CE QUE J'AJOUTE
  Tu as raison sur un point : un bouton n'a rien a faire dans la zone des
  informations. Mais l'information « Maroli veut cette commune » n'a rien a
  faire dans la zone des boutons non plus. Donc les deux se separent :

    — en haut, une simple ligne de texte, sans bordure ni fleche, qui dit
      laquelle des quatre situations ;
    — en bas, avec les autres actions, un bouton « Voir l'echange propose ».

  ET SURTOUT, ca corrige une impasse que j'avais laissee. Quand une commune
  est deja engagee dans une proposition, le bouton « Proposer un echange »
  menait nulle part : le serveur l'ecarte de la liste des communes
  echangeables, donc le joueur arrivait sur l'onglet Echange et ne la
  trouvait pas. Le bouton est maintenant REMPLACE par « Voir l'echange
  propose », qui mene la ou il y a quelque chose a faire.

  Trois boutons dont un en impasse, ca n'aurait pas ete mieux que deux.
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


js = lire('app.js')

# --- 1. propose se calcule avant les actions -------------------------------
js = rempl(js,
u"""  const actions = [];
  if(attaquable && !immunisee) actions.push(['attaque', 'attaque', 'Attaquer', 'Attaquer ' + c.nom]);
  if(!mienne) actions.push(['', 'echange', 'Proposer un échange', 'Échanger contre ' + c.nom]);""",
u"""  // une proposition en attente sur cette commune, s'il y en a une
  const propose = echangeSurCommune(code);

  const actions = [];
  if(attaquable && !immunisee) actions.push(['attaque', 'attaque', 'Attaquer', 'Attaquer ' + c.nom]);
  // Si une proposition est deja en attente, « Proposer un echange » menait
  // nulle part : le serveur ecarte les communes engagees de la liste des
  // echangeables, donc le joueur arrivait sur l'onglet et ne la trouvait pas.
  if(propose) actions.push(['', 'voir-echange', 'Voir l’échange proposé', 'Voir la proposition sur ' + c.nom]);
  else if(!mienne) actions.push(['', 'echange', 'Proposer un échange', 'Échanger contre ' + c.nom]);""",
u'le bouton remplace quand une proposition existe')

js = rempl(js,
u"""  const propose = echangeSurCommune(code);

  let note = '';""",
u"""  let note = '';""",
u'suppression du calcul en double')

# --- 2. en haut, une ligne de texte et non un bouton -----------------------
js = rempl(js,
u"""    ${propose ? `<button class="pc-echange" data-pc="voir-echange">${ICONES_PC.echange}<span>${echapperHtml(propose)}</span><i>Voir</i></button>` : ''}""",
u"""    ${propose ? `<p class="pc-propose">${ICONES_PC.echange}<span>${echapperHtml(propose)}</span></p>` : ''}""",
u'la bande devient une ligne')

# --- 3. l'icone du nouveau bouton ------------------------------------------
js = rempl(js,
u"""  joueur: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="3.4"/><path d="M5.5 20a6.5 6.5 0 0 1 13 0"/></svg>',
};""",
u"""  joueur: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="3.4"/><path d="M5.5 20a6.5 6.5 0 0 1 13 0"/></svg>',
};
// Voir une proposition et en faire une, c'est le meme objet vu des deux
// cotes : meme icone.
ICONES_PC['voir-echange'] = ICONES_PC.echange;""",
u"l'icone du bouton voir-echange")

ecrire('app.js', js)


css = lire('style.css')

css = rempl(css,
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
  }""",
u"""  /* L'echange propose : une information, donc une ligne de texte, sans
     bordure ni bouton — l'action correspondante est en bas avec les autres.
     Bleue et non rouge : le rouge est pris par « on t'attaque », qui ne doit
     se confondre avec rien. */
  .pc-propose{
    display:flex; align-items:center; gap:7px;
    margin: 0 0 8px; padding: 0 2px;
    color:#9FBEF5; font-size:0.8rem; line-height:1.35;
  }
  .pc-propose svg{ width:15px; height:15px; flex-shrink:0; }""",
u'style de la ligne')

ecrire('style.css', css)
print(u'patch59 applique.')
