# -*- coding: utf-8 -*-
u"""
patch123 — le paquet prêt appelle le clic, le bouton s'efface (idée de Nataël).

1. Quand un paquet gratuit attend dans l'onglet Tirage, il « appelle » toutes
   les 4,5 s : il se soulève, se dandine, un reflet balaie le paquet et le
   trait doré parcourt les pointillés (le même que celui du survol).
   L'appel s'arrête dès qu'on survole ou touche le paquet. Coupé si le
   réglage Animation est éteint ou si l'appareil demande moins de mouvement.
2. Tant que ce paquet est affiché, « Ouvrir un paquet gratuit » est grisé
   (le paquet lui-même est le bouton) : plus deux façons de faire la même
   chose. Info-bulle : « Touche le paquet ci-dessous ».
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
assert 'paquetPretAffiche' not in js, u'patch123 deja applique'

# 1. le paquet pret appelle le clic
js = rempl(js, u"""  pack.dataset.pret = '1';
  pack.setAttribute('aria-label', 'Ouvrir un paquet gratuit');""", u"""  pack.dataset.pret = '1';
  pack.setAttribute('aria-label', 'Ouvrir un paquet gratuit');
  // patch123 : il appelle le clic, jusqu'au premier survol ou toucher
  if(ouvAnim){
    pack.classList.add('appel');
    const calmer = () => pack.classList.remove('appel');
    pack.addEventListener('pointerenter', calmer, { once: true });
    pack.addEventListener('pointerdown', calmer, { once: true });
  }""", u'appel')

# 2. le bouton s'efface tant que le paquet est la
js = rempl(js, u"""  dispoPrecedente = dispo;
  majPaquetPret(dispo);
}""", u"""  dispoPrecedente = dispo;
  majPaquetPret(dispo);
  // patch123 : le paquet affiche est le bouton ; pas deux facons de faire la meme chose
  const bouton = document.getElementById('openFreeBtn');
  if(paquetPretAffiche()){
    bouton.disabled = true;
    bouton.title = 'Touche le paquet ci-dessous';
  } else bouton.removeAttribute('title');
}
function paquetPretAffiche(){
  return !!document.querySelector('#packZone .paquet[data-pret]');
}""", u'bouton')

css += u"""
/* ---------- patch123 : le paquet pret appelle le clic ---------- */
.paquet.appel:not(.charge):not(.coupe):not(.dechire){ animation: paquetAppel 4.5s ease-in-out .8s infinite; }
.paquet.appel:not(.charge):not(.coupe):not(.dechire) .perfo-masque{ animation: perfoAppel 4.5s ease-in-out .8s infinite; transition:none; }
.paquet.appel:not(.charge):not(.coupe):not(.dechire) .paquet-corps::after{ animation: refletAppel 4.5s ease-in-out .8s infinite; transition:none; }
@keyframes paquetAppel{
  0%, 30%, 100%{ transform:none; filter:none; }
  6%{ transform:translateY(-8px) rotate(-2deg); filter:drop-shadow(0 10px 18px rgba(240,180,41,.35)); }
  10%{ transform:translateY(-8px) rotate(2deg); }
  14%{ transform:translateY(-8px) rotate(-1.5deg); }
  18%{ transform:translateY(-8px) rotate(0); filter:drop-shadow(0 10px 18px rgba(240,180,41,.35)); }
}
@keyframes perfoAppel{ 0%, 16%{ width:0; opacity:1; } 34%{ width:188px; opacity:1; } 48%, 100%{ width:188px; opacity:0; } }
@keyframes refletAppel{ 0%, 14%{ background-position:110% 0; } 32%, 100%{ background-position:-10% 0; } }
@media (prefers-reduced-motion: reduce){ .paquet.appel, .paquet.appel .perfo-masque, .paquet.appel .paquet-corps::after{ animation:none !important; } }
"""

ecrire('app.js', js)
ecrire('style.css', css)
print(u'patch123 applique')
