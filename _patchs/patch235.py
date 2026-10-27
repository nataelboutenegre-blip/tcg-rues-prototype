# patch235 : étoile Aurore de la carte plus discrète (sans halo, taille d'une légendaire)
import pathlib
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:60], s.count(a)); s = s.replace(a, b)
rep("""  const h = ctx.createRadialGradient(x, y, 0, x, y, r * 2.3);
  h.addColorStop(0, 'rgba(61,242,192,0.7)'); h.addColorStop(0.5, 'rgba(91,140,255,0.3)'); h.addColorStop(1, 'rgba(176,108,255,0)');
  ctx.fillStyle = h; ctx.beginPath(); ctx.arc(x, y, r * 2.3, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath();
  for(let i = 0; i < 8; i++){""", """  ctx.beginPath();   // patch235 : plus de halo
  for(let i = 0; i < 8; i++){""")
rep("dessinerEtoileAurore(ctx, x, y, (j.moi ? 11 : 10) * e)", "dessinerEtoileAurore(ctx, x, y, (j.moi ? 6.5 : 6) * e)")
f.write_text(s, encoding='utf-8'); print('patch235 ok')
