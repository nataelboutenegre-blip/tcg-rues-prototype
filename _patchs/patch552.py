# patch552 (s3-85) : la grille « Lettres » du motif propose aussi - . / # _ + & ! ? ' (3 caractères au plus en tout).
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('app.js', """    pk.innerHTML = `Gratuit · <b>${MOT_MAX_LETTRES} lettres au plus par motif</b>, pour éviter qu'on écrive des mots.`;
    g.innerHTML = `<div class="mot-lettres">${'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'.split('').map(l => `<button type="button" data-l="${l}">${l}</button>`).join('')}</div>`;""",
"""    pk.innerHTML = `Gratuit · <b>${MOT_MAX_LETTRES} caractères au plus par motif</b> (lettres, chiffres ou signes), pour éviter qu'on écrive des mots.`;   // patch552
    g.innerHTML = `<div class="mot-lettres">${[...'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', ...'-./#_+&!?\\''].map(l => `<button type="button" data-l="${echapperTexte(l)}">${echapperTexte(l)}</button>`).join('')}</div>`;""")
rep('app.js', "texte: `${MOT_MAX_LETTRES} lettres au plus par motif.` });", "texte: `${MOT_MAX_LETTRES} caractères au plus par motif.` });", n=2)
p = os.path.join(R, 'data/nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
n1 = "✏️ Motif de territoire : en plus des lettres et chiffres, tu peux placer - . / # _ + & ! ? ' (3 caractères au plus en tout). Idée d'Arkhannou."
if n1 not in d[0]['nouveautes']: d[0]['nouveautes'].append(n1)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('nouveautes : ok')
