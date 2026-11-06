# patch355 (6/11/2026) : joueurs bloqués au Front quand le pot est vide.
#
# Constat : un joueur qui avait encore des tirages payés (tirages_restants > 0)
# voyait le jeu lui représenter son paquet non ouvert (paquetEnCours = vrai).
# Or quand la roue du Front remplace les paquets (pot vide), la zone des
# paquets est cachée : le paquet est invisible, impossible de le déchirer,
# et le bouton Terra / Front refuse de changer de mode (« Un paquet est en
# cours »). Le joueur reste coincé au Front avec la roue.
#
# Correctif :
# 1. Tant que la roue remplace les paquets, le jeu ne représente plus un paquet
#    en attente (ni à l'arrivée, ni « Ouvrir le paquet suivant »). Les tirages
#    restent gardés sur le serveur : ils reviennent quand des communes
#    redeviennent libres.
# 2. Changer de mode n'est plus refusé si le paquet « en cours » est caché par
#    la roue : le paquet est rangé et on change de mode.
# 3. Quand la roue prend la place des paquets, un paquet en attente caché est
#    rangé tout de suite (le joueur n'a même pas à toucher au bouton).
# Rien d'autre ne change, aucun SQL.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch355' not in s, 'patch355 déjà appliqué'

# 1a. le paquet en attente, à l'arrivée
s = rep(s, "async function verifierTiragesEnAttente(){\n  if(paquetEnCours) return;\n",
           "async function verifierTiragesEnAttente(){\n  if(paquetEnCours) return;\n"
           "  if(typeof roueActive === 'function' && roueActive()) return;   // patch355 : la roue cache les paquets, les tirages restent gardés\n")
s = rep(s, "  // patch134 : un paquet a pu etre ouvert pendant qu'on interrogeait le serveur\n  if(paquetEnCours || tirageEnVol) return;\n",
           "  // patch134 : un paquet a pu etre ouvert pendant qu'on interrogeait le serveur\n  if(paquetEnCours || tirageEnVol) return;\n"
           "  if(typeof roueActive === 'function' && roueActive()) return;   // patch355\n")
# 1b. « Ouvrir le paquet suivant »
s = rep(s, "async function proposerPaquetSuivant(){\n  if(paquetEnCours) return;\n",
           "async function proposerPaquetSuivant(){\n  if(paquetEnCours) return;\n"
           "  if(typeof roueActive === 'function' && roueActive()) return;   // patch355\n")
# 2. le bouton Terra / Front
s = rep(s, "    if(paquetEnCours){ notifier({ type: 'info', titre: 'Un paquet est en cours', texte: 'Retourne tes cartes avant de changer de mode.' }); return; }",
           "    // patch355 : un paquet caché par la roue (pot vide) ne bloque plus : on le range\n"
           "    if(paquetEnCours && modeJeu === 'front' && typeof roueActive === 'function' && roueActive()\n"
           "       && !document.querySelector('#packZone .card, #packZone .ouv-pile')){\n"
           "      paquetEnCours = false;\n"
           "      const z = document.getElementById('packZone'); if(z) z.innerHTML = '';\n"
           "    }\n"
           "    if(paquetEnCours){ notifier({ type: 'info', titre: 'Un paquet est en cours', texte: 'Retourne tes cartes avant de changer de mode.' }); return; }")

# 3. quand la roue prend la place des paquets, un paquet en attente caché est rangé
s = rep(s, "  if(panel) panel.classList.toggle('roue-active', actif);\n",
           "  if(panel) panel.classList.toggle('roue-active', actif);\n"
           "  if(actif && paquetEnCours && !document.querySelector('#packZone .card, #packZone .ouv-pile')){   // patch355\n"
           "    paquetEnCours = false;\n"
           "    const z = document.getElementById('packZone'); if(z) z.innerHTML = '';\n"
           "  }\n")

F.write_text(s, encoding='utf-8')
print('patch355 appliqué')
