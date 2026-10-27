# -*- coding: utf-8 -*-
u"""
patch229 — deux bugs signalés le 27/10.
- Wally : la Commune du jour terminée n'avait pas de bouton « Retour au QG »
  (Radar et Rafale l'ont).
- Arkhannou (PC) : la bulle d'une commune d'outre-mer ne se fermait pas.
  Elle a maintenant une croix, et un clic hors des territoires la ferme
  (Front et Ma France). Dans la petite vue des 5 territoires, elle est
  plus compacte.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rep(s, a, b, n=1):
    c = s.count(a); assert c == n, ('MATCH', a[:70], 'trouve', c, 'attendu', n); return s.replace(a, b)

s = lire('app.js')
assert 'patch229' not in s
# 1. Commune du jour : Retour au QG
s = rep(s, '<button type="button" class="cdj-copier" id="cdjCopier">Copier le résultat pour Discord</button>`;',
           '<div class="cdj-fin-actions"><button type="button" class="qg-btn plein" id="cdjRetourQG">Retour au QG</button>'
           '<button type="button" class="cdj-copier" id="cdjCopier">Copier le résultat pour Discord</button></div>`;\n'
           "  document.getElementById('cdjRetourQG').onclick = () => { const t = document.querySelector('.tab[data-tab=\"qg\"]'); if(t) t.click(); };   // patch229")
# 2. la bulle d'outre-mer : une croix
X = '<button type="button" class="om-bulle-x" aria-label="Fermer">✕</button>'
s = rep(s, "    b.innerHTML = `<i class=\"mf-pastille vide\"></i><div><b>Commune libre</b><span>Personne ne la tient : elle peut sortir d'un paquet Front.</span></div>`;",
           "    b.innerHTML = `<i class=\"mf-pastille vide\"></i><div><b>Commune libre</b><span>Personne ne la tient : elle peut sortir d'un paquet Front.</span></div>" + X + "`;")
s = rep(s, "    if(e) b.dataset.tcode = e.code; else delete b.dataset.tcode;\n",
           "    b.insertAdjacentHTML('beforeend', '" + X + "');   // patch229\n    if(e) b.dataset.tcode = e.code; else delete b.dataset.tcode;\n")
s = s.rstrip('\n') + u'''

// ---------- patch229 : la bulle d'outre-mer se ferme (croix, ou clic hors des territoires) ----------
document.addEventListener('click', (e) => {
  const x = e.target.closest('.om-bulle-x');
  if(!x && e.target.closest('.om-tuile')) return;
  const ouvertes = document.querySelectorAll('.om-bulle:not([hidden])');
  if(!ouvertes.length) return;
  if(x){ e.stopPropagation(); e.preventDefault(); }
  ouvertes.forEach(b => { b.hidden = true; });
  if(typeof OMF !== 'undefined' && OMF.bulle){ const d = OMF.bulle.dep; OMF.bulle = null; omfDessiner(d); }
  if(typeof OM !== 'undefined' && OM.bulle){ const d = OM.bulle.dep; OM.bulle = null; omDessiner(d); }
}, true);
'''
ecrire('app.js', s)
c = lire('style.css')
c = c.rstrip('\n') + u'''

/* ---------- patch229 : Retour au QG (Commune du jour), bulle d'outre-mer refermable ---------- */
.cdj-fin-actions{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; }
.cdj-fin-actions .cdj-copier{ align-self:center; }
.om-bulle-x{ margin-left:auto; flex:none; align-self:flex-start; border:0; background:none; color:var(--brume); font:inherit; font-size:.95rem; line-height:1; padding:2px 2px 6px 8px; cursor:pointer; }
.om-bulle-x:hover{ color:#fff; }
.om-bulle-x:focus-visible{ outline:2px solid #fff; outline-offset:2px; border-radius:4px; }
.om-grille:not(.focus) .om-bulle{ padding:6px 6px 6px 9px; gap:6px; }
.om-grille:not(.focus) .om-bulle .mf-pastille{ display:none; }
.om-grille:not(.focus) .om-bulle b{ font-size:.76rem; }
.om-grille:not(.focus) .om-bulle span{ font-size:.64rem; line-height:1.3; }
'''
ecrire('style.css', c)
print('patch229 ok')
