# patch352 (5/11/2026) : la barre du bas reste au milieu de l'écran après le
# clavier, sur iPhone (signalé par un joueur sous iOS 27, le 5/11).
#
# Ce n'est pas un défaut du jeu : depuis iOS 26, Safari ne remet pas sa zone
# d'affichage en place quand le clavier se ferme, et les éléments fixés en bas
# de l'écran (notre barre d'onglets) restent décalés vers le haut. Corrigé dans
# iOS 26.1, revenu dans iOS 27 d'après les forums d'Apple (fil 800125).
#
# Contournement : sur iPhone et iPad seulement, quand un champ perd le focus
# (le clavier se ferme), quand la zone visible retrouve sa hauteur, et au
# retour dans le jeu, on fait défiler la page d'un pixel puis on la remet en
# place. Ça force Safari à recalculer la position de la barre. Rien ne change
# ailleurs, aucun SQL.
import pathlib, json

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch352' not in s, 'patch352 déjà appliqué'
s = s.rstrip('\n') + '\n' + r"""
// ---------- patch352 : la barre du bas décalée après le clavier (Safari iOS 26 et 27) ----------
// Safari ne remet pas sa zone d'affichage en place quand le clavier se ferme :
// la barre d'onglets, fixée en bas, reste au milieu de l'écran (capture
// d'un joueur sous iOS 27). On fait défiler la page d'un pixel puis on la remet en
// place, ce qui oblige Safari à recalculer la position des éléments fixés.
(function barreApresClavier(){
  const ua = navigator.userAgent || '';
  const ios = /iP(hone|ad|od)/.test(ua) || (/Macintosh/.test(ua) && (navigator.maxTouchPoints || 0) > 1);
  if(!ios) return;
  const CHAMP = 'input, textarea, select, [contenteditable="true"]';
  const vv = window.visualViewport;
  let minuteur = null;
  function recaler(){
    clearTimeout(minuteur);
    minuteur = setTimeout(() => {
      const a = document.activeElement;
      if(a && a.matches && a.matches(CHAMP)) return;   // le clavier est encore ouvert
      if(vv && vv.scale > 1.01) return;               // zoom à deux doigts : rien à corriger
      const x = window.scrollX, y = window.scrollY;
      window.scrollTo(x, y > 0 ? y - 1 : y + 1);
      requestAnimationFrame(() => window.scrollTo(x, y));
    }, 300);
  }
  document.addEventListener('focusout', (e) => {
    if(e.target && e.target.matches && e.target.matches(CHAMP)) recaler();
  }, true);
  if(vv){
    let avant = vv.height;
    vv.addEventListener('resize', () => {
      if(vv.height > avant + 80) recaler();   // la zone visible s'agrandit : le clavier vient de se fermer
      avant = vv.height;
    });
  }
  document.addEventListener('visibilitychange', () => { if(!document.hidden) recaler(); });
  window.addEventListener('pageshow', recaler);
})();
"""
F.write_text(s, encoding='utf-8')

# la ligne de la cloche (correctif du jour)
N = pathlib.Path('data/nouveautes.json')
d = json.loads(N.read_text(encoding='utf-8'))
assert d and d[0].get('date') == '2026-11-05', 'la première entrée n’est pas celle du 5/11'
ligne = 'Sur iPhone, la barre du bas pouvait rester au milieu de l’écran après avoir fermé le clavier (un défaut de Safari depuis iOS 26, revenu avec iOS 27). Le jeu la remet en place tout seul (signalé par Oshannir)'
d[0].setdefault('correctifs', [])
if ligne not in d[0]['correctifs']:
    d[0]['correctifs'].append(ligne)
N.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch352 appliqué')
