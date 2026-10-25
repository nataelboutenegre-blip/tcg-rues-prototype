# -*- coding: utf-8 -*-
u"""
patch193 — QG : le classement passe sous le jeu choisi, replie par defaut
(on le deplie d'un toucher) ; les dernieres parties restent a droite.
L'etat ouvert / ferme est retenu. Aucun SQL.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)

js = lire('app.js')
assert 'qgClOuvert' not in js, u'patch193 deja applique'
js = rempl(js, u"""    const cl = document.getElementById('qgClassement');
    if(cl && cl.closest('.qg-carte')) cl.closest('.qg-carte').id = 'qgClassementBloc';""",
u"""    const cl = document.getElementById('qgClassement');
    if(cl && cl.closest('.qg-carte')){
      const bloc = cl.closest('.qg-carte');
      bloc.id = 'qgClassementBloc';
      // patch193 : un menu deroulant, replie par defaut
      const ligne = bloc.querySelector('.qg-h3-ligne');
      if(ligne){
        const bouton = document.createElement('button');
        bouton.type = 'button';
        bouton.className = 'qg-cl-bascule';
        bouton.setAttribute('aria-controls', 'qgClassement');
        bouton.innerHTML = '<h3 class="qg-h3">Classement</h3><svg class="qg-cl-chevron" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M5 8l5 5 5-5"/></svg>';
        ligne.replaceWith(bouton);
        bouton.addEventListener('click', () => {
          qgClOuvert = !qgClOuvert;
          try{ localStorage.setItem('tf-qg-cl-ouvert', qgClOuvert ? '1' : ''); }catch(err){}
          majClassementQG();
        });
      }
    }""", 'classement')
js = rempl(js, u"""function choixQG(){""", u"""let qgClOuvert = (() => { try{ return localStorage.getItem('tf-qg-cl-ouvert') === '1'; }catch(e){ return false; } })();   // patch193
function majClassementQG(){
  const bloc = document.getElementById('qgClassementBloc');
  if(!bloc) return;
  bloc.classList.toggle('replie', !qgClOuvert);
  const b = bloc.querySelector('.qg-cl-bascule');
  if(b) b.setAttribute('aria-expanded', String(qgClOuvert));
}
function choixQG(){""", 'etat')
js = rempl(js, u"""  const titreC = document.querySelector('#qgClassementBloc .qg-h3');
  if(titreC) titreC.innerHTML = `Classement <small>${nom}</small>`;
}""", u"""  const titreC = document.querySelector('#qgClassementBloc .qg-h3');
  if(titreC) titreC.innerHTML = `Classement <small>${nom}</small>`;
  majClassementQG();   // patch193
}""", 'fin choix')
ecrire('app.js', js)

css = lire('style.css')
assert 'patch193' not in css
css += u"""

/* ---------- patch193 : le classement sous le jeu, en menu deroulant ---------- */
.qg-choix-actif .qg-jeux{ grid-row:2; }
.qg-choix-actif #qgClassementBloc{ grid-column:1; grid-row:3; }
.qg-choix-actif #qgDerniersBloc{ grid-column:2; grid-row:2 / span 2; }
.qg-choix-actif #qgCdjNote{ grid-row:2 / span 2; }
.qg-cl-bascule{ display:flex; align-items:center; justify-content:space-between; gap:12px; width:100%; min-height:44px;
  background:none; border:0; padding:0; color:#fff; font:inherit; text-align:left; cursor:pointer; }
.qg-cl-bascule:focus-visible{ outline:2px solid var(--c-legendaire); outline-offset:4px; border-radius:6px; }
.qg-cl-bascule .qg-h3{ margin:0; }
.qg-cl-chevron{ width:20px; height:20px; color: var(--brume); flex:none; transition: transform .18s ease; }
.qg-cl-bascule[aria-expanded="true"] .qg-cl-chevron{ transform: rotate(180deg); color: var(--c-legendaire); }
#qgClassementBloc.replie #qgClassement{ display:none; }
#qgClassementBloc.replie{ gap:0; }
@media (prefers-reduced-motion: reduce){ .qg-cl-chevron{ transition:none; } }
@media (max-width: 900px){
  .qg-choix-actif .qg-jeux{ order:1; } .qg-choix-actif #qgClassementBloc{ order:2; }
  .qg-choix-actif #qgDerniersBloc, .qg-choix-actif #qgCdjNote{ order:3; grid-row:auto; }
  .qg-choix-actif #qgDefisBloc{ order:0; }
}
"""
ecrire('style.css', css)
print(u'patch193 applique. Lancer : python3 maj-version.py')
