# -*- coding: utf-8 -*-
u"""
patch205 — pastille rouge « nouveauté » sur l'onglet Boutique et sur le volet
« Objets TerraFront » : allumée tant qu'un objet en vente (que je n'ai pas)
n'a pas encore été vu ; elle s'éteint quand j'ouvre Objets TerraFront.
Mémoire par appareil (localStorage). Sur téléphone, suit aussi sur « Plus ».
Aucun SQL.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)

js = lire('app.js')
assert 'patch205' not in js
def rempl(avant, apres):
    global js
    assert js.count(avant) == 1, (js.count(avant), avant[:70])
    js = js.replace(avant, apres)

rempl(u"""  const v = document.getElementById('bqVolets');
  if(v) v.hidden = !bqeAcces;
}
""", u"""  const v = document.getElementById('bqVolets');
  if(v) v.hidden = !bqeAcces;
  majPastilleBoutique();   // patch205
}

// ---------- patch205 : pastille « nouveauté » sur la Boutique ----------
function bqeEnVente(){
  const cat = bqeCat;
  return ((cat && cat.articles) || [])
    .filter(a => a.type !== 'pass' && !a.possede && (!a.reserve_og || cat.og))
    .map(a => a.id);
}
function bqeVus(){
  try{ const v = JSON.parse(localStorage.getItem('tf-bqe-vus') || '[]'); return Array.isArray(v) ? v : []; }catch(e){ return []; }
}
function majPastilleBoutique(){
  const vus = bqeVus();
  const nouveau = !!bqeAcces && bqeEnVente().some(id => !vus.includes(id));
  const tab = document.querySelector('.tab[data-tab="boutique"]');
  if(tab){
    let b = tab.querySelector('.tab-badge.bq-nouveau');
    if(!b && nouveau){ b = document.createElement('span'); b.className = 'tab-badge point bq-nouveau'; b.setAttribute('aria-label', 'Nouveautés dans la boutique'); tab.appendChild(b); }
    if(b) b.hidden = !nouveau;
  }
  const v = document.querySelector('.volet[data-volet="boutiqueeuros"]');
  if(v){
    let p = v.querySelector('.volet-point');
    if(!p && nouveau){ p = document.createElement('span'); p.className = 'volet-point'; p.setAttribute('aria-label', 'nouveau'); v.appendChild(p); }
    if(p) p.hidden = !nouveau;
  }
  try{ majBadgePlus(); }catch(e){}
}
// j'ai ouvert Objets TerraFront : tout ce qui est en vente est vu
function bqeMarquerVus(){
  try{ localStorage.setItem('tf-bqe-vus', JSON.stringify([...new Set([...bqeVus(), ...bqeEnVente()])])); }catch(e){}
  majPastilleBoutique();
}
""")
rempl(u"""bqeCommandes = m.error ? [] : (m.data || []);
  renderBoutiqueEuros();""", u"""bqeCommandes = m.error ? [] : (m.data || []);
  renderBoutiqueEuros();
  bqeMarquerVus();   // patch205""")
# sur téléphone, la Boutique peut être dans « Plus » : la pastille y suit
rempl(u"""  } else {
    cible.hidden = !cdjAJouer;
    cible.textContent = cdjAJouer ? '1' : '';
  }""", u"""  } else {
    // patch205 : une nouveauté en boutique, quand la Boutique est dans le menu
    const bq = document.querySelector('.tab[data-tab="boutique"] .bq-nouveau');
    const bqMenu = surTelephone() && ONGLETS_MENU.includes('boutique') && bq && !bq.hidden;
    cible.hidden = !(cdjAJouer || bqMenu);
    cible.textContent = cdjAJouer ? '1' : '';
    cible.classList.toggle('point', !cdjAJouer && !!bqMenu);
  }""")
ecrire('app.js', js)

css = lire('style.css')
assert 'patch205' not in css
css = css.rstrip('\n') + u"""

/* ---------- patch205 : pastille « nouveauté » (un point, sans chiffre) ---------- */
.tab-badge.point{ min-width: 10px; width: 10px; height: 10px; padding: 0; }
.volet-point{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--c-rouge); margin-left: 7px; vertical-align: middle; flex: none; }
.volet-point[hidden]{ display: none; }
"""
ecrire('style.css', css)
print(u'patch205 applique. Lancer : python3 maj-version.py')
