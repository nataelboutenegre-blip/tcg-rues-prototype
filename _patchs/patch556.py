# patch556 : Terra › Ma France : un bouton « Vue départements » qui garde la carte par département à tous les zooms
# (pour voir les blasons des départements complets en grand). Idée d'Arkhannou.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('app.js', "function mfComplet(dep){", """function mfVueDep(){ if(MF.figer === undefined){ try{ MF.figer = localStorage.getItem('tf-mf-figer') === '1'; }catch(e){ MF.figer = false; } } return MF.k < MF_COMMUNES || MF.figer; }   // patch556
function mfComplet(dep){""")
rep('app.js', """      <div class="mf-zoom"><button data-mf="plus" aria-label="Zoomer">+</button><button data-mf="moins" aria-label="Dézoomer">−</button><button data-mf="centre" aria-label="Recentrer">⌂</button></div>""",
"""      <div class="mf-zoom"><button data-mf="plus" aria-label="Zoomer">+</button><button data-mf="moins" aria-label="Dézoomer">−</button><button data-mf="centre" aria-label="Recentrer">⌂</button></div>
      <button type="button" class="mf-figer${mfVueDep() && MF.figer ? ' on' : ''}" data-mf="figer" aria-pressed="${!!MF.figer}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" aria-hidden="true"><path d="M3 4h7v7H3zM3 14h7v7H3zM14 4h7v7h-7zM14 14h7v7h-7z"/></svg>Vue départements</button>""")
# dessin et toucher : la vue départements reste si le bouton est mis
rep('app.js', """  if(MF.k < MF_COMMUNES){
    for(const dep in CONTOURS_DEPTS){
      const p = cheminDeptCanvas(dep, CONTOURS_DEPTS[dep]);""", """  if(mfVueDep()){   // patch556
    for(const dep in CONTOURS_DEPTS){
      const p = cheminDeptCanvas(dep, CONTOURS_DEPTS[dep]);""")
rep('app.js', "      const hpx = Math.max(16, Math.min(46, 0.55 * Math.min(b[2] - b[0], b[3] - b[1]) * S));",
    "      const hpx = Math.max(16, Math.min(MF.figer ? 140 : 46, 0.55 * Math.min(b[2] - b[0], b[3] - b[1]) * S));   // patch556 : en grand si on zoome")
rep('app.js', "    if(niveau) niveau.textContent = MF.k <= 1.01 ? 'France entière · par département' : 'Par département · zoome encore';",
    "    if(niveau) niveau.textContent = MF.figer && MF.k >= MF_COMMUNES ? 'Vue départements' : MF.k <= 1.01 ? 'France entière · par département' : MF.figer ? 'Par département' : 'Par département · zoome encore';")
rep('app.js', """  if(MF.k < MF_COMMUNES){
    MF.bulle = null;   // patch540""", """  if(mfVueDep()){
    MF.bulle = null;   // patch540""")
rep('app.js', "    majBulleMF();\n    mfZoomer(3, px, py); mfPlanifier(); return;", "    majBulleMF();\n    if(!MF.figer || !MF.bulle) mfZoomer(MF.figer ? 1.8 : 3, px, py); mfPlanifier(); return;   // patch556 : en vue départements, toucher un blason l'ouvre sans zoomer")
rep('app.js', """    if(z.dataset.mf === 'centre'){ MF.k = 1; MF.ox = 0; MF.oy = 0; MF.bulle = null; majBulleMF(); }""",
"""    if(z.dataset.mf === 'figer'){   // patch556
      MF.figer = !MF.figer; try{ localStorage.setItem('tf-mf-figer', MF.figer ? '1' : '0'); }catch(err){}
      z.classList.toggle('on', MF.figer); z.setAttribute('aria-pressed', String(MF.figer)); MF.bulle = null; majBulleMF();
      mfPlanifier(); return;
    }
    if(z.dataset.mf === 'centre'){ MF.k = 1; MF.ox = 0; MF.oy = 0; MF.bulle = null; majBulleMF(); }""")
css = """
/* patch556 : « Vue départements » sur Ma France */
.mf-figer{ position:absolute; left:8px; bottom:8px; display:inline-flex; align-items:center; gap:6px; border:1px solid rgba(169,188,212,.25); background:rgba(15,31,56,.9);
  color:#cfd8e8; font:inherit; font-size:.78rem; font-weight:700; padding:7px 11px; border-radius:999px; cursor:pointer; }
.mf-figer svg{ width:15px; height:15px; }
.mf-figer.on{ border-color:rgba(240,180,41,.6); background:rgba(240,180,41,.18); color:#F7C948; }
"""
p = os.path.join(R, 'style.css'); t = open(p, encoding='utf-8').read()
if 'patch556' not in t: open(p, 'a', encoding='utf-8').write(css); print('style.css : ajouté')
p = os.path.join(R, 'data/nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
n1 = "🛡️ Terra › Ma France : un bouton « Vue départements » garde la carte par département même en zoomant, pour admirer en grand les blasons de tes départements complets. Idée d'Arkhannou."
if n1 not in d[0]['nouveautes']: d[0]['nouveautes'].append(n1)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('nouveautes : ok')
