# patch424 (12/11/2026) : sur la carte, la fiche d'attaque décompte toute seule le délai avant le prochain assaut,
# comme l'onglet Attaquer (signalé par Oshannir : il fallait quitter la commune et y revenir). À zéro, la fiche se
# recharge (chances et série à jour) et le bouton « Lancer l'assaut » revient. Disparaît le 22/11 avec le siège.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'
if 'patch424' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')
rep(A, """      <button class="pc-action attaque" data-pc="assaut" ${attente > 0 || attaqueEnCours ? 'disabled' : ''}>""",
"""      <button class="pc-action attaque" data-pc="assaut" data-pc-fin="${attente > 0 ? prochain : ''}" ${attente > 0 || attaqueEnCours ? 'disabled' : ''}>""")
open(A, 'a', encoding='utf-8').write("""
// ---------- patch424 : sur la carte, le délai avant le prochain assaut se décompte tout seul (Oshannir) ----------
setInterval(() => {
  if(document.hidden) return;
  const b = document.querySelector('#mapPanneau .pc-action.attaque[data-pc-fin]');
  if(!b || !b.dataset.pcFin) return;
  const reste = Number(b.dataset.pcFin) - Date.now();
  if(reste > 0){
    const t = 'Encore ' + formatDuree(reste) + ' à attendre';
    if(b.textContent.trim() !== t) b.textContent = t;
    return;
  }
  b.dataset.pcFin = '';
  const code = rbDerniers && rbDerniers[0];
  if(attaqueEnCours || !code || code !== panneauCommune) return;
  ouvrirAttaque(code);   // à zéro : chances et série relues, le bouton revient
}, 1000);
""")
print('patch424 OK')
