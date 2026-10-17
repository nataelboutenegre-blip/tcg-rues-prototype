# -*- coding: utf-8 -*-
u"""
patch136 — pas de requêtes quand le jeu n'est pas à l'écran (17 octobre).

Constat (Supabase, 17 octobre 19 h 51-20 h 51) : 8 454 requêtes en une heure ;
les trois premières sont des vérifications automatiques, toutes les minutes
et pour chaque joueur : mes_echanges (388), sieges_contre_moi (344),
sieges_communes (291). Elles tournent aussi quand le jeu est dans un onglet
caché ou un téléphone verrouillé, et la base est déjà à court de mémoire
(elle « swappe ») avec des pointes de CPU à 100 %.

Les vérifications régulières (grandes conquêtes, attaques contre moi,
échanges reçus, énergie, nouvelle version) ne partent plus quand la page est
cachée. Quand le joueur revient sur le jeu, elles partent une fois tout de
suite (au plus une fois toutes les 20 s), pour que tout soit à jour.
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
assert 'siVisible' not in js, u'patch136 deja applique'

js = rempl(js, u"""setInterval(surveillerGrandesConquetes, 60000);""", u"""// patch136 : une verification reguliere ne part que si le jeu est a l'ecran
const siVisible = (f) => () => { if(!document.hidden) f(); };
const VERIF_AU_RETOUR = [];
let dernierRetour = 0;
document.addEventListener('visibilitychange', () => {
  if(document.hidden || Date.now() - dernierRetour < 20000) return;
  dernierRetour = Date.now();
  VERIF_AU_RETOUR.forEach(f => { try{ f(); }catch(e){} });
});
VERIF_AU_RETOUR.push(surveillerGrandesConquetes);
setInterval(siVisible(surveillerGrandesConquetes), 60000);""", u'conquetes')

js = rempl(js, u"""    menacesInterval = setInterval(loadMenaces, 60000);
    // meme cadence pour les propositions d'echange recues
    echangesInterval = setInterval(loadBadgeEchanges, 60000);""", u"""    menacesInterval = setInterval(siVisible(loadMenaces), 60000);
    // meme cadence pour les propositions d'echange recues
    echangesInterval = setInterval(siVisible(loadBadgeEchanges), 60000);
    VERIF_AU_RETOUR.push(loadMenaces, loadBadgeEchanges);   // patch136""", u'menaces')

js = rempl(js, u"""  if(!energieTimer) energieTimer = setInterval(majEnergie, 60000);""",
u"""  if(!energieTimer){ energieTimer = setInterval(siVisible(majEnergie), 60000); VERIF_AU_RETOUR.push(majEnergie); }""", u'energie')

js = rempl(js, u"""setInterval(() => verifierVersion(), 30 * 60 * 1000);""",
u"""setInterval(siVisible(() => verifierVersion()), 30 * 60 * 1000);""", u'version')

ecrire('app.js', js)
print(u'patch136 applique')
