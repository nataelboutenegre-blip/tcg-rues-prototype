# patch409 (11/11/2026) : Attaquer, « Meilleures chances » avec trop de cibles (bug signalé par Arkhannou)
# Avant : au-delà de TRI_MAX (4 000) cibles, rien n'était trié, le bouton restait allumé et une note discrète l'expliquait.
# Maintenant : les 4 000 cibles les plus proches de mon territoire sont triées par chance, les autres suivent par distance,
# et la note le dit (« Trié parmi les 4 000 cibles les plus proches… »).
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'
if 'patch409' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')

rep(A, """  if(!combatEnCours && (triChances || combatProximite) && cibles.length){
    const codes = cibles.map(c => c.commune_code);
    if(codes.length > TRI_MAX){""",
"""  if(!combatEnCours && (triChances || combatProximite) && cibles.length){
    let codes = cibles.map(c => c.commune_code);
    let reste = [];   // patch409 : trop de cibles, on trie les plus proches, le reste suit par distance
    if(codes.length > TRI_MAX && triChances){
      const dk = (c) => (c._distKm == null ? 1e9 : c._distKm);
      const parDist = cibles.slice().sort((a, b) => dk(a) - dk(b));
      reste = parDist.slice(TRI_MAX);
      cibles = parDist.slice(0, TRI_MAX);
      codes = cibles.map(c => c.commune_code);
      triMajBoutons(true, codes.length + reste.length);
    }
    if(codes.length > TRI_MAX){""")
rep(A, """      cibles = cibles.slice().sort((a, b) => ch(b) - ch(a)
        || (combatProximite ? dist(a) - dist(b) : 0)
        || rang(a) - rang(b) || String(a.communes.nom).localeCompare(String(b.communes.nom), 'fr'));
    }""",
"""      cibles = cibles.slice().sort((a, b) => ch(b) - ch(a)
        || (combatProximite ? dist(a) - dist(b) : 0)
        || rang(a) - rang(b) || String(a.communes.nom).localeCompare(String(b.communes.nom), 'fr'));
      if(reste.length) cibles = cibles.concat(reste);   // patch409
    }""")
rep(A, """function triMajBoutons(trop){
  document.querySelectorAll('#combatTri [data-tri]').forEach(b => {
    const on = (b.dataset.tri === 'chances') === triChances;
    b.classList.toggle('active', on); b.setAttribute('aria-pressed', String(on));
  });
  const n = document.getElementById('combatTriNote');
  if(n){ n.hidden = !trop; n.textContent = trop ? 'Trop de cibles pour les trier toutes : choisis une rareté, un département ou « Près de mon territoire ».' : ''; }
}""",
"""function triMajBoutons(trop, total){
  document.querySelectorAll('#combatTri [data-tri]').forEach(b => {
    const on = (b.dataset.tri === 'chances') === triChances;
    b.classList.toggle('active', on); b.setAttribute('aria-pressed', String(on));
  });
  const n = document.getElementById('combatTriNote');
  // patch409 : on trie quand même les plus proches
  if(n){ n.hidden = !trop; n.textContent = trop ? `Trié parmi les ${TRI_MAX.toLocaleString('fr-FR')} cibles les plus proches de ton territoire (sur ${(total || 0).toLocaleString('fr-FR')}). Pour tout trier, choisis une rareté, un département ou « Près de mon territoire ».` : ''; }
}""")
print('patch409 OK')
