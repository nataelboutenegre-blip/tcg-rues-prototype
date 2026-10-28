# patch244 : bâtiments sur la carte — à côté des étoiles, calque « Bâtiments », ligne à part dans la légende
import pathlib
def ouvrir(n): return pathlib.Path(n), pathlib.Path(n).read_text(encoding='utf-8')
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:90], s.count(a)); return s.replace(a, b)

f, s = ouvrir('app.js')
# 1. le calque, allumé par défaut
s = rep(s, "                   raretes: true, passage: false, clans: false };",
           "                   raretes: true, passage: false, clans: false, batiments: true };")
s = rep(s, """  zone.innerHTML = Object.keys(NOMS).map(id =>""",
"""  // patch244 : le calque des bâtiments, juste après Raretés
  const ordre = Object.keys(NOMS);
  if(SAISON2 && BATIMENTS){
    NOMS.batiments = 'Bâtiments';
    ICONES.batiments = ICONE_FORTERESSE;
    ordre.splice(ordre.indexOf('raretes') + 1, 0, 'batiments');
  }
  zone.innerHTML = ordre.map(id =>""")
s = rep(s, "  if(SAISON2 && BATIMENTS_CARTE.size) dessinerBatimentsCanvas(ctx, liste);   // patch243\n",
           "  if(SAISON2 && CALQUES.batiments && BATIMENTS_CARTE.size) dessinerBatimentsCanvas(ctx, liste);   // patch243-244\n")
# le bouton apparaît quand les bâtiments sont chargés (la barre est dessinée avant)
s = rep(s, "    BATIMENTS_CARTE = carte;\n    renderBatimentsBloc();\n",
           "    BATIMENTS_CARTE = carte;\n    renderBatimentsBloc();\n"
           "    if(!document.querySelector('#mapCalques [data-calque=\"batiments\"]') && typeof rendreCalques === 'function') rendreCalques();   // patch244\n"
           "    legendeSignature = '';\n")

# 2. à côté du point de la commune (et de son étoile), pas dessus
s = rep(s, """      const r = 7.5 * e;
      const cx = x + (types.length > 1 ? (i ? 1 : -1) * r * 0.95 : 0), cy = y - r * 1.1;""",
"""      const r = 7 * e;
      // patch244 : à droite du point et de son étoile (rayon 7 au plus), côte à côte s'il y en a deux
      const cx = x + 9 * e + r + i * (2 * r + 2 * e), cy = y;""")

# 3. la légende : les bâtiments sur leur propre ligne, sous les raretés
s = rep(s, "stroke=\"#0B1830\"/></svg>Aurore</div>${SAISON2 && BATIMENTS ? `<div><span class=\"leg-bt\">${ICONE_FONDERIE}</span>Fonderie</div><div><span class=\"leg-bt\">${ICONE_FORTERESSE}</span>Forteresse</div>` : ''}\n      </div>\n",
           "stroke=\"#0B1830\"/></svg>Aurore</div>\n      </div>${SAISON2 && BATIMENTS ? `\n      <div class=\"leg-tailles leg-batiments\"><div><span class=\"leg-bt\">${ICONE_FONDERIE}</span>Fonderie</div><div><span class=\"leg-bt\">${ICONE_FORTERESSE}</span>Forteresse</div></div>` : ''}\n")
s = rep(s, "    + '|' + TOTAL_COMMUNES;\n  if(sig === legendeSignature) return;",
           "    + '|' + TOTAL_COMMUNES\n    + '|' + (BATIMENTS ? 1 : 0);   // patch244\n  if(sig === legendeSignature) return;")
f.write_text(s, encoding='utf-8')

f, s = ouvrir('style.css')
s += """
/* ---------- patch244 : la ligne des bâtiments dans la légende ---------- */
.leg-tailles.leg-batiments{ justify-content:flex-start; align-items:center; gap:14px; margin-top:8px; padding-top:8px; }
.leg-tailles.leg-batiments div{ flex-direction:row; gap:6px; }
.leg-tailles.leg-batiments .leg-bt{ margin:0; }
"""
f.write_text(s, encoding='utf-8')
print('patch244 ok')
