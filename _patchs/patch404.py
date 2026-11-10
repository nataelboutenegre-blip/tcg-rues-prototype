# patch404 (10/11/2026) : les étiquettes des zones bombardées encombraient la carte vue de loin
# (5 bombes en même temps le 10/11 : Kaltenhouse, Saint-Clet, Narbonne, Vatteville-la-Rue, Saint-Vrain ;
# capture d'Arkhannou). Taille fixe à l'écran : de loin elles couvraient des régions entières, se
# chevauchaient et sortaient du cadre. Désormais, sous le zoom 2,6, chaque zone n'a qu'une pastille 💥 ;
# plus près, l'étiquette complète, sauf si elle en chevauche une autre (la bombe la plus récente d'abord).
# Toucher l'étiquette ou la pastille rejoue toujours l'impact (zones touchables mémorisées au dessin).
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'

rep(A, """// la carte : les zones bombardées (ellipses : la carte est en degrés)
function dessinerZonesBombes(ctx, trait){
  if(!mapBounds || !MAP_W) return;
  const { latMin, latMax, lonMin, lonMax } = mapBounds;
  for(const z of BOMBES_ZONES){
    if(z.lat == null || new Date(z.fin).getTime() < Date.now()) continue;
    if(BFX && BFX.cache && BFX.z.id === z.id) continue;   // patch377 : l'animation la dessine""",
"""// la carte : les zones bombardées (ellipses : la carte est en degrés)
// patch404 : de loin, une pastille 💥 par zone ; l'étiquette complète à partir du zoom 2,6 si elle a la place
const BOMBE_ETIQ_ZOOM = 2.6;
let BOMBE_ETIQS = [];   // les étiquettes et pastilles dessinées, en unités de carte (pour les toucher)
function dessinerZonesBombes(ctx, trait){
  if(!mapBounds || !MAP_W) return;
  const { latMin, latMax, lonMin, lonMax } = mapBounds;
  const poses = [];
  BOMBE_ETIQS = [];
  const zones = BOMBES_ZONES.filter(z => z.lat != null && new Date(z.fin).getTime() >= Date.now())
    .sort((a, b) => new Date(b.fin).getTime() - new Date(a.fin).getTime());   // la plus récente d'abord
  for(const z of zones){
    if(BFX && BFX.cache && BFX.z.id === z.id) continue;   // patch377 : l'animation la dessine""")

rep(A, """    const f = trait(11), txt = `💥 +${btReglage('bombe_bonus', 15)} % · ${z.cible_nom || ''}`;
    ctx.font = `600 ${f}px "Instrument Sans", system-ui, sans-serif`;
    const w = ctx.measureText(txt).width + f * 1.2, h = f * 1.7, y = cy - ry - trait(6) - h;
    ctx.fillStyle = 'rgba(229,72,77,0.92)';
    ctx.beginPath();
    if(ctx.roundRect) ctx.roundRect(cx - w / 2, y, w, h, h / 2); else ctx.rect(cx - w / 2, y, w, h);
    ctx.fill();
    ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(txt, cx, y + h / 2 + f * 0.05);
    ctx.restore();
  }
}""",
"""    const f = trait(11), txt = `💥 +${btReglage('bombe_bonus', 15)} % · ${z.cible_nom || ''}`;
    ctx.font = `600 ${f}px "Instrument Sans", system-ui, sans-serif`;
    let w = ctx.measureText(txt).width + f * 1.2, h = f * 1.7, y = cy - ry - trait(6) - h;
    const chevauche = (a) => poses.some(b => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h);
    const complet = mapZoom >= BOMBE_ETIQ_ZOOM && !chevauche({ x: cx - w / 2, y, w, h });
    if(!complet){ h = trait(20); w = h; y = cy - ry - trait(3) - h; }   // la pastille
    const r = { x: cx - w / 2, y, w, h };
    poses.push(r); BOMBE_ETIQS.push(Object.assign({ z }, r));
    ctx.fillStyle = 'rgba(229,72,77,0.92)';
    ctx.beginPath();
    if(ctx.roundRect) ctx.roundRect(r.x, y, w, h, h / 2); else ctx.rect(r.x, y, w, h);
    ctx.fill();
    if(!complet){ ctx.strokeStyle = 'rgba(255,255,255,0.85)'; ctx.lineWidth = trait(1.2); ctx.stroke(); }
    ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(complet ? txt : '💥', cx, y + h / 2 + f * 0.05);
    ctx.restore();
  }
}""")

rep(A, """// toucher l'étiquette « 💥 +15 % · Commune » rejoue l'impact
let bfxMesure = null;
function bfxToucher(x, y){
  if(!mapBounds || !(BOMBES_ZONES || []).length) return false;
  const ech = echelleCarte(), s = ech * mapZoom;
  if(!bfxMesure) bfxMesure = document.createElement('canvas').getContext('2d');
  bfxMesure.font = '600 11px "Instrument Sans", system-ui, sans-serif';
  for(const z of BOMBES_ZONES){
    if(z.lat == null || new Date(z.fin).getTime() < Date.now()) continue;
    const g = bfxGeo(z), px = g.cx * s + mapPanX, haut = (g.cy - g.ry) * s + mapPanY - 6 - 18.7;
    const larg = bfxMesure.measureText(`💥 +${btReglage('bombe_bonus', 15)} % · ${z.cible_nom || ''}`).width + 13.2;
    if(Math.abs(x - px) <= larg / 2 + 6 && y >= haut - 6 && y <= haut + 18.7 + 6){ bfxJouer(z, false); return true; }
  }
  return false;
}""",
"""// toucher l'étiquette « 💥 +15 % · Commune » (ou la pastille 💥, patch404) rejoue l'impact
function bfxToucher(x, y){
  if(!mapBounds || !BOMBE_ETIQS.length) return false;
  const s = echelleCarte() * mapZoom, mx = (x - mapPanX) / s, my = (y - mapPanY) / s, m = 6 / s;
  for(const e of BOMBE_ETIQS){
    if(new Date(e.z.fin).getTime() < Date.now()) continue;
    if(mx >= e.x - m && mx <= e.x + e.w + m && my >= e.y - m && my <= e.y + e.h + m){ bfxJouer(e.z, false); return true; }
  }
  return false;
}""")
print('patch404 OK')
