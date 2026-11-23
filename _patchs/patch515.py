# patch515 : éditeur de motifs — toucher un chiffre à droite d'un curseur permet de taper la valeur (idée d'Arkhannou, 23/11).
# Valable pour tous les curseurs de l'éditeur (calque et « Sur mon territoire ») : la valeur tapée est bornée au min/max
# du curseur, puis le curseur reçoit les événements input/change habituels. La rotation passe au degré près (pas de 1).
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

rep('app.js', '<input type="range" id="motSR" min="0" max="355" step="5" value="${c.r}">',
              '<input type="range" id="motSR" min="0" max="359" step="1" value="${c.r}">')   # patch515 : au degré près
rep('app.js', "/* la bibliothèque de formes */",
"""// patch515 : toucher le chiffre d'un curseur pour taper la valeur (idée d'Arkhannou)
function motSaisieOuvrir(o){
  const r = o.previousElementSibling;
  if(!r || r.type !== 'range' || o.hidden) return;
  const s = document.createElement('input');
  s.type = 'number'; s.className = 'mot-saisie'; s.inputMode = 'numeric';
  s.min = r.min; s.max = r.max; s.step = r.step || 1; s.value = r.value;
  s.setAttribute('aria-label', 'Valeur de ' + ((o.parentElement.querySelector('label') || {}).textContent || 'ce réglage'));
  o.hidden = true; o.after(s); s.focus(); s.select();
  let fini = false;
  const finir = (garder) => {
    if(fini) return; fini = true;
    const v = parseFloat(String(s.value).replace(',', '.'));
    s.remove(); o.hidden = false;
    if(!garder || !Number.isFinite(v)) return;
    const min = +r.min || 0, max = r.max === '' ? 100 : +r.max, pas = +r.step || 1;
    r.value = String(Math.min(max, Math.max(min, Math.round(v / pas) * pas)));
    r.dispatchEvent(new Event('input', { bubbles: true }));
    r.dispatchEvent(new Event('change', { bubbles: true }));
  };
  s.addEventListener('keydown', (e) => { if(e.key === 'Enter'){ e.preventDefault(); finir(true); } else if(e.key === 'Escape'){ e.preventDefault(); finir(false); } });
  s.addEventListener('blur', () => finir(true));
}
document.addEventListener('click', (e) => {
  const o = e.target.closest('.mot-ligne output');
  if(o) motSaisieOuvrir(o);
});
document.addEventListener('keydown', (e) => {
  const o = e.target.closest && e.target.closest('.mot-ligne output');
  if(o && (e.key === 'Enter' || e.key === ' ')){ e.preventDefault(); motSaisieOuvrir(o); }
});
/* la bibliothèque de formes */""")
rep('style.css', ".mot-ligne output{ width:44px; text-align:right; font-family:var(--titre, 'Big Shoulders Display'), Impact, sans-serif; font-weight:700; font-size:1rem; }",
""".mot-ligne output{ width:44px; text-align:right; font-family:var(--titre, 'Big Shoulders Display'), Impact, sans-serif; font-weight:700; font-size:1rem; }
.mot-ligne output{ cursor:text; border-radius:6px; padding:2px 4px; background:rgba(255,255,255,.06); border-bottom:1px dashed rgba(255,255,255,.35); }   /* patch515 : on peut taper la valeur */
.mot-saisie{ width:52px; flex:none; text-align:right; font:inherit; font-family:var(--titre, 'Big Shoulders Display'), Impact, sans-serif; font-weight:700; font-size:1rem; color:inherit; background:rgba(0,0,0,.35); border:1px solid var(--mor, #F2B92C); border-radius:6px; padding:2px 4px; -moz-appearance:textfield; }
.mot-saisie::-webkit-outer-spin-button, .mot-saisie::-webkit-inner-spin-button{ -webkit-appearance:none; margin:0; }""")
# accessibilité : les chiffres se focalisent au clavier
rep('app.js', "  motEl('motBForme').onclick = () => motOuvrirFormes(ME.sel);",
              "  motEl('motBForme').onclick = () => motOuvrirFormes(ME.sel);\n  b.querySelectorAll('.mot-ligne output').forEach(o => { o.tabIndex = 0; o.title = 'Toucher pour taper une valeur'; });   // patch515")

p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
if d[0].get('date') != '2026-11-23': d.insert(0, {'date': '2026-11-23', 'nouveautes': []})
e = d[0]; e.setdefault('nouveautes', [])
l = "🎨 Motifs : touche le chiffre à droite d'un curseur (taille, rotation, opacité, position…) pour taper la valeur exacte. La rotation se règle maintenant au degré près. Idée d'Arkhannou."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
