# patch267 : « Mes garnisons » : nom cliquable vers la carte + département (idée d'Arkhannou, aperçu validé le 29/10)
import pathlib
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:90], s.count(a)); return s.replace(a, b)
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch267' not in s
s = rep(s, """      const tier = TIERS.find(t => t.id === g.tier) || TIERS[TIERS.length - 1];
      return `<div class="gl"><i class="gl-c ${tier.id}"></i><div class="gl-t"><b>${echapperTexte(g.nom)}</b>
""", """      const tier = TIERS.find(t => t.id === g.tier) || TIERS[TIERS.length - 1];
      const dep = code.startsWith('97') ? code.slice(0, 3) : code.slice(0, 2);   // patch267
      return `<div class="gl"><i class="gl-c ${tier.id}"></i><div class="gl-t">
        <div class="gl-nom"><button type="button" class="df-voir" data-voir-carte="${echapperTexte(code)}" title="Voir sur la carte" aria-label="Voir ${echapperTexte(g.nom)} sur la carte"><b>${echapperTexte(g.nom)}</b><svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/></svg></button>${badgeDept(dep)}</div>
""")
f.write_text(s, encoding='utf-8')
f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch267' not in s
s = s.rstrip('\n') + """
/* patch267 : « Mes garnisons » : nom vers la carte + département */
.gl-t .gl-nom{ display:flex; align-items:center; gap:7px; min-width:0; }
.gl-t .gl-nom b{ display:inline; }
.gl-t .gl-nom .df-voir svg{ width:14px; height:14px; stroke:#F0B429; flex:none; }
.gl-t .gl-nom .dep{ font-size:.66rem; color:#C8D5E6; }
"""
f.write_text(s, encoding='utf-8')
print('patch267 appliqué')
