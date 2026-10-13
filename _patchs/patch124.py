# -*- coding: utf-8 -*-
u"""
patch124 — l'appel du paquet, corrigé (signalé par Nataël : « aucune animation »).

Deux causes possibles, corrigées toutes les deux :
1. patch123 n'animait que le paquet gratuit posé (data-pret). Le paquet
   « non ouvert » qu'on retrouve en arrivant (payé ou tiré mais pas encore
   déchiré : afficherPaquetATirer) n'avait rien. Il appelle maintenant aussi.
2. Le simple passage de la souris arrêtait l'appel pour toujours : sur
   ordinateur, il suffisait de survoler le paquet une fois pour ne plus
   jamais le voir bouger. Le survol met maintenant l'appel en pause ; seul le
   toucher (ou le clic) l'arrête.
Toujours coupé si le réglage Animation est éteint ou si l'appareil demande
moins de mouvement.
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

js = lire('app.js')
css = lire('style.css')
assert 'appelerPaquet' not in js, u'patch124 deja applique'

# une seule fonction pour les deux paquets
js = rempl(js, u"""  // patch123 : il appelle le clic, jusqu'au premier survol ou toucher
  if(ouvAnim){
    pack.classList.add('appel');
    const calmer = () => pack.classList.remove('appel');
    pack.addEventListener('pointerenter', calmer, { once: true });
    pack.addEventListener('pointerdown', calmer, { once: true });
  }""", u"""  appelerPaquet(pack);""", u'appel pret')

js = rempl(js, u"""  const pack = makePackEl(type);
  sceneOuverture(zone).echelle.appendChild(pack);
  armerPaquet(pack, () => tirerCartesDuPaquet(nbCartes));   // patch87
}""", u"""  const pack = makePackEl(type);
  sceneOuverture(zone).echelle.appendChild(pack);
  appelerPaquet(pack);   // patch124 : le paquet non ouvert appelle aussi
  armerPaquet(pack, () => tirerCartesDuPaquet(nbCartes));   // patch87
}

// patch123/124 : le paquet appelle le clic. Le survol le met en pause (CSS),
// le toucher ou le clic l'arrete.
function appelerPaquet(pack){
  if(!ouvAnim || REDUCED_MOTION) return;
  pack.classList.add('appel');
  pack.addEventListener('pointerdown', () => pack.classList.remove('appel'), { once: true });
}""", u'appel a tirer')

css += u"""
/* patch124 : le survol met l'appel en pause au lieu de l'arreter */
@media (hover: hover){
  .paquet.appel:hover, .paquet.appel:hover .perfo-masque, .paquet.appel:hover .paquet-corps::after{ animation-play-state: paused; }
}
"""

ecrire('app.js', js)
ecrire('style.css', css)
print(u'patch124 applique')
