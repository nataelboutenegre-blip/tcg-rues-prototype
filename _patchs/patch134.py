# -*- coding: utf-8 -*-
u"""
patch134 — un paquet ne peut plus être tiré deux fois en même temps
(signalé par Oshannir le 14 octobre : « arnaque », 3 cartes affichées).

Constat : le serveur lui a bien donné 5 cartes, à 0,1 s d'écart, mais
l'écran n'en a montré que 3, une sur deux (1re, 3e, 5e). Deux tirages
tournaient en même temps sur son écran et se partageaient les 5 cartes ;
chacun s'est arrêté quand il n'y en avait plus. Les 2 autres cartes sont
dans sa collection.

1. tirerCartesDuPaquet ne lance jamais deux tirages à la fois : un second
   appel reçoit la réponse du premier, sans rien tirer de plus.
2. verifierTiragesEnAttente regarde de nouveau s'il y a un paquet en cours
   APRÈS avoir interrogé le serveur (elle ne le vérifiait qu'avant : si le
   joueur ouvrait un paquet pendant ce temps, elle posait un second paquet
   par-dessus celui en cours d'ouverture).
3. Si un tirage s'arrête, le message dit maintenant que les cartes déjà
   tirées sont dans la collection.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)
js = lire('app.js')
assert 'tirageEnVol' not in js, u'patch134 deja applique'

js = rempl(js, u"""// Les cinq tirages, l'un apres l'autre, avec la gestion d'erreur d'origine.
async function tirerCartesDuPaquet(nbCartes){
  if(enTerra()) return tirerPaquetTerra();""", u"""// patch134 : un seul tirage a la fois. Deux tirages simultanes se
// partageaient les cartes du paquet et chacun n'en montrait qu'une partie.
let tirageEnVol = null;
function tirerCartesDuPaquet(nbCartes){
  if(tirageEnVol) return tirageEnVol;
  tirageEnVol = tirerCartesDuPaquetSeul(nbCartes).finally(() => { tirageEnVol = null; });
  return tirageEnVol;
}

// Les cinq tirages, l'un apres l'autre, avec la gestion d'erreur d'origine.
async function tirerCartesDuPaquetSeul(nbCartes){
  if(enTerra()) return tirerPaquetTerra();""", u'verrou')

js = rempl(js, u"""  const data = await monEtat();
  if(!data || !(data.tirages_restants > 0)) return;
  paquetEnCours = true;
  renderPackStatus();
  afficherPaquetATirer('gratuit', Math.min(5, data.tirages_restants));""", u"""  const data = await monEtat();
  if(!data || !(data.tirages_restants > 0)) return;
  // patch134 : un paquet a pu etre ouvert pendant qu'on interrogeait le serveur
  if(paquetEnCours || tirageEnVol) return;
  paquetEnCours = true;
  renderPackStatus();
  afficherPaquetATirer('gratuit', Math.min(5, data.tirages_restants));""", u'attente')

js = rempl(js, u"""        notifier({ type: 'erreur', titre: 'Tirage interrompu', texte: messageLisible(error.message) });""",
u"""        notifier({ type: 'erreur', titre: 'Tirage interrompu',
                   texte: messageLisible(error.message) + (i > 0 ? ` Les ${i} carte${i > 1 ? 's' : ''} déjà tirée${i > 1 ? 's sont' : ' est'} dans ta collection.` : '') });""", u'message')

ecrire('app.js', js)
print(u'patch134 applique')
