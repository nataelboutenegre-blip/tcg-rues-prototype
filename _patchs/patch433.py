# patch433 (15/11/2026) : habillage « Topo » de la saison 3 (direction A du 5/11, demande de Nataël du 15/11).
#  - topo.js (lu dans <head>, avant la feuille de style) pose html.topo : le 22/11 à 10 h (Paris),
#    ou tout de suite avec ?topo=test (?topo=non l'éteint, ?topo=auto revient à la date) ;
#    config_jeu 'interface'.topo = 0 l'éteint pour tout le monde (1 l'allume), lu par interface_options() ;
#  - les règles de l'habillage, toutes sous html.topo, à la fin de style.css ;
#  - « énergie » du sélecteur de mode dans son propre <span> (caché par l'habillage).
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, S, H = 'app.js', 'style.css', 'index.html'
if 'patch433' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')
TOPO_CSS = open(sys.argv[1], encoding='utf-8').read() if len(sys.argv) > 1 else sys.exit('usage : patch433.py chemin/topo.css')

rep(H, '<link rel="stylesheet" href="style.css?v=', '<script src="topo.js?v=1"></script><!-- patch433 : habillage Topo -->\n<link rel="stylesheet" href="style.css?v=')
rep(A, '<b id="mbEnergie">—</b>/ <span id="mbMax">50</span> énergie</span></button>`;',
       '<b id="mbEnergie">—</b>/ <span id="mbMax">50</span><span class="mb-u"> énergie</span></span></button>`;   // patch433 : « énergie » à part')
rep(A, """      IFACE.recap = Number(o.recap_arrivee) === 1;
""", """      IFACE.recap = Number(o.recap_arrivee) === 1;
      // patch433 : l'habillage Topo s'allume ou s'éteint pour tout le monde depuis la base
      if(o.topo !== undefined && o.topo !== null){
        const t = Number(o.topo) === 1;
        document.documentElement.classList.toggle('topo', t || (Number(o.topo) !== 0 && document.documentElement.classList.contains('topo')));
        try{ localStorage.setItem('tf-topo-serveur', String(Number(o.topo))); }catch(e){}
      } else { try{ localStorage.removeItem('tf-topo-serveur'); }catch(e){} }
""")
open(S, 'a', encoding='utf-8').write('\n' + TOPO_CSS)
open('topo.js', 'w', encoding='utf-8').write('''// patch433 : habillage « Topo » de la saison 3. Lu avant la feuille de style, pour ne pas montrer l'ancien habillage une fraction de seconde.
// Allumé le 22/11/2026 à 10 h (Paris). Sur cet appareil : ?topo=test l'allume, ?topo=non l'éteint, ?topo=auto revient à la date.
// Pour tout le monde : config_jeu 'interface'.topo = 0 l'éteint, 1 l'allume (gardé ici dans tf-topo-serveur au chargement suivant).
(function(){
  var force = null, serveur = null;
  try{
    var q = new URLSearchParams(location.search).get('topo');
    if(q === 'test') localStorage.setItem('tf-topo', '1');
    if(q === 'non') localStorage.setItem('tf-topo', '0');
    if(q === 'auto') localStorage.removeItem('tf-topo');
    force = localStorage.getItem('tf-topo');
    serveur = localStorage.getItem('tf-topo-serveur');
  }catch(e){}
  var date = Date.now() >= Date.UTC(2026, 10, 22, 9, 1);
  var on = force === '1' || (force !== '0' && serveur !== '0' && (date || serveur === '1'));
  if(on) document.documentElement.classList.add('topo');
})();
''')
print('patch433 OK')
