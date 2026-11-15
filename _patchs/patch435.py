# patch435 (15/11/2026) : saison 3, les sièges en cours sur la carte du Front (idée de JeanFlouff).
# Un anneau autour du point de la commune, rempli selon la jauge : or pour mes sièges,
# rouge pour les sièges contre mes communes ; de près, le pourcentage à côté.
# Ne dessine rien tant que le siège est éteint (SIEGE faux).
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'
if 'patch435' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')

rep(A, """  if(SAISON2 && CALQUES.batiments && garnisonsMoi.size) dessinerGarnisonsCanvas(ctx, liste);   // patch395
""", """  if(SAISON2 && CALQUES.batiments && garnisonsMoi.size) dessinerGarnisonsCanvas(ctx, liste);   // patch395
  if(typeof SIEGE !== 'undefined' && SIEGE && (sgMes.length || sgMenaces.length)) dessinerSiegesCanvas(ctx, liste);   // patch435
""")
rep(A, """// patch395 : mes garnisons sur la carte, un bouclier à gauche du point avec son niveau""", """// patch435 : les sièges en cours, un anneau rempli selon la jauge (or : les miens ; rouge : contre moi)
function dessinerSiegesCanvas(ctx, liste){
  const jauges = new Map();
  for(const s of sgMes){
    const r = Number(s.resistance) || 0;
    if(r > 0) jauges.set(String(s.commune), { p: Math.min(1, (Number(s.degats) || 0) / r), moi: true });
  }
  const laisses = typeof sgLaisses === 'function' ? sgLaisses() : new Set();
  for(const m of sgMenaces){
    const r = Number(m.resistance) || 0, k = String(m.commune);
    if(r <= 0 || laisses.has(m.id)) continue;
    const p = Math.min(1, (Number(m.degats) || 0) / r), e = jauges.get(k);
    if(!e || (!e.moi && p > e.p)) jauges.set(k, { p, moi: false });
  }
  if(!jauges.size) return;
  const vue = vueCarteUnites(24);
  const u = 1 / (echelleCarte() * mapZoom);   // unités de carte par pixel d'écran
  const px = mapZoom < 2 ? 4.5 : mapZoom < 12 ? 6.5 : 10;   // plus discret de loin
  const rayon = px * u, ep = Math.max(1.6, px * 0.32) * u;
  const debut = -Math.PI / 2;
  for(const c of liste){
    const j = jauges.get(String(c.code));
    if(!j) continue;
    if(c.x < vue[0] || c.x > vue[2] || c.y < vue[1] || c.y > vue[3]) continue;
    const coul = j.moi ? '#F0B429' : '#E5484D';
    ctx.save();
    ctx.lineCap = 'round';
    ctx.beginPath(); ctx.arc(c.x, c.y, rayon, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(7,17,31,.82)'; ctx.lineWidth = ep + 2.4 * u; ctx.stroke();
    ctx.beginPath(); ctx.arc(c.x, c.y, rayon, 0, Math.PI * 2);
    ctx.strokeStyle = j.moi ? 'rgba(240,180,41,.28)' : 'rgba(229,72,77,.3)'; ctx.lineWidth = ep; ctx.stroke();
    if(j.p > 0){
      ctx.beginPath(); ctx.arc(c.x, c.y, rayon, debut, debut + Math.PI * 2 * Math.max(0.04, j.p));
      ctx.shadowColor = coul; ctx.shadowBlur = 6;
      ctx.strokeStyle = coul; ctx.lineWidth = ep; ctx.stroke();
    }
    ctx.restore();
    if(mapZoom >= 12){   // de près : le pourcentage
      const f = 10.5 * u, txt = Math.round(100 * j.p) + ' %';
      ctx.save();
      ctx.font = `700 ${f}px "Instrument Sans", system-ui, sans-serif`;
      const w = ctx.measureText(txt).width + 8 * u, h = 15 * u, x = c.x - w / 2, y = c.y + rayon + 4 * u;
      ctx.fillStyle = j.moi ? 'rgba(240,180,41,.95)' : 'rgba(229,72,77,.95)';
      ctx.beginPath(); if(ctx.roundRect) ctx.roundRect(x, y, w, h, h / 2); else ctx.rect(x, y, w, h); ctx.fill();
      ctx.fillStyle = j.moi ? '#1A1404' : '#fff'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(txt, c.x, y + h / 2 + 0.5 * u);
      ctx.restore();
    }
  }
}

// patch395 : mes garnisons sur la carte, un bouclier à gauche du point avec son niveau""")
# la carte se redessine quand les sièges arrivent
rep(A, """  sgMenaces = Array.isArray(data) ? data : [];
  renderMenacesSiege();""", """  sgMenaces = Array.isArray(data) ? data : [];
  if(typeof canvasActif === 'function' && canvasActif()) demanderDessin();   // patch435
  renderMenacesSiege();""")
rep(A, """  sgMes = Array.isArray(data) ? data : [];
  renderMesSieges();""", """  sgMes = Array.isArray(data) ? data : [];
  if(typeof canvasActif === 'function' && canvasActif()) demanderDessin();   // patch435
  renderMesSieges();""")
print('patch435 OK')
