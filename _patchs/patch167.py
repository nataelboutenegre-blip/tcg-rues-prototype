# -*- coding: utf-8 -*-
u"""
patch167 — profil : la case « épiques » manquait (légendaires et rares
seulement). SQL : _sql/profil-epiques.sql. Sans le SQL, la case affiche 0.
Mise en page : communes et départements, puis légendaires / épiques / rares.
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
assert 'pf-trio' not in js, u'patch167 deja applique'
js = rempl(js, u"""          <div class="pf-ch"><b style="color:var(--c-legendaire)">${nb(p.legendaires)}</b><span>légendaires</span></div>
          <div class="pf-ch"><b style="color:var(--c-rare)">${nb(p.rares)}</b><span>rares</span></div>
        </div>""", u"""        </div>
        <div class="pf-paire pf-trio">
          <div class="pf-ch"><b style="color:var(--c-legendaire)">${nb(p.legendaires)}</b><span>légendaires</span></div>
          <div class="pf-ch"><b style="color:var(--c-epique)">${nb(p.epiques)}</b><span>épiques</span></div>
          <div class="pf-ch"><b style="color:var(--c-rare)">${nb(p.rares)}</b><span>rares</span></div>
        </div>""", 'panneau')
js = rempl(js, u"""          <div class="pr-ch"><b style="color:var(--c-legendaire)">${nb(p.legendaires)}</b><span>légendaires</span></div>
          <div class="pr-ch"><b style="color:var(--c-rare)">${nb(p.rares)}</b><span>rares</span></div>""", u"""          <div class="pr-ch"><b style="color:var(--c-legendaire)">${nb(p.legendaires)}</b><span>légendaires</span></div>
          <div class="pr-ch"><b style="color:var(--c-epique)">${nb(p.epiques)}</b><span>épiques</span></div>
          <div class="pr-ch"><b style="color:var(--c-rare)">${nb(p.rares)}</b><span>rares</span></div>""", 'fiche')
ecrire('app.js', js)
css = lire('style.css')
css = rempl(css, u"  .pf-paire{ display:grid; grid-template-columns:1fr 1fr; gap:11px; }", u"""  .pf-paire{ display:grid; grid-template-columns:1fr 1fr; gap:11px; }
  .pf-paire.pf-trio{ grid-template-columns:repeat(3, minmax(0, 1fr)); margin-top:11px; }   /* patch167 */""", 'trio')
css = rempl(css, u"  .pr-chiffres{ display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-bottom:20px; }",
  u"  .pr-chiffres{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:8px; margin-bottom:20px; }", 'fiche5')
css = rempl(css, u"    .pr-chiffres{ grid-template-columns:repeat(2,1fr); }",
  u"    .pr-chiffres{ grid-template-columns:repeat(6,minmax(0,1fr)); } .pr-chiffres .pr-ch{ grid-column:span 2; } .pr-chiffres .pr-ch:nth-child(-n+2){ grid-column:span 3; }", 'fiche-mobile')
ecrire('style.css', css)
print(u'patch167 applique. Lancer : python3 maj-version.py')
