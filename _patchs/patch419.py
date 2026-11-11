# patch419 (11/11/2026) : l'annonce des récompenses de fin de saison 2
# Bandeau « Fin de la saison 2 dimanche 22/11 à 10 h · Les récompenses » sous le titre du classement (Front et Clans),
# jusqu'à la clôture ; il ouvre la fiche des récompenses (podium et top 10, clan champion, 13 distinctions,
# seigneurs de territoire, Pionnier du Front + 1 paquet Terra). Décisions de Nataël du 11/11 (« les 5 », annonce maintenant).
# L'attribution se fera à la clôture (script à part).
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, C = 'app.js', 'style.css'
if 'patch419' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')
rep(A, """  bloc.hidden = false;
  bloc.classList.toggle('replie', !classementOuvert);""", """  bloc.hidden = false;
  bloc.classList.toggle('replie', !classementOuvert);
  if(typeof rs2Bandeau === 'function') rs2Bandeau();   // patch419""")
open(A, 'a', encoding='utf-8').write(open('_patchs/patch419-recompenses.js', encoding='utf-8').read())
open(C, 'a', encoding='utf-8').write(open('_patchs/patch419-recompenses.css', encoding='utf-8').read())
print('patch419 OK')
