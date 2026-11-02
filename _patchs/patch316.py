# patch316 : deux idées d'Arkhannou (aperçu validé le 2/11)
#  1. Survoler ou toucher le numéro d'un département (partout où badgeDept l'affiche)
#     montre la France avec ce département en or, son nom et sa région.
#  2. Sur la fiche d'une commune d'un membre du clan, un bouton « Proposer un échange
#     à X » ouvre Clan › Échanges avec ce coéquipier et cette commune déjà choisis.
import pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch316' not in s

# 1. le badge porte son département
s = rep(s, """  return `<span class="dep"${nom ? ` title="${echapperTexte(nom)}"` : ''}>${echapperTexte(d)}</span>`;""",
           """  return `<span class="dep" data-dep="${echapperTexte(d)}">${echapperTexte(d)}</span>`;   // patch316 : la bulle remplace le title""")

# 2. la fiche d'une commune du clan
s = rep(s, """  if(allie) note = 'Commune d’un membre de ton clan : vous ne pouvez pas vous attaquer.';   // patch268""",
           """  if(allie) note = 'Vous êtes dans le même clan : pas d’attaque entre vous.';   // patch268   // patch316
  let echClan = '';   // patch316 : proposer un échange au coéquipier
  if(allie && enFrontClan()){
    const e = clanEch.etat;
    const raison = !e ? '' : e.pret_le ? 'Échanges possibles 48 h après ton arrivée dans le clan'
      : Math.max(0, (e.max || 3) - (e.faits || 0)) === 0 ? 'Plus d’échange possible aujourd’hui' : '';
    echClan = `<button class="pc-action pc-ech-clan" data-pc="ech-clan"${raison ? ` disabled title="${echapperHtml(raison)}"` : ''}>🤝 Proposer un échange à ${echapperHtml(c.pseudo || 'ton coéquipier')}</button>${raison ? `<p class="pc-note">${echapperHtml(raison)}.</p>` : ''}`;
  }""")
s = rep(s, """    ${note ? `<p class="pc-note">${note}</p>` : ''}
    ${actions.length ? `<div class="pc-actions">""", """    ${echClan}${note ? `<p class="pc-note">${note}</p>` : ''}
    ${actions.length ? `<div class="pc-actions">""")
s = rep(s, """  if(quoi === 'gn-plus'){ gnRetraitArme = null; garnisonAction(code, Number(b.dataset.n) || 1); return; }""",
           """  if(quoi === 'ech-clan'){ const o = othersMap.get(code); if(o && o.joueurId) ouvrirEchangeClan(o.joueurId, code, o.nom); return; }   // patch316
  if(quoi === 'gn-plus'){ gnRetraitArme = null; garnisonAction(code, Number(b.dataset.n) || 1); return; }""")

s = s.rstrip('\n') + r"""

// ---------- patch316 : idées d'Arkhannou ----------
// Proposer un échange depuis la fiche d'une commune d'un coéquipier : on ouvre
// Clan › Échanges avec le coéquipier et la commune déjà choisis.
function ouvrirEchangeClan(qui, code, nom){
  clanEch.qui = qui; clanEch.leurs = null; clanEch.recoit = code; clanEch.r2 = nom || '';
  try{ fermerPanneau(); }catch(e){}
  const t = document.querySelector('.tab[data-tab="clan"]');
  if(t) t.click();
  setTimeout(() => { const z = document.querySelector('.ce-bloc'); if(z) z.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 700);
}

// La France au survol (ou au toucher) du numéro d'un département.
var depChemins = null, depCheminsP = null, depBulle = null, depBulleCible = null;
function depCheminsCharger(){
  if(depChemins) return Promise.resolve(depChemins);
  if(!depCheminsP) depCheminsP = fetch('contours-departements.json', { cache: 'force-cache' }).then(r => r.json()).then(C => {
    const k = Math.cos(46.5 * Math.PI / 180);
    let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    Object.values(C).forEach(rs => rs.forEach(r => r.forEach(p => { const x = p[0] * k, y = -p[1]; if(x < x0) x0 = x; if(x > x1) x1 = x; if(y < y0) y0 = y; if(y > y1) y1 = y; })));
    const e = 190 / Math.max(x1 - x0, y1 - y0), ox = (200 - (x1 - x0) * e) / 2, oy = (200 - (y1 - y0) * e) / 2;
    depChemins = {};
    Object.keys(C).forEach(d => {
      depChemins[d] = C[d].map(r => 'M' + r.map(p => ((p[0] * k - x0) * e + ox).toFixed(1) + ' ' + ((-p[1] - y0) * e + oy).toFixed(1)).join('L') + 'Z').join('');
    });
    return depChemins;
  }).catch(() => { depCheminsP = null; return null; });
  return depCheminsP;
}
function depBulleCacher(){
  if(depBulle) depBulle.hidden = true;
  if(depBulleCible) depBulleCible.classList.remove('dep-on');
  depBulleCible = null;
}
async function depBulleMontrer(b){
  const d = b.dataset.dep;
  if(!d) return;
  if(!depBulle){ depBulle = document.createElement('div'); depBulle.className = 'dep-bulle'; depBulle.hidden = true; document.body.appendChild(depBulle); }
  if(depBulleCible) depBulleCible.classList.remove('dep-on');
  depBulleCible = b; b.classList.add('dep-on');
  const nom = DEPT_NAMES[d] || '', region = (typeof DEP_REGION !== 'undefined' && DEP_REGION[d]) || '';
  const C = await depCheminsCharger();
  if(depBulleCible !== b) return;
  const carte = C && C[d] ? `<svg viewBox="0 0 200 200" aria-hidden="true">${Object.keys(C).map(x => x === d ? '' : `<path d="${C[x]}" fill="#2A4468" stroke="#0B1A33" stroke-width=".5"/>`).join('')}<path class="dep-bulle-or" d="${C[d]}" fill="#F0B429" stroke="#FFE7A0" stroke-width="1"/></svg>` : '';
  depBulle.innerHTML = `${carte}<p><b>${echapperTexte(nom || d)}</b> (${echapperTexte(d)})${region ? `<small>${echapperTexte(region)}</small>` : ''}</p>`;
  depBulle.hidden = false;
  const or = depBulle.querySelector('.dep-bulle-or');
  if(or){
    const bb = or.getBBox(), r = Math.max(9, Math.max(bb.width, bb.height) / 2 + 5);
    or.insertAdjacentHTML('afterend', `<circle cx="${bb.x + bb.width / 2}" cy="${bb.y + bb.height / 2}" r="${r}" fill="none" stroke="#FFD56B" stroke-width="1.5" stroke-dasharray="3 2"/>`);
  }
  const rb = b.getBoundingClientRect(), w = depBulle.offsetWidth, h = depBulle.offsetHeight;
  let x = rb.left + rb.width / 2 - w / 2, y = rb.bottom + 8;
  if(y + h > window.innerHeight - 8) y = rb.top - h - 8;
  x = Math.max(8, Math.min(x, window.innerWidth - w - 8));
  depBulle.style.left = x + 'px'; depBulle.style.top = Math.max(8, y) + 'px';
}
document.addEventListener('mouseover', (e) => {
  if(!window.matchMedia || !window.matchMedia('(hover: hover)').matches) return;
  const b = e.target.closest && e.target.closest('.dep[data-dep]');
  if(b && b !== depBulleCible) depBulleMontrer(b);
});
document.addEventListener('mouseout', (e) => {
  if(!window.matchMedia || !window.matchMedia('(hover: hover)').matches) return;
  const b = e.target.closest && e.target.closest('.dep[data-dep]');
  if(b && !(e.relatedTarget && b.contains(e.relatedTarget))) depBulleCacher();
});
document.addEventListener('click', (e) => {
  const b = e.target.closest && e.target.closest('.dep[data-dep]');
  if(b){ e.preventDefault(); e.stopPropagation(); depBulleMontrer(b); return; }
  if(depBulleCible && !(depBulle && depBulle.contains(e.target))) depBulleCacher();
}, true);
window.addEventListener('scroll', () => { if(depBulleCible) depBulleCacher(); }, true);
"""
f.write_text(s + '\n', encoding='utf-8')

f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch316' not in s
s = s.rstrip('\n') + """

/* patch316 : la France au survol du numéro de département ; l'échange de clan depuis la fiche */
.dep[data-dep]{ cursor:pointer; }
.dep.dep-on{ outline:1px solid #F0B429; color:#FFD56B; }
.dep-bulle{ position:fixed; z-index:9000; width:190px; padding:8px 8px 6px; background:#0B1A33; border:1px solid rgba(240,180,41,.55);
  border-radius:12px; box-shadow:0 10px 24px rgba(0,0,0,.45); color:#EAF1F8; pointer-events:none; text-align:center; }
.dep-bulle[hidden]{ display:none; }
.dep-bulle svg{ display:block; width:100%; height:auto; }
.dep-bulle p{ margin:4px 0 0; font-size:.8rem; }
.dep-bulle p b{ color:#FFD56B; }
.dep-bulle p small{ display:block; color:#A9BCD4; font-size:.7rem; }
.pc-action.pc-ech-clan{ display:flex; align-items:center; justify-content:center; gap:8px; width:100%; margin:8px 0 4px;
  min-height:42px; border:0; border-radius:12px; background:#2BD48B; color:#0F1F38; font:inherit; font-weight:700; cursor:pointer; }
.pc-action.pc-ech-clan:disabled{ background:#2A3E5C; color:#A9BCD4; cursor:default; }
"""
f.write_text(s, encoding='utf-8')
print('patch316 appliqué')
