// patch433 : habillage « Topo » de la saison 3. Lu avant la feuille de style, pour ne pas montrer l'ancien habillage une fraction de seconde.
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
