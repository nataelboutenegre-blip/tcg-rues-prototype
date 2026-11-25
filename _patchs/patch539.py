# patch539 (ASMFCB) : 4 partitions à trois couleurs (tiercés) et « Couleur 3 » dans l'éditeur de blason (s3-78) ;
# le bouton « Au hasard » tire de nouveau la couleur du meuble (cassé par patch536).
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('app.js', "  gironne:   { nom:'Gironné',", """  // patch539 : les tiercés, à trois couleurs (d = couleur 2, d3 = couleur 3)
  tierce_pal:   { nom:'Tiercé en pal', d:'M33.4 0H66.7V120H33.4Z', d3:'M66.7 0H110V130H66.7Z' },
  tierce_fasce: { nom:'Tiercé en fasce', d:'M-10 40H110V80H-10Z', d3:'M-10 80H110V130H-10Z' },
  tierce_bande: { nom:'Tiercé en bande', d:'M-10 -52L110 92V172L-10 28Z', d3:'M-10 28L110 172H-10Z' },
  pairle:       { nom:'Tiercé en pairle', d:'M50 56L-2 -6H-10V130H50Z', d3:'M50 56L102 -6H110V130H50Z' },
  gironne:   { nom:'Gironné',""")
rep('app.js', "const BL_DEFAUT = { forme:'francais', partition:'plein', c1:'azur', c2:'or', meuble:'aucun',",
              "const BL_DEFAUT = { forme:'francais', partition:'plein', c1:'azur', c2:'or', c3:'gueules', meuble:'aucun',")
rep('app.js', "c2: BL_E[x.c2] ? x.c2 : 'or', meuble:", "c2: BL_E[x.c2] ? x.c2 : 'or', c3: BL_E[x.c3] ? x.c3 : 'gueules', meuble:")
rep('app.js', """${P.d ? `<path d="${P.d}" fill="${BL_E[b.c2]}"/>` : ''}${meubles}""",
              """${P.d ? `<path d="${P.d}" fill="${BL_E[b.c2]}"/>` : ''}${P.d3 ? `<path d="${P.d3}" fill="${BL_E[b.c3]}"/>` : ''}${meubles}""")
rep('app.js', """    <div class="bl-deux"><div><h2>Couleur 1</h2><div class="bl-emaux">${pastilles('c1')}</div></div>
      <div><h2>Couleur 2</h2>${BL_PARTITIONS[B.partition].d ? `<div class="bl-emaux">${pastilles('c2')}</div>` : '<p class="clan-note">Partition « Plein » : une seule couleur.</p>'}</div></div>""",
"""    <div class="bl-deux${BL_PARTITIONS[B.partition].d3 ? ' bl-trois' : ''}"><div><h2>Couleur 1</h2><div class="bl-emaux">${pastilles('c1')}</div></div>
      <div><h2>Couleur 2</h2>${BL_PARTITIONS[B.partition].d ? `<div class="bl-emaux">${pastilles('c2')}</div>` : '<p class="clan-note">Partition « Plein » : une seule couleur.</p>'}</div>${BL_PARTITIONS[B.partition].d3 ? `
      <div><h2>Couleur 3</h2><div class="bl-emaux">${pastilles('c3')}</div></div>` : ''}</div>""")
rep('app.js', "      B.meuble = tire(Object.keys(BL_MEUBLES).slice(1).filter(k => !(BL_MEUBLES[k].rare > blRares)));   // patch536 do { B.cm = tire(cles); } while(B.cm === B.c1);",
              "      do { B.c3 = tire(cles); } while(B.c3 === B.c1 || B.c3 === B.c2);   // patch539\n      B.meuble = tire(Object.keys(BL_MEUBLES).slice(1).filter(k => !(BL_MEUBLES[k].rare > blRares)));   // patch536\n      do { B.cm = tire(cles); } while(B.cm === B.c1);")
rep('style.css', ".bl-deux{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:14px; }",
              ".bl-deux{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:14px; }\n.bl-deux.bl-trois{ grid-template-columns:repeat(3, minmax(0,1fr)); }   /* patch539 */")
rep('style.css', "@media (max-width:560px){ .bl-deux{ grid-template-columns:1fr; }", "@media (max-width:560px){ .bl-deux, .bl-deux.bl-trois{ grid-template-columns:1fr; }")
