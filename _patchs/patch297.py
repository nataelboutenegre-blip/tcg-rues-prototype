# patch297 : « Ta boutique » cassée (31/10)
# Le raccourci 🛍 du patch291 utilisait la classe .bqr, déjà prise par le bloc « Ta boutique » (patch261).
# Effets : le bloc était réduit à 38 × 38 px (les cartes débordaient sur toute la page),
# il était caché pour les joueurs sans accès à la boutique en euros, et ses horloges « bougeaient ».
# Correction : le raccourci prend la classe .bqs (sac), le bloc « Ta boutique » n'est plus touché.
import json, pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch297' not in s
a = s[s.index('/* patch291 : la boutique plus proche */'):s.index('.soutien{')]
b = (a.replace('.bqr{', '.bqs{')
      .replace('.bqr[hidden]', '.bqs[hidden]')
      .replace('.bqr svg', '.bqs svg')
      .replace('.bqr:hover', '.bqs:hover')
      .replace('.bqr:focus-visible', '.bqs:focus-visible')
      .replace('.bqr-point', '.bqs-point')
      .replace('.bqr.bouge', '.bqs.bouge')
      .replace('/* patch291 : la boutique plus proche */', '/* patch291 : la boutique plus proche (classe .bqs depuis patch297) */'))
assert '.bqr{' not in b and '.bqr.' not in b and '.bqr-point' not in b, b
s = s.replace(a, b)
f.write_text(s, encoding='utf-8')

f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch297' not in s
s = rep(s, "b.type = 'button'; b.className = 'bqr'; b.id = id; b.hidden = true;",
           "b.type = 'button'; b.className = 'bqs'; b.id = id; b.hidden = true;   // patch297 : .bqr est pris par « Ta boutique »")
s = rep(s, """b.innerHTML = BQR_SAC + '<span class="bqr-point" hidden></span>';""",
           """b.innerHTML = BQR_SAC + '<span class="bqs-point" hidden></span>';""")
s = rep(s, """  document.querySelectorAll('.bqr').forEach(b => {
    b.hidden = !ok;
    const p = b.querySelector('.bqr-point'); if(p) p.hidden = !nouveau;""",
           """  document.querySelectorAll('.bqs').forEach(b => {
    b.hidden = !ok;
    const p = b.querySelector('.bqs-point'); if(p) p.hidden = !nouveau;""")
s = rep(s, "document.querySelectorAll('.bqr:not([hidden])').forEach(b =>",
           "document.querySelectorAll('.bqs:not([hidden])').forEach(b =>")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('data/nouveautes.json'); d = json.loads(f.read_text(encoding='utf-8'))
e = next(x for x in d if x['date'] == '2026-10-31')
e.setdefault('correctifs', []).append('« Ta boutique » : les cartes se chevauchaient et débordaient sur la page')
f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch297 appliqué')
