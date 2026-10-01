# -*- coding: utf-8 -*-
u"""
patch55 — L'ordre des onglets sur ordinateur.

L'ORDRE DEMANDE
  Tirage · Territoire · Collection · Monuments · Combat · Defense ·
  Contrat · Bourse · Echange · Profil · Communaute · Succes

  Il n'est pas arbitraire, et c'est pour ca qu'il est meilleur que l'ancien :
  il suit ce qu'on fait, dans l'ordre ou on le fait.
    — on obtient      : Tirage, Territoire, Collection, Monuments
    — on se bat       : Combat, Defense
    — on transforme   : Contrat, Bourse, Echange
    — on fait le point: Profil, Communaute, Succes

  L'ancien ordre melangeait les trois : la Bourse etait coincee entre la
  Communaute et le Combat, et Monuments se retrouvait en dernier parce qu'il
  venait d'etre ajoute.

COMMENT C'EST FAIT
  Le script ne deplace pas du texte a la main : il decoupe les douze blocs
  d'onglet, verifie qu'il les a bien tous les douze et qu'aucun ne manque a
  l'appel, puis les recolle dans l'ordre voulu. Si un onglet etait ajoute ou
  renomme entre-temps, le script s'arreterait au lieu d'en perdre un.

DEUX CHOSES QUE LA REORGANISATION A FAIT APPARAITRE

  Les quatre groupes etaient invisibles : douze lignes a intervalle egal, et
  l'oeil n'y voit aucune logique. Trois respirations les separent maintenant
  — rien d'autre, pas de trait, pas de titre. Sur telephone la barre du bas
  est une rangee, donc la regle ne vaut que pour la colonne.

  Bourse et Echange portaient exactement la meme icone, deux fleches. Ca ne
  se voyait pas tant qu'elles etaient eloignees ; cote a cote, c'est le
  premier defaut qu'on remarque. Les fleches restent a Echange, qui est bien
  un troc entre joueurs ; la Bourse prend une etiquette de prix, qui dit
  qu'on achete.

LE TELEPHONE
  La barre du bas ne change pas : elle garde Tirage, Collection, Combat,
  Defense et le bouton Plus, comme avant. Mais le menu Plus suit desormais
  le meme ordre que la colonne de l'ordinateur — deux ordres differents pour
  les memes entrees, c'etait une raison de se tromper pour rien.
"""
import io, os, re

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


ORDRE = ['tirage', 'territoire', 'collection', 'monuments', 'combat', 'defense',
         'contrat', 'bourse', 'echange', 'profil', 'communaute', 'succes']


# ===========================================================================
#  index.html — on recolle les blocs dans l'ordre
# ===========================================================================
html = lire('index.html')

# --- l'icone de la Bourse ---------------------------------------------------
html = rempl(html,
u"""      <div class="tab" data-tab="bourse">
        <div class="icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
            <path d="M4 8h13M17 8l-3-3M17 8l-3 3"/>
            <path d="M20 16H7M7 16l3-3M7 16l3 3"/>
          </svg>
        </div>
        Bourse""",
u"""      <div class="tab" data-tab="bourse">
        <div class="icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3.5 12.6V5.2a1.7 1.7 0 0 1 1.7-1.7h7.4l7.9 7.9a1.7 1.7 0 0 1 0 2.4l-7.4 7.4a1.7 1.7 0 0 1-2.4 0z"/>
            <circle cx="8.2" cy="8.2" r="1.5"/>
          </svg>
        </div>
        Bourse""",
u"l'etiquette de prix de la Bourse")


DEBUT = u'<div class="tabs-row" id="tabsRow">\n'
FIN = u'      <button class="tab tab-plus" id="btnPlus"'
i = html.index(DEBUT) + len(DEBUT)
j = html.index(FIN)
zone = html[i:j]

# un bloc = l'ouverture a six espaces jusqu'a la fermeture a six espaces ;
# le <div class="icon"> interieur est a huit, il n'est donc jamais confondu
MOTIF = re.compile(u'      <div class="tab[^"]*" data-tab="(\\w+)">.*?\n      </div>\n',
                   re.S)
blocs = {}
for m in MOTIF.finditer(zone):
    blocs[m.group(1)] = m.group(0)

assert len(blocs) == len(ORDRE), \
    u'%d onglets trouves, %d attendus : %s' % (len(blocs), len(ORDRE), sorted(blocs))
manquants = [o for o in ORDRE if o not in blocs]
assert not manquants, u'onglets introuvables : %s' % manquants
# rien d'autre que les blocs dans la zone (hors lignes vides)
reste = MOTIF.sub(u'', zone).strip()
assert reste == u'', u'du contenu inattendu entre les onglets : %r' % reste[:200]

# l'onglet actif au chargement est le premier affiche : on retire la classe
# partout et on la repose sur celui qui ouvre le jeu
nouveau = u''
for n, cle in enumerate(ORDRE):
    b = blocs[cle].replace(u'<div class="tab active" ', u'<div class="tab" ')
    if n == 0:
        b = b.replace(u'<div class="tab" ', u'<div class="tab active" ')
    nouveau += b + (u'\n' if n < len(ORDRE) - 1 else u'')

html = html[:i] + nouveau + html[j:]
assert html.count(u'data-tab="') >= len(ORDRE), u'des onglets ont disparu'
ecrire('index.html', html)


# ===========================================================================
#  app.js — le menu Plus suit le meme ordre
# ===========================================================================
js = lire('app.js')

js = rempl(js,
u"""const ONGLETS_MENU = ['territoire', 'communaute', 'bourse', 'echange', 'contrat', 'succes', 'monuments', 'profil'];""",
u"""// Meme ordre que la colonne de l'ordinateur, moins les quatre de la barre du
// bas : deux ordres differents pour les memes entrees, c'etait une raison de
// se tromper pour rien.
const ONGLETS_MENU = ['territoire', 'monuments', 'contrat', 'bourse', 'echange', 'profil', 'communaute', 'succes'];""",
u'ordre du menu Plus')

ecrire('app.js', js)


# ===========================================================================
#  style.css — les respirations entre groupes
# ===========================================================================
css = lire('style.css')

# La regle vit dans sa propre media query plutot que d'etre annulee plus loin :
# une annulation posee avant, a specificite egale, serait perdue par l'ordre du
# fichier — c'est exactement ce qui m'avait fait rater le 16 px d'iOS.
css += (
u"""
  /* ---------- Les quatre groupes de la colonne ----------
     Douze onglets a intervalle egal, et l'oeil n'y voit aucune logique.
     Trois respirations suffisent a montrer le decoupage : on obtient, on se
     bat, on transforme, on fait le point. Pas de trait ni de titre — il n'y
     a rien a lire, juste a sentir. Sur telephone la barre du bas est une
     rangee : la regle ne s'y applique jamais. */
  @media (min-width: 721px){
    .tab[data-tab="combat"],
    .tab[data-tab="contrat"],
    .tab[data-tab="profil"]{ margin-top: 14px; }
  }
""")

ecrire('style.css', css)
print(u'patch55 applique : ' + u' · '.join(ORDRE))
