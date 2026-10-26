# -*- coding: utf-8 -*-
u"""
patch215 — l'e-mail n'est plus affiché en permanence (demande de Nataël :
« mode streamer »). En bas du menu, le pseudo remplace l'e-mail, pour tout le
monde. L'e-mail ne se voit plus que dans Profil, en bas, masqué
(n••••@gmail.com), avec « Afficher ». Sans SQL.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rep(s, a, b, n=1):
    c = s.count(a)
    assert c == n, (a[:90], c, n)
    return s.replace(a, b)

js = lire('app.js')
assert 'patch215' not in js
js = rep(js, u"""  document.getElementById('whoami').textContent = session_.user.email;
""", u"""  // patch215 : jamais l'e-mail à l'écran (lives, captures) : le pseudo à la place
  window.__monEmail = session_.user.email || '';
  document.getElementById('whoami').textContent = '';
  majWhoami(session_.user.id);
""")
js = rep(js, u"""function rafraichirPanneauProfil(){
  profilPanneau = null;""", u"""// patch215 : le pseudo en bas du menu, et l'e-mail masqué dans le profil
async function majWhoami(id){
  const el = document.getElementById('whoami');
  if(!el || !id) return;
  try{
    const { data, error } = await sb.rpc('profil_joueur', { p_joueur: id });
    const p = !error && (Array.isArray(data) ? data[0] : data);
    el.textContent = p && p.pseudo ? p.pseudo : '';
  }catch(e){}
}
function emailMasque(m){
  const [u, d] = String(m || '').split('@');
  if(!d) return '';
  return (u ? u.charAt(0) : '') + '\\u2022\\u2022\\u2022\\u2022@' + d;
}
document.addEventListener('click', (e) => {
  const b = e.target.closest('[data-pf-mail]');
  if(!b) return;
  const s = document.getElementById('pfMail');
  if(!s) return;
  const visible = b.dataset.pfMail === 'cacher';
  s.textContent = visible ? emailMasque(window.__monEmail) : window.__monEmail;
  b.dataset.pfMail = visible ? 'voir' : 'cacher';
  b.textContent = visible ? 'Afficher' : 'Masquer';
});

function rafraichirPanneauProfil(){
  if(window.__monId) majWhoami(window.__monId);   // patch215 : le pseudo a pu changer
  profilPanneau = null;""")
js = rep(js, u"""    <div class="pf-compte">
      <p class="pf-legal">""", u"""    <div class="pf-compte">
      ${window.__monEmail ? `<p class="pf-mail">Compte : <span id="pfMail">${echapperTexte(emailMasque(window.__monEmail))}</span> <button type="button" class="pf-mail-b" data-pf-mail="voir">Afficher</button></p>` : ''}
      <p class="pf-legal">""")
ecrire('app.js', js)
css = lire('style.css')
assert 'patch215' not in css
css += u"""
/* patch215 : e-mail masqué dans le profil */
.pf-mail{ margin:0 0 8px; font-size:.8rem; color:var(--brume); }
.pf-mail span{ color:#fff; }
.pf-mail-b{ font:inherit; font-size:.78rem; color:var(--brume); background:none; border:0; padding:0 0 0 6px; text-decoration:underline; cursor:pointer; }
"""
ecrire('style.css', css)
print('patch215 ok')
