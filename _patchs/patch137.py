# -*- coding: utf-8 -*-
u"""
patch137 — un bandeau d'annonce en haut du jeu (maintenance, nouveautés).
Le texte vient du serveur (fonction annonce(), _sql/annonce.sql) : on
l'affiche ou on l'enlève sans pousser de code. Relu toutes les 5 minutes
quand le jeu est à l'écran. Le joueur peut le fermer (une fois par texte).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)
js = lire('app.js'); css = lire('style.css'); html = lire('index.html')
assert 'chargerAnnonce' not in js, u'patch137 deja applique'

html = rempl(html, u"""    <div class="saison-bandeau" id="saisonBandeau" hidden>""", u"""    <div class="annonce-bandeau" id="annonceBandeau" role="status" hidden><span id="annonceTexte"></span><button type="button" id="annonceFermer" aria-label="Fermer l'annonce">&times;</button></div>
    <div class="saison-bandeau" id="saisonBandeau" hidden>""", u'bandeau')

js = rempl(js, u"""  demarrerPresence(session_.user.id);   // patch127""", u"""  demarrerPresence(session_.user.id);   // patch127
  chargerAnnonce();   // patch137""", u'demarrage')

js = rempl(js, u"""// ---------- patch122 : ecran de chargement ----------""", u"""// ---------- patch137 : bandeau d'annonce ----------
async function chargerAnnonce(){
  let texte = null;
  try{ const { data, error } = await sb.rpc('annonce'); if(!error) texte = data; }catch(e){}
  const el = document.getElementById('annonceBandeau');
  if(!el) return;
  let fermee = null;
  try{ fermee = localStorage.getItem('tf-annonce-fermee'); }catch(e){}
  if(!texte || fermee === texte){ el.hidden = true; return; }
  document.getElementById('annonceTexte').textContent = texte;
  el.dataset.texte = texte;
  el.hidden = false;
}
document.getElementById('annonceFermer').addEventListener('click', () => {
  const el = document.getElementById('annonceBandeau');
  try{ localStorage.setItem('tf-annonce-fermee', el.dataset.texte || ''); }catch(e){}
  el.hidden = true;
});
setInterval(() => { if(!document.hidden && window.__monId) chargerAnnonce(); }, 5 * 60 * 1000);

// ---------- patch122 : ecran de chargement ----------""", u'fonction')

css += u"""
/* ---------- patch137 : bandeau d'annonce ---------- */
.annonce-bandeau{ display:flex; align-items:flex-start; gap:12px; margin:0 0 14px; padding:11px 14px; border-radius:12px;
  background: rgba(240,180,41,.12); border:1px solid rgba(240,180,41,.45); color:#fff; font-size:.92rem; line-height:1.45; }
.annonce-bandeau[hidden]{ display:none; }
.annonce-bandeau span{ flex:1; }
.annonce-bandeau button{ flex:none; background:none; border:0; color: var(--brume); font-size:20px; line-height:1; cursor:pointer; padding:0 2px; }
.annonce-bandeau button:hover{ color:#fff; }
"""
ecrire('app.js', js); ecrire('style.css', css); ecrire('index.html', html)
print(u'patch137 applique')
