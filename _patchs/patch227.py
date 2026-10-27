# -*- coding: utf-8 -*-
u"""
patch227 — idée d'Arkhannou (27/10) : le nom de la commune attaquée mène à
la carte du Front, centrée sur elle (outre-mer compris).
- Défendre : le nom de chaque commune attaquée, avec une petite icône de carte.
- La cloche : « Maroli t'attaque à Saint-Leu », Saint-Leu mène à la carte
  (on passe en mode Front si besoin).
Réutilise voirCommuneSurCarte (le « voir sur la carte » de l'assaut).
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
assert 'patch227' not in s
PIN = '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/></svg>'
# 1. Défendre
s = rep(s, "        <b>${echapperTexte(g.nom)}</b>${badgeDept(g.dept)}<span class=\"df-rarete\">",
           "        <button type=\"button\" class=\"df-voir\" data-voir-carte=\"${echapperTexte(g.code)}\" title=\"Voir sur la carte\" aria-label=\"Voir ${echapperTexte(g.nom)} sur la carte\"><b>${echapperTexte(g.nom)}</b>" + PIN + "</button>${badgeDept(g.dept)}<span class=\"df-rarete\">")
# 2. la cloche
s = rep(s, "t'attaque à <b>${echapperTexte(nomDe(m.commune_code))}</b>`,",
           "t'attaque à <button type=\"button\" class=\"nc-lien\" data-nc-voir=\"${echapperTexte(String(m.commune_code))}\" title=\"Voir sur la carte\">${echapperTexte(nomDe(m.commune_code))}" + PIN + "</button>`,")
s = rep(s, "async function ncClic(e){\n  const b = e.target.closest('button');\n  if(!b) return;\n",
           "async function ncClic(e){\n  const b = e.target.closest('button');\n  if(!b) return;\n"
           "  if(b.dataset.ncVoir){   // patch227 : la commune attaquée, sur la carte du Front\n"
           "    const code = b.dataset.ncVoir, entree = collectionMap.get(code) || { code };\n"
           "    return ncAller('front', 'territoire', () => voirCommuneSurCarte(entree));\n  }\n")
# 3. le clic dans Défendre
s = s.rstrip('\n') + u'''

// ---------- patch227 : le nom d'une commune attaquée mène à la carte (idée d'Arkhannou) ----------
document.addEventListener('click', (e) => {
  const b = e.target.closest('[data-voir-carte]');
  if(!b) return;
  const code = b.dataset.voirCarte;
  voirCommuneSurCarte(collectionMap.get(code) || { code });
});
'''
ecrire('app.js', s)
c = lire('style.css')
c = c.rstrip('\n') + u'''

/* ---------- patch227 : le nom d'une commune attaquée mène à la carte ---------- */
.df-voir{ display:inline-flex; align-items:center; gap:4px; padding:0; border:0; background:none; font:inherit; color:inherit; cursor:pointer; text-align:left; }
.df-voir b{ text-decoration:underline dotted rgba(169,188,212,.55); text-underline-offset:3px; }
.df-voir svg, .nc-lien svg{ width:13px; height:13px; stroke:var(--c-legendaire); flex:none; }
.df-voir:hover b{ color:var(--c-legendaire); text-decoration-color:currentColor; }
.df-voir:focus-visible, .nc-lien:focus-visible{ outline:2px solid var(--c-legendaire); outline-offset:2px; border-radius:4px; }
.nc-lien{ display:inline-flex; align-items:center; gap:3px; padding:0; border:0; background:none; font:inherit; font-weight:700; color:#fff; cursor:pointer;
  text-decoration:underline dotted rgba(169,188,212,.6); text-underline-offset:3px; vertical-align:baseline; }
.nc-lien svg{ width:12px; height:12px; }
'''
ecrire('style.css', c)
print('patch227 ok')
