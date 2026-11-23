# patch512 : les motifs de territoire sur les départements, quand la carte est dézoomée (idée d'Arkhannou, 23/11).
# Le joueur en tête d'un département y montre son motif, comme un drapeau. Plus la domination est nette, plus il se voit.
# Rien côté serveur. Le calque « Motifs » coupe aussi ce dessin. Pas en mode clan « Plein ».
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

rep('app.js', """        const cd = cheminDeptCanvas(dep, CONTOURS_DEPTS[dep]);
        ctx.fill(cd);
        ctx.globalAlpha = 1;""",
"""        const cd = cheminDeptCanvas(dep, CONTOURS_DEPTS[dep]);
        ctx.fill(cd);
        ctx.globalAlpha = 1;
        if(!pleinD) motPeindreDept(ctx, info.joueur, cd, k, info.force);   // patch512 : le motif du joueur en tête""")
rep('app.js', "/* ---------- Boutique › Atelier › Mon territoire ---------- */",
"""// patch512 : de loin, le motif sur le département du joueur en tête (idée d'Arkhannou)
function motPeindreDept(ctx, id, chemin, k, force){
  if(CALQUES.motifs === false || !MTF.formes) return;
  const m = id === ID_MOI ? MTF.moi : MOTIFS.get(id);
  if(!m) return;
  const px = Math.max(8, Math.round((m.densite || 42) * CV.dpr));
  let e = MTF.pats.get(id);
  if(!e || e.m !== m || e.px !== px){ e = { m, px, pat: ctx.createPattern(motTuile(m, px), 'repeat') }; MTF.pats.set(id, e); }
  if(!e.pat) return;
  if(e.pat.setTransform) e.pat.setTransform(new DOMMatrix().scale(1 / k));
  ctx.globalAlpha = opaciteJoueur(id, Math.min(1, (force || 0.6) / 0.85) * (m.intensite || 80) / 100);
  ctx.fillStyle = e.pat; ctx.fill(chemin);
  ctx.globalAlpha = 1;
}

/* ---------- Boutique › Atelier › Mon territoire ---------- */""")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
if d[0].get('date') != '2026-11-23': d.insert(0, {'date': '2026-11-23', 'nouveautes': []})
e = d[0]; e.setdefault('nouveautes', [])
l = "🎨 Territoire : de loin, chaque département montre le motif du joueur en tête, comme un drapeau. Plus il domine, plus son motif se voit. Idée d'Arkhannou."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
