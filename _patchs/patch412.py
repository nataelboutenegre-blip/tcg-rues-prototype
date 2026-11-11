# patch412 (11/11/2026) : « Qui possède ta commune ? » (s3-9), la fiche publique sur la page d'accueil, sans compte
#  - page d'accueil : un bouton dans le haut, une section avec la recherche et la fiche (propriétaire, clan, depuis quand,
#    nombre de prises de la saison, petite carte des 12 km autour, « Viens la reprendre » / « Viens la conquérir », « Partager ») ;
#  - adresse terrafront.fr/?c=cognac-16 : un visiteur sans compte arrive sur la fiche ;
#  - après inscription ou connexion : la carte du Front sur la commune (fiche ouverte) si elle est tenue, le Tirage du Front sinon.
import sys, os
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, I, C = 'app.js', 'index.html', 'style.css'
ICI = os.path.dirname(os.path.abspath(__file__))
if 'patch412' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')

rep(I, """          <span>Trouve une commune mystère en six essais, sans t'inscrire.</span>
        </div>""", """          <span>Trouve une commune mystère en six essais, sans t'inscrire.</span>
        </div>
        <div class="lp-invite lp-cp-invite"><!-- patch412 -->
          <button class="lp-invite-btn" data-cp-aller>Qui possède ta commune ?</button>
          <span>Tape ta ville et regarde qui la tient.</span>
        </div>""")
rep(I, """  <div class="lp-sec">
    <div class="lp-wrap">
      <h2 class="lp-h2">Comment ça marche</h2>""", """  <div class="lp-sec lp-cp" id="lpCp"><!-- patch412 : « Qui possède ta commune ? » -->
    <div class="lp-wrap">
      <h2 class="lp-h2">Qui possède ta commune ?</h2>
      <p class="lp-sous">Sur TerraFront, chaque commune de France est une carte, et une seule personne peut la tenir. Tape ta ville pour savoir qui, et depuis quand.</p>
      <div class="cp-cherche">
        <input type="search" id="cpRecherche" class="cp-input" placeholder="Ta commune : Cognac, Lille, Saint-Denis…" autocomplete="off" enterkeyhint="search" aria-label="Ta commune">
        <ul class="cp-resultats" id="cpResultats" hidden></ul>
      </div>
      <div class="cp-fiche" id="cpFiche" hidden></div>
    </div>
  </div>

  <div class="lp-sec">
    <div class="lp-wrap">
      <h2 class="lp-h2">Comment ça marche</h2>""")
rep(A, """  else if(dejaJoue()) showAuth();
  else montrerLanding();""", """  else if(cpRefUrl()){ montrerLanding(); cpOuvrir(cpRefUrl(), true); }   // patch412 : ?c=cognac-16
  else if(dejaJoue()) showAuth();
  else montrerLanding();""")

js = open(os.path.join(ICI, 'patch412-cp.js'), encoding='utf-8').read() + """
// une fois le jeu affiché (connexion, inscription, retour) : la commune gardée
(function(){
  const avant = showGame;
  showGame = async function(){ const r = await avant.apply(this, arguments); setTimeout(cpApresConnexion, 1200); return r; };
})();
"""
open(A, 'a', encoding='utf-8').write(js)
open(C, 'a', encoding='utf-8').write(open(os.path.join(ICI, 'patch412-cp.css'), encoding='utf-8').read())
print('patch412 OK')
