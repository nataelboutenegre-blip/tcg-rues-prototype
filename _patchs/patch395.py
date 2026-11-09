# patch395 (10/11/2026) : mes garnisons sur la carte, un bouclier avec son niveau (Arkhannou, 9/11).
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'
rep(A, """  if(SAISON2 && CALQUES.batiments && BATIMENTS_CARTE.size) dessinerBatimentsCanvas(ctx, liste);   // patch243-244
  majLegendeSiBesoin(joueurs);""",
"""  if(SAISON2 && CALQUES.batiments && BATIMENTS_CARTE.size) dessinerBatimentsCanvas(ctx, liste);   // patch243-244
  if(SAISON2 && CALQUES.batiments && garnisonsMoi.size) dessinerGarnisonsCanvas(ctx, liste);   // patch395
  majLegendeSiBesoin(joueurs);""")
rep(A, """// ---------- patch91 : garnisons ----------
async function chargerGarnisons(){""",
"""// patch395 : mes garnisons sur la carte, un bouclier à gauche du point avec son niveau
// vert : 4 à 10 · ambre : 1 à 3, à recharger · bleu : vide
const GN_BOUCLIER = new Path2D('M12 1.5 3.5 4.8v6.4c0 5.3 3.6 9.6 8.5 11.3 4.9-1.7 8.5-6 8.5-11.3V4.8z');
function dessinerGarnisonsCanvas(ctx, liste){
  const vue = vueCarteUnites(12);
  for(const c of liste){
    if(c.joueur !== ID_MOI) continue;
    const g = garnisonsMoi.get(String(c.code));
    if(!g) continue;
    const x = c.x, y = c.y;
    if(x < vue[0] || x > vue[2] || y < vue[1] || y > vue[3]) continue;
    const n = Math.max(0, Math.min(10, Number(g.energie) || 0));
    const coul = n >= 4 ? ['#2BD48B', '#0C3024', '#D8FFEC', 'rgba(43,212,139,.6)']
               : n >= 1 ? ['#F0B429', '#3A280A', '#FFEBB0', 'rgba(240,180,41,.6)']
               :          ['#6EA8FF', '#0E1E3A', '#D6E4FF', 'rgba(110,168,255,.6)'];
    const u = 1 / (echelleCarte() * mapZoom);   // unités de carte par pixel d'écran
    const h = mapZoom < 3 ? 17 : 23;            // hauteur du bouclier à l'écran, en px
    const k = h * u / 24;
    const cx = x - (h * 0.5 + 6) * u, cy = y;   // à gauche du point (les bâtiments sont à droite)
    ctx.save();
    ctx.translate(cx - 12 * k, cy - 12 * k); ctx.scale(k, k);
    ctx.shadowColor = coul[3]; ctx.shadowBlur = 8;
    ctx.fillStyle = coul[1]; ctx.fill(GN_BOUCLIER);
    ctx.shadowBlur = 0;
    ctx.lineWidth = 2.2; ctx.lineJoin = 'round'; ctx.strokeStyle = coul[0]; ctx.stroke(GN_BOUCLIER);
    ctx.fillStyle = coul[2]; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = '800 ' + (n >= 10 ? 10.5 : 12.5) + 'px "Big Shoulders Display", Impact, sans-serif';
    ctx.fillText(String(n), 12, 12.6);
    ctx.restore();
  }
}

// ---------- patch91 : garnisons ----------
async function chargerGarnisons(){""")
rep(A, """    repousses: g.repousses_24h, subis: g.subis_24h }]));
  renderGarnisons();""",
"""    repousses: g.repousses_24h, subis: g.subis_24h }]));
  renderGarnisons();
  if(typeof canvasActif === 'function' && canvasActif()) demanderDessin();   // patch395 : les boucliers de la carte""")
print('patch395 ok')
