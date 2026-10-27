# patch236 : filtre « Aurore » dans la collection Terra (idée de Maroli)
import pathlib
def ouvrir(n): return pathlib.Path(n), pathlib.Path(n).read_text(encoding='utf-8')
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:60], s.count(a)); return s.replace(a, b)
f, s = ouvrir('app.js')
s = rep(s, """  const nbDbl = Object.values(dbl).reduce((s, n) => s + n, 0);
  const gainMax""", """  const nbDbl = Object.values(dbl).reduce((s, n) => s + n, 0);
  let nbAur = 0; for(const e of terraCollection.values()) if(e.aurore > 0) nbAur++;   // patch236
  if(terraFiltre === 'aurore' && !nbAur) terraFiltre = 'tous';
  const gainMax""")
s = rep(s, """data-tcf="doublons">Doublons <span class="nb">${fmtNombre(nbDbl)}</span></button>
""", """data-tcf="doublons">Doublons <span class="nb">${fmtNombre(nbDbl)}</span></button>
      ${nbAur ? `<button class="coll-filtre ${terraFiltre === 'aurore' ? 'actif' : ''}" data-tcf="aurore"><i class="au-pt" aria-hidden="true"></i>Aurore <span class="nb">${fmtNombre(nbAur)}</span></button>` : ''}
""")
s = rep(s, """(terraFiltre === 'doublons' ? libresTerra(e) > 0 : e.tier.id === terraFiltre))""",
           """(terraFiltre === 'doublons' ? libresTerra(e) > 0 : terraFiltre === 'aurore' ? e.aurore > 0 : e.tier.id === terraFiltre))""")
f.write_text(s, encoding='utf-8')
f, s = ouvrir('style.css')
s = rep(s, """  .coll-filtre .point{ width:8px; height:8px; border-radius:50%; }
""", """  .coll-filtre .point{ width:8px; height:8px; border-radius:50%; }
  .coll-filtre .au-pt{ width:11px; height:11px; flex:none; background:linear-gradient(135deg,#fff,#9FFFE2 35%,#7FA8FF 70%,#C08CFF);
    clip-path:polygon(50% 0,61% 39%,100% 50%,61% 61%,50% 100%,39% 61%,0 50%,39% 39%); }
  .coll-filtre.actif .au-pt{ background:linear-gradient(135deg,#1FB98F,#4A78F0 55%,#8A4CF0); }
""")
f.write_text(s, encoding='utf-8'); print('patch236 ok')
