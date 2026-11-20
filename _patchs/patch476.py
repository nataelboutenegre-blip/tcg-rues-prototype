# patch476 : un interrupteur « Garder Terra / Front en haut » dans le menu Plus (téléphone, style S3).
# Allumé par défaut ; le choix est gardé sur l'appareil (localStorage tf-bascule-colle). Éteint : la bande part avec la page.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A = 'app.js'
rep(A, "function construireMenuPlus(){",
"""// patch476 : garder la bande Terra / Front en haut (choix sur l'appareil, oui par défaut)
function basculeColleVoulue(){ try{ return localStorage.getItem('tf-bascule-colle') !== '0'; }catch(e){ return true; } }
function basculeColleAppliquer(){ document.documentElement.classList.toggle('sans-colle', !basculeColleVoulue()); }
basculeColleAppliquer();
function basculeColleHtml(){
  if(!document.documentElement.classList.contains('topo') || !surTelephone()) return '';
  const on = basculeColleVoulue();
  return `<button class="fp-item fp-inter" data-bascule-colle role="switch" aria-checked="${on}"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M15.5 2.5l6 6-2.1.7-3.6 3.6.5 4.6-1.6 1.6-4.2-4.2L5 20.3 3.7 19l5.5-5.5L5 9.3l1.6-1.6 4.6.5 3.6-3.6z"/></svg><span>Garder Terra / Front en haut</span><i class="fp-switch${on ? ' on' : ''}"></i></button>`;
}
document.addEventListener('click', (e) => {
  const b = e.target.closest('[data-bascule-colle]'); if(!b) return;
  e.stopPropagation();
  const on = !basculeColleVoulue();
  try{ localStorage.setItem('tf-bascule-colle', on ? '1' : '0'); }catch(err){}
  basculeColleAppliquer();
  b.setAttribute('aria-checked', String(on)); b.querySelector('.fp-switch').classList.toggle('on', on);
}, true);

function construireMenuPlus(){""")
rep(A, """    <div class="fp-sep"></div>
    <button class="fp-item" data-aller="regles">${ICONE_REGLES}Règles du jeu</button>""",
"""    <div class="fp-sep"></div>${basculeColleHtml()}
    <button class="fp-item" data-aller="regles">${ICONE_REGLES}Règles du jeu</button>""")
rep('style.css', "  html.topo .mode-bascule button.terra{ min-width:0; }\n  /* patch474",
"""  html.topo .mode-bascule button.terra{ min-width:0; }
  /* patch476 : la bande ne reste pas en haut si le joueur l'a choisi (menu Plus) */
  html.topo.sans-colle .mode-bascule.colle{ position:absolute; top:14px; box-shadow:none; background:var(--t-surface); -webkit-backdrop-filter:none; backdrop-filter:none; }
  /* patch474""")
rep('style.css', ".fp-badge.dg-point{",
""".fp-item.fp-inter span{ flex:1; }   /* patch476 : l'interrupteur du menu Plus */
.fp-switch{ position:relative; flex:none; width:40px; height:24px; border-radius:12px; background:rgba(169,188,212,.25); transition:background .2s; }
.fp-switch::after{ content:''; position:absolute; top:3px; left:3px; width:18px; height:18px; border-radius:50%; background:#fff; transition:transform .2s; box-shadow:0 1px 3px rgba(0,0,0,.35); }
.fp-switch.on{ background:var(--t-or, #F0B429); }
.fp-switch.on::after{ transform:translateX(16px); }
.fp-badge.dg-point{""")
print('patch476 : fini')
