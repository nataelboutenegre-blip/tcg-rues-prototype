# patch320 : le tampon de la Carte postale ne cache plus le nom de la carte
#  Le tampon quitte le milieu de la carte (sur le nom, le n° et la rareté) pour le coin
#  haut de la photo, comme un vrai cachet de la poste ; à gauche si le coin droit porte
#  déjà le « ×N ». Il est dessiné en SVG : le nom suit l'arc du cachet (il tient toujours,
#  quelle que soit sa longueur, sans couper les mots), le n° du département au centre.
#  Le nom de la carte postale ne se coupe plus au milieu d'un mot.
import pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch320' not in s
s = rep(s, """      + (st === 'postale' && niv > 0 ? `<span class="atl-tampon" aria-hidden="true">${echapperTexte(String(e.nom || '').toUpperCase())}<br>· ${echapperTexte(e.dept || '')} ·<br>2026</span>` : ''),""",
           """      + (st === 'postale' && niv > 0 ? atlTampon(e.nom, e.dept) : ''),   // patch320""")
s = rep(s, """function atlParts(e, grande, hantee){""", """// patch320 : le cachet de la poste, en SVG (le nom suit l'arc et tient toujours)
let atlTamponN = 0;
function atlTampon(nom, dept){
  const id = 'atlTp' + (++atlTamponN), n = String(nom || '').length;
  const taille = n <= 10 ? 13 : n <= 16 ? 11.5 : 10;
  return `<span class="atl-tampon" aria-hidden="true"><svg viewBox="0 0 100 100"><defs><path id="${id}" d="M 15 52 A 35 35 0 0 1 85 52"/></defs>`
    + `<circle cx="50" cy="50" r="46" class="tp-o"/><circle cx="50" cy="50" r="23" class="tp-i"/>`
    + `<text font-size="${taille}"><textPath href="#${id}" startOffset="50%" text-anchor="middle"${n > 11 ? ' textLength="106" lengthAdjust="spacingAndGlyphs"' : ''}>${echapperTexte(String(nom || '').toUpperCase())}</textPath></text>`
    + `<text x="50" y="57" class="tp-d" text-anchor="middle">${echapperTexte(dept || '')}</text>`
    + `<text x="50" y="88" class="tp-a" text-anchor="middle">2026</text></svg></span>`;
}
function atlParts(e, grande, hantee){""")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
s = rep(s, """.atl.st-postale:not(.skin):not(.aurore) .atl-tampon{ display:flex; position:absolute; z-index:4; right:6px; top:52%; width:44px; height:44px; box-sizing:border-box; padding:3px;
  border-radius:50%; border:1.6px solid rgba(122,40,30,.62); color:rgba(122,40,30,.78); font:700 5.4px/1.2 Georgia, serif; letter-spacing:.04em;
  text-align:center; align-items:center; justify-content:center; transform:rotate(-14deg); overflow:hidden; overflow-wrap:anywhere; pointer-events:none; }
.mini.atl-n1.st-postale .atl-tampon{ width:34px; height:34px; font-size:4.4px; }
.card.atl.st-postale:not(.skin):not(.aurore) .atl-tampon{ right:8px; top:100px; width:56px; height:56px; font-size:7px; border-width:2px; }
""", """/* patch320 : le cachet sur le coin de la photo, plus sur le nom ; à gauche si le « ×N » occupe le coin droit */
.atl.st-postale:not(.skin):not(.aurore) .atl-tampon{ display:block; position:absolute; z-index:4; right:5px; top:5px; width:42px; height:42px;
  color:rgba(122,40,30,.82); transform:rotate(-14deg); pointer-events:none; filter:drop-shadow(0 0 1px rgba(239,227,200,.7)); }
.mini.atl-n1.st-postale .atl-tampon{ width:32px; height:32px; }
.card.atl.st-postale:not(.skin):not(.aurore) .atl-tampon{ right:8px; top:100px; width:56px; height:56px; }
.mini-int:has(> .mini-ex) > .atl-tampon{ right:auto !important; left:5px; transform:rotate(12deg) !important; }
.atl-tampon svg{ display:block; width:100%; height:100%; overflow:visible; }
.atl-tampon .tp-o, .atl-tampon .tp-i{ fill:none; stroke:currentColor; }
.atl-tampon .tp-o{ stroke-width:3.2; } .atl-tampon .tp-i{ stroke-width:1.6; }
.atl-tampon text{ fill:currentColor; font-family:Georgia, 'Times New Roman', serif; font-weight:700; letter-spacing:.05em; }
.atl-tampon .tp-d{ font-size:19px; } .atl-tampon .tp-a{ font-size:11px; letter-spacing:.12em; }
""")
s = rep(s, """.mini.atl.st-postale:not(.skin):not(.aurore) .mini-nom{ font-size:.86rem; } .mini.atl.st-postale:not(.skin):not(.aurore) .mini-nom.long{ font-size:.74rem; }""",
           """.mini.atl.st-postale:not(.skin):not(.aurore) .mini-nom{ font-size:.86rem; overflow-wrap:break-word; } .mini.atl.st-postale:not(.skin):not(.aurore) .mini-nom.long{ font-size:.68rem; }   /* patch320 */""")
f.write_text(s, encoding='utf-8')
print('patch320 ok')
