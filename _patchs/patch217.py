# -*- coding: utf-8 -*-
u"""
patch217 — Content-Security-Policy + sortie des onerror inline + apostrophe échappée
(audit sécurité 26-27 oct). index.html n'a aucun script/handler inline ; les
seules origines externes sont Supabase. La CSP bloque l'exécution de tout script
injecté (défense contre une future faille d'injection), sans 'unsafe-eval'
(d3 n'utilise sa lecture CSV — seule à faire du new Function — jamais au runtime).
Les 5 onerror= de repli d'image deviennent un gestionnaire global (sinon la CSP
les bloquerait). echapperTexte/echapperHtml échappent aussi l'apostrophe.
Testé au banc : 0 violation CSP, scripts/styles/SW OK, repli d'image identique.
Sans SQL.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rep(s, a, b, n=1):
    c = s.count(a); assert c == n, ('MATCH', a[:70], 'trouve', c, 'attendu', n); return s.replace(a, b)

js = lire('app.js')
assert 'patch217' not in js, 'deja applique'
js = rep(js,
  u"""/[&<>"]/g, ch => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;'}[ch])""",
  u"""/[&<>"']/g, ch => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[ch])""",
  n=2)
js = rep(js,
  u"""function echapperTexte(s){
  return String(s == null ? '' : s).replace""",
  u"""// patch217 : repli d'image cassee sans gestionnaire inline (compatible CSP)
window.addEventListener('error', function(ev){
  var t = ev.target;
  if(!(t instanceof HTMLImageElement) || !t.dataset || !t.dataset.onfail) return;
  if(t.dataset.onfail === 'next' && t.nextElementSibling) t.nextElementSibling.remove();
  t.remove();
}, true);
function echapperTexte(s){
  return String(s == null ? '' : s).replace""")
js = rep(js, u'onerror="this.nextElementSibling&&this.nextElementSibling.remove();this.remove()"', u'data-onfail="next"', n=1)
js = rep(js, u'onerror="this.remove()"', u'data-onfail="1"', n=4)
ecrire('app.js', js)

h = lire('index.html')
assert 'Content-Security-Policy' not in h, 'CSP deja presente'
CSP = ("default-src 'self'; "
       "script-src 'self'; "
       "style-src 'self' 'unsafe-inline'; "
       "img-src 'self' data: https://yzcgroprydxhbwaufkdu.supabase.co; "
       "font-src 'self'; "
       "connect-src 'self' https://yzcgroprydxhbwaufkdu.supabase.co wss://yzcgroprydxhbwaufkdu.supabase.co; "
       "media-src 'self' data:; "
       "worker-src 'self'; manifest-src 'self'; "
       "object-src 'none'; base-uri 'none'; form-action 'self'")
h = rep(h, u'<meta charset="UTF-8">', u'<meta charset="UTF-8">\n<meta http-equiv="Content-Security-Policy" content="' + CSP + u'">', n=1)
ecrire('index.html', h)
print('patch217 ok')
