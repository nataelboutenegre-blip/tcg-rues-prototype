# patch463 : le paquet Département de la boutique ne propose plus les cantons (ni les provinces) :
# le serveur les refuse (boutique_ouvrir_paquet, s3-3 : « pas encore de paquet de canton »), le joueur
# recevait « Choisis d'abord un département ». Décision de Nataël du 19/11.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
p = os.path.join(R, 'app.js'); t = open(p, encoding='utf-8').read()
a = """      ? `<select class="bq-dep" id="bqDep" aria-label="Département"><option value="">Choisis un département${SUISSE ? ' ou un canton' : ''}</option>${
          (SUISSE   // patch332 : les cantons à part, sous « Suisse »
            ? '<optgroup label="France">' + deps.filter(d => !estEtrangerDep(d)).map(optDep).join('')
              + '</optgroup><optgroup label="Suisse">' + deps.filter(estCanton).map(d => `<option value="${d}">${d} · ${echapperTexte(DEPT_NAMES[d])}</option>`).join('') + '</optgroup>'
            : deps.map(optDep).join(''))}</select>` : '';"""
b = """      ? `<select class="bq-dep" id="bqDep" aria-label="Département"><option value="">Choisis un département</option>${
          deps.filter(d => !estEtrangerDep(d)).map(optDep).join('')}</select>` : '';   // patch463 : pas de canton ni de province (le serveur les refuse)"""
assert t.count(a) == 1, t.count(a)
open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print('app.js : ok')
