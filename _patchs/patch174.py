# -*- coding: utf-8 -*-
u"""
patch174 — poser une garnison depuis Defendre (demande de Natael, 25 octobre).
Sous « Mes garnisons », tant qu'il reste une place : un champ pour chercher
une de ses communes du Front ; les plus rares d'abord, 6 resultats ; le
bouton « En garnison » pose comme la fiche de la carte (jusqu'a 5 energie).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)
js = lire('app.js')
assert 'gnRecherche' not in js, u'patch174 deja applique'
js = rempl(js, u"""    ${liste.length < 3 ? `<p class="gl-vide">${3 - liste.length} place${liste.length < 2 ? 's' : ''} libre${liste.length < 2 ? 's' : ''} : ouvre une de tes communes sur la carte et choisis « Mettre en garnison ».</p>` : ''}
    ${recits}`;
}""", u"""    ${liste.length < 3 ? `<p class="gl-vide">${3 - liste.length} place${liste.length < 2 ? 's' : ''} libre${liste.length < 2 ? 's' : ''} : choisis une de tes communes ci-dessous (ou depuis la carte).</p>
      <input type="search" class="bourse-search gn-cherche" id="gnCherche" placeholder="Chercher une de mes communes…" autocomplete="off" value="${echapperTexte(gnRecherche)}">
      <div class="gn-choix" id="gnChoix">${gnChoixHtml()}</div>` : ''}
    ${recits}`;
  const champ = document.getElementById('gnCherche');
  if(champ) champ.addEventListener('input', (e) => {
    gnRecherche = e.target.value;
    const z = document.getElementById('gnChoix'); if(z) z.innerHTML = gnChoixHtml();
  });
}
// patch174 : poser une garnison depuis Defendre
let gnRecherche = '';
function gnChoixHtml(){
  const q = sansAccents(gnRecherche.trim().toLowerCase());
  const rang = (t) => TIERS.findIndex(x => x.id === t.id);
  const mes = [...collectionMap.values()].filter(c => !garnisonsMoi.has(c.code)
    && (!q || sansAccents(c.nom.toLowerCase()).includes(q) || c.dept === q.toUpperCase()));
  mes.sort((a, b) => rang(a.tier) - rang(b.tier) || a.nom.localeCompare(b.nom, 'fr'));
  if(!mes.length) return `<p class="gl-vide">${collectionMap.size ? 'Aucune de tes communes ne correspond.' : 'Tu n\\'as pas encore de commune dans le Front.'}</p>`;
  return mes.slice(0, 6).map(c => `<div class="gl gn-ligne"><i class="gl-c ${c.tier.id}"></i><div class="gl-t"><b>${echapperTexte(c.nom)}</b>
      <span>${c.tier.label} · ${echapperTexte(DEPT_NAMES[c.dept] || c.dept)} (${echapperTexte(c.dept)})</span></div>
      <button class="gl-r gn-poser" data-gn-poser="${echapperTexte(c.code)}">En garnison</button></div>`).join('')
    + (mes.length > 6 ? `<p class="gl-vide">+ ${mes.length - 6} autre${mes.length - 6 > 1 ? 's' : ''} : affine la recherche.</p>` : '');
}""", 'bloc')
js = rempl(js, u"""      const b = e.target.closest('[data-gn-recharger]');
      if(b) garnisonAction(b.dataset.gnRecharger, 5);""", u"""      const b = e.target.closest('[data-gn-recharger]');
      if(b) garnisonAction(b.dataset.gnRecharger, 5);
      const p = e.target.closest('[data-gn-poser]');   // patch174
      if(p){
        p.disabled = true;
        const dispo = energieEtat ? Math.floor(energieEtat.energie) : 5;
        garnisonAction(p.dataset.gnPoser, Math.max(1, Math.min(5, dispo)));
      }""", 'clic')
ecrire('app.js', js)
css = lire('style.css')
css = rempl(css, u".gl-vide{ color:var(--brume); font-size:.78rem; padding:10px 0 2px; margin:0; }", u""".gl-vide{ color:var(--brume); font-size:.78rem; padding:10px 0 2px; margin:0; }
.gn-cherche{ width:100%; margin:10px 0 4px; }   /* patch174 */
.gl-r.gn-poser{ border-color: rgba(61,214,140,.5); background: rgba(61,214,140,.14); }""", 'css')
ecrire('style.css', css)
print(u'patch174 applique. Lancer : python3 maj-version.py')
