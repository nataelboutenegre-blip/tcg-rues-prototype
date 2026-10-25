# -*- coding: utf-8 -*-
u"""
patch170 — les Aurore du Front S1 versees en Terra : etiquette rouge
« Front S1 » sur la mini-carte (collection, vitrine, profils).
SQL : _sql/aurore-saison-1.sql (passe ces cartes en Aurore et donne la liste).
Sans le SQL : rien ne change.
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
assert 'terra_aurores_s1' not in js, u'patch170 deja applique'
js = rempl(js, u"""        <span class="mini-rarete">${e.tier.label}</span>""",
u"""        <span class="mini-rarete">${e.tier.label}${e.auroreS1 ? '<span class="mini-origine" title="Aurore gagnée dans le Front, saison 1">Front S1</span>' : ''}</span>""", 'etiquette')
js = rempl(js, u"""  terraCharge = true;
  return true;""", u"""  // patch170 : les Aurore venues du Front S1
  try{
    const { data: s1, error: es } = await sb.rpc('terra_aurores_s1', { p_joueur: window.__monId });
    if(!es) for(const code of s1 || []){ const e = terraCollection.get(code); if(e) e.auroreS1 = true; }
  }catch(err){}
  terraCharge = true;
  return true;""", 'collection')
js = rempl(js, u"""  return (data || []).map(r => ({ code: r.code, nom: r.nom, dept: r.departement,
    tier: TIERS.find(t => t.id === r.tier) || TIERS[TIERS.length - 1], pop: r.population,
    exemplaires: 1, rank: r.rang, tierSize: r.palier_total, aurore: r.aurore ? 1 : 0 }));""",
u"""  let s1 = new Set();   // patch170
  try{ const r2 = await sb.rpc('terra_aurores_s1', { p_joueur: id }); if(!r2.error) s1 = new Set(r2.data || []); }catch(err){}
  return (data || []).map(r => ({ code: r.code, nom: r.nom, dept: r.departement,
    tier: TIERS.find(t => t.id === r.tier) || TIERS[TIERS.length - 1], pop: r.population,
    exemplaires: 1, rank: r.rang, tierSize: r.palier_total, aurore: r.aurore ? 1 : 0, auroreS1: s1.has(r.code) }));""", 'vitrine')
ecrire('app.js', js)
css = lire('style.css')
css = rempl(css, u"/* patch115 : l'astuce sous la recherche d'echange */", u"""/* patch170 : l'Aurore venue du Front S1 */
.mini-origine{ display:inline-block; margin-left:4px; padding:0 4px; border-radius:3px; background:#E5484D; color:#fff;
  font-size:.82em; font-weight:800; letter-spacing:.02em; line-height:1.4; vertical-align:1px; text-transform:none; }

/* patch115 : l'astuce sous la recherche d'echange */""", 'css')
ecrire('style.css', css)
print(u'patch170 applique. Lancer : python3 maj-version.py')
