# patch545 : petits lauriers (classement, fiches) : la feuille du bout suit la branche au lieu de flotter ; laurier plus large.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('app.js', "  const n = petit ? 5 : 10, t0 = 0.32, t1 = 2.55;", "  const n = petit ? 6 : 10, t0 = 0.32, t1 = 2.55;   // patch545 : 6 paires en petit")
rep('app.js', "      const k = (petit ? 1.75 : 1) * (1.15 - 0.45 * i / (n - 1));", "      const k = (petit ? 1.6 : 1) * (1.15 - 0.45 * i / (n - 1));")
rep('app.js', """    const [xe, ye] = pt(t1 + 0.08); const xt = sens > 0 ? 100 - xe : xe;
    feuilles += `<path transform="translate(${xt.toFixed(1)} ${ye.toFixed(1)}) rotate(${sens > 0 ? -60 : -120}) scale(${petit ? 1.4 : .8})\"""",
"""    // patch545 : en petit, la pointe part du bout de la tige et suit sa direction (elle flottait au-dessus de l'écu)
    const [xe, ye] = pt(petit ? t1 : t1 + 0.08); const xt = sens > 0 ? 100 - xe : xe;
    const [xf, yf] = pt(t1 + 0.01); const ap = Math.atan2(yf - ye, (sens > 0 ? 100 - xf : xf) - xt) * 180 / Math.PI;
    feuilles += `<path transform="translate(${xt.toFixed(1)} ${ye.toFixed(1)}) rotate(${petit ? ap.toFixed(1) : (sens > 0 ? -60 : -120)}) scale(${petit ? 1.3 : .8})\"""")
rep('style.css', ".lr.petit > .laurier-svg{ width: 140%; }", ".lr.petit > .laurier-svg{ width: 175%; transform: translate(-50%, -46%); }   /* patch545 */")
rep('style.css', ".lr.petit{ margin: 0 4px; }", ".lr.petit{ margin: 0 8px; }")
