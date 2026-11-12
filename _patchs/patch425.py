# patch425 (12/11/2026) : échanges entre clans, un par joueur par jour au lieu d'un par semaine (avec s2-140).
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, I = 'app.js', 'index.html'
if 'patch425' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')
rep(I, "mais <b>un échange par semaine</b> par joueur, 2 propositions en attente au plus.</p><!-- patch341, patch398 -->",
       "mais <b>un échange par jour</b> par joueur, 2 propositions en attente au plus.</p><!-- patch341, patch398, patch425 -->")
rep(A, "`Un échange entre clans par semaine : le prochain le ${dispo.toLocaleDateString(", "`Un échange entre clans par jour : le prochain le ${dispo.toLocaleDateString(")
rep(A, "Proposer un échange <small>· 1 par semaine</small></button>", "Proposer un échange <small>· 1 par jour</small></button>")
rep(A, "Mêmes règles, mais <b>un échange par semaine</b>${clanEch.etat", "Mêmes règles, mais <b>un échange par jour</b>${clanEch.etat")
rep(A, "${echCarte.inter ? ' Un échange entre clans par semaine.' : ''}", "${echCarte.inter ? ' Un échange entre clans par jour.' : ''}")
open(A, 'a', encoding='utf-8').write("\n// patch425 : échanges entre clans, un par jour (s2-140)\n")
print('patch425 OK')
