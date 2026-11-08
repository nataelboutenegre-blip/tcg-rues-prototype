# patch383 : la bulle d'un département au survol (ordinateur) montre aussi le nombre de communes
# (Oshannir, #bugs 8/11 18 h 50 : « moi je vois des % pas des chiffres »). La fiche au toucher
# les montrait déjà (« 8,3 % · 42 ») ; la bulle n'avait que les pourcentages.
# Le titre donne aussi le total de communes du département.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
s = rep(s, """        const s = statsDepartement(dep);
        bulle.dataset.dep = dep;
        bulle.classList.add('dept');
        bulle.innerHTML = `<b class="ib-titre">${echapperHtml(DEPT_NAMES[dep] || dep)} (${echapperHtml(dep)})</b>`
          + lignesDept(s).map(j => `<span class="ib-j${j.moi ? ' moi' : ''}"><i style="background:${j.couleur}"></i>${echapperHtml(j.pseudo)}<em>${partDept(j.n, s.total)}</em></span>`).join('')
          + `<span class="ib-libre">Libres<em>${partDept(s.total - s.pris, s.total)}</em></span>`
          + (CALQUES.couleur === 'raretes' ? `<span class="ib-rar">${rarDeptTexte(dep)}</span>` : '');   // patch294""", """        bulle.dataset.dep = dep;
        bulle.classList.add('dept');
        bulle.innerHTML = bulleDeptHtml(dep);   // patch383""")
s = rep(s, """function brancherSurvolCanvas(){""", """// patch383 : la bulle d'un département, avec le nombre de communes à côté du pourcentage
function bulleDeptHtml(dep){
  const s = statsDepartement(dep);
  const n = (x) => `<small>· ${nbFr(x)}</small>`;
  return `<b class="ib-titre">${echapperHtml(DEPT_NAMES[dep] || dep)} (${echapperHtml(dep)})<small>${nbFr(s.total)} communes</small></b>`
    + lignesDept(s).map(j => `<span class="ib-j${j.moi ? ' moi' : ''}"><i style="background:${j.couleur}"></i>${echapperHtml(j.pseudo)}<em>${partDept(j.n, s.total)} ${n(j.n)}</em></span>`).join('')
    + `<span class="ib-libre">Libres<em>${partDept(s.total - s.pris, s.total)} ${n(s.total - s.pris)}</em></span>`
    + (CALQUES.couleur === 'raretes' ? `<span class="ib-rar">${rarDeptTexte(dep)}</span>` : '');   // patch294
}

function brancherSurvolCanvas(){""")
F.write_text(s, encoding='utf-8')

C = pathlib.Path('style.css'); c = C.read_text(encoding='utf-8')
assert 'patch383' not in c
c += """
/* patch383 : le nombre de communes dans la bulle d'un département */
.map-infobulle em small{ font-weight:400; color:#8FA4BF; margin-left:2px; }
.map-infobulle .ib-titre small{ display:block; font-weight:500; font-size:.7rem; color:#8FA4BF; margin-top:1px; }
"""
C.write_text(c, encoding='utf-8')
print('patch383 ok')
