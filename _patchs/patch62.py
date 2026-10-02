# -*- coding: utf-8 -*-
u"""
patch62 — Le bandeau de fin de saison, et la barre des favoris qui se tait
          jusque-la.

L'IDEE VIENT D'OSHANNIR
  « Mettre ca uniquement quand la fin de saison est annoncee et qu'il reste
  que quelques jours, car entre temps les cartes ca va ca vient. »

  Il a raison, et le chiffre le prouve : a la simulation de cloture du
  1er octobre, 6 favoris etaient marques sur 115 possibles — 22 joueurs sur
  23 n'avaient rien choisi. La barre reclame tous les jours une action que
  presque personne ne fait, et pour une bonne raison : a deux mois de la
  fin, marquer une commune qu'on peut perdre demain n'a aucun sens.

  La cacher ne coute rien a personne : la cloture complete automatiquement,
  un joueur qui n'a rien marque garde quand meme ses cinq meilleures, et la
  regle d'une seule legendaire est respectee depuis le correctif du
  1er octobre. L'etoile reste disponible toute l'annee sur la fiche pour qui
  veut choisir a l'avance.

CE QUE CE PATCH FAIT D'AUTRE, ET C'EST LE PLUS IMPORTANT
  Il allume le mecanisme de saison, qui etait installe mais inerte.

  saison_courante() est la fonction qui arme le compte a rebours quand le
  seuil de communes libres est franchi. Elle existe en base depuis le
  1er octobre — et RIEN NE L'APPELAIT. Le compte a rebours ne pouvait donc
  jamais se declencher : la saison 1 serait restee ouverte indefiniment.

  Le jeu l'appelle maintenant au demarrage. C'est sans danger aujourd'hui :
  il reste environ 28 000 communes libres pour un seuil de 3 000. Le jour ou
  le seuil sera franchi, le premier joueur qui ouvrira le jeu armera le
  compte a rebours, ce qui est exactement le fonctionnement prevu.

LE BANDEAU
  Visible seulement pendant le compte a rebours, en haut de tous les
  onglets. Il dit le temps restant, la regle des cinq communes, et mene a
  la Collection pour choisir. Les dernieres 24 heures, il annonce aussi que
  les boucliers ne protegent plus.

  Il ne se ferme pas. Cinq jours, et c'est la seule echeance du jeu qui
  fasse perdre des cartes : un joueur qui le masque et l'oublie perdrait
  pour de bon.

SI LA FONCTION NE REPOND PAS
  Pas de bandeau, et la barre des favoris reste cachee. On ne sait pas si on
  est en fin de saison, donc on n'annonce rien — et comme la cloture
  complete toute seule, personne ne perd quoi que ce soit.
"""
import io, os

BASE = os.path.dirname(os.path.abspath(__file__))

def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f:
        return f.read()

def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f:
        f.write(s)

def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)


# ===========================================================================
#  index.html
# ===========================================================================
html = lire('index.html')

html = rempl(html,
u"""    </div>


    <section class="tab-panel active" id="panel-tirage">""",
u"""    </div>

    <div class="saison-bandeau" id="saisonBandeau" hidden>
      <div class="sb-txt">
        <b id="sbTitre"></b>
        <span id="sbTexte"></span>
      </div>
      <button class="sb-btn" id="sbChoisir">Choisir mes cinq</button>
    </div>


    <section class="tab-panel active" id="panel-tirage">""",
u'le bandeau de fin de saison')

ecrire('index.html', html)


# ===========================================================================
#  app.js
# ===========================================================================
js = lire('app.js')

js = rempl(js,
u"""function majBarreFavoris(){""",
u"""// ---------- La fin de saison ----------
// saison_courante() fait deux choses : elle dit ou en est la saison, et elle
// ARME le compte a rebours quand le seuil de communes libres est franchi.
// Rien ne l'appelait jusqu'ici : le mecanisme etait installe mais inerte, et
// la saison 1 serait restee ouverte indefiniment.
let saisonEtat = null;
let saisonMinuteur = null;

const enFinDeSaison = () => !!(saisonEtat && saisonEtat.etat === 'compte_a_rebours');

// showGame() est appelee deux fois au demarrage (getSession, puis
// onAuthStateChange) : sans ce garde-fou, saison_courante() tournerait deux
// fois, et elle compte les 34 739 communes et toutes les possessions a chaque
// appel. On retient la promesse en cours, comme loadOutline() le fait deja.
let saisonEnCours = null;
function chargerSaison(){
  if(!saisonEnCours) saisonEnCours = lireSaison();
  return saisonEnCours;
}

async function lireSaison(){
  const { data, error } = await sb.rpc('saison_courante');
  if(error){
    // on ne sait pas ou on en est : on n'annonce rien plutot que d'annoncer
    // a tort une fin de saison
    console.warn('TERRAFRONT saison indisponible', error);
    saisonEtat = null;
  } else {
    saisonEtat = (data && data[0]) || null;
  }
  renderSaison();
  majBarreFavoris();
}

// « 4 j 7 h », « 7 h 20 min », « 12 min »
function dureeRestante(ms){
  if(ms <= 0) return 'quelques instants';
  const min = Math.floor(ms / 60000);
  const h = Math.floor(min / 60);
  const j = Math.floor(h / 24);
  if(j >= 1) return j + ' j ' + (h % 24) + ' h';
  if(h >= 1) return h + ' h ' + (min % 60) + ' min';
  return min + ' min';
}

function renderSaison(){
  const bandeau = document.getElementById('saisonBandeau');
  if(!bandeau) return;
  if(!enFinDeSaison()){
    bandeau.hidden = true;
    if(saisonMinuteur){ clearInterval(saisonMinuteur); saisonMinuteur = null; }
    return;
  }
  bandeau.hidden = false;
  const fin = saisonEtat.fin_prevue ? new Date(saisonEtat.fin_prevue).getTime() : 0;
  const titre = document.getElementById('sbTitre');
  const texte = document.getElementById('sbTexte');
  if(titre) titre.textContent = fin
    ? 'Fin de saison dans ' + dureeRestante(fin - Date.now())
    : 'La saison se termine';
  if(texte) texte.innerHTML = 'Tu gardes <b>cinq communes</b>, dont <b>une seule légendaire</b>. '
    + 'Tout le reste retourne au pot.'
    + (saisonEtat.sans_bouclier
       ? ' <b>Dernières 24 heures : les boucliers ne protègent plus.</b>' : '');
  // le compte a rebours doit descendre sous les yeux du joueur, sinon il
  // croit l'ecran fige
  if(!saisonMinuteur) saisonMinuteur = setInterval(renderSaison, 60000);
}

document.getElementById('sbChoisir').addEventListener('click', () => {
  const tab = document.querySelector('.tab[data-tab="collection"]');
  if(tab) tab.click();
});


function majBarreFavoris(){""",
u'le bandeau de fin de saison en JS')

# --- la barre des favoris ne repete plus la regle ---------------------------
# Sur la Collection les deux se suivent, et disaient la meme phrase : « cinq
# communes gardees, une seule legendaire, le reste retourne au pot ». Le
# bandeau l'explique, partout ; la barre compte, la ou on choisit.
js = rempl(js,
u"""  if(elT) elT.innerHTML = n >= FAV_MAX
    ? 'communes gard\u00e9es \u00e0 la fin de la saison. Retire une \u00e9toile pour en changer.'
    : 'communes gard\u00e9es \u00e0 la fin de la saison \u2014 le reste retourne au pot. '
      + '<b>Une seule l\u00e9gendaire</b> parmi les cinq.';""",
u"""  if(elT) elT.innerHTML = n >= FAV_MAX
    ? 'communes choisies. Retire une \u00e9toile pour en changer.'
    : 'communes choisies. Clique l\u2019\u00e9toile d\u2019une carte pour la garder.';""",
u'la barre des favoris ne repete plus la regle')

# --- la barre des favoris attend la fin de saison --------------------------
js = rempl(js,
u"""  if(!favorisCharges || vueCollection === 'france'){ barre.hidden = true; return; }
  const n = favorisSet.size;""",
u"""  if(!favorisCharges || vueCollection === 'france'){ barre.hidden = true; return; }
  // Avant le compte a rebours, elle reclamerait tous les jours un choix qui
  // n'a pas de sens : les communes changent de mains entre-temps, et la
  // cloture complete toute seule pour qui n'a rien marque. L'etoile reste
  // disponible sur la fiche pour qui veut choisir a l'avance.
  if(!enFinDeSaison()){ barre.hidden = true; return; }
  const n = favorisSet.size;""",
u'la barre des favoris attend la fin de saison')

# --- chargee au demarrage ---------------------------------------------------
js = rempl(js,
u"""  chargerEchangesEnCours();
  verifierVersion();""",
u"""  chargerEchangesEnCours();
  // c'est cet appel qui arme le compte a rebours le jour ou le seuil est
  // franchi : sans lui le mecanisme de saison ne se declenche jamais
  chargerSaison();
  verifierVersion();""",
u'la saison lue au demarrage')

ecrire('app.js', js)


# ===========================================================================
#  style.css
# ===========================================================================
css = lire('style.css')

css += (
u"""
  /* ---------- Le bandeau de fin de saison ----------
     Il ne se ferme pas : cinq jours, et c'est la seule echeance du jeu qui
     fasse perdre des cartes. Un joueur qui le masque et l'oublie perdrait
     pour de bon. */
  .saison-bandeau{
    display:flex; align-items:center; gap:14px; flex-wrap:wrap;
    width:100%; max-width:980px; margin: 0 0 18px; padding: 12px 16px;
    border:1px solid rgba(240,180,41,0.45); border-radius:14px;
    background: linear-gradient(100deg, rgba(240,180,41,0.16), rgba(240,180,41,0.06));
  }
  .saison-bandeau[hidden]{ display:none; }
  .sb-txt{ flex:1; min-width:220px; display:flex; flex-direction:column; gap:3px; }
  .sb-txt b{ font-family: var(--titre); font-weight:800; font-size:1.2rem;
             letter-spacing:.3px; color: var(--c-legendaire); }
  .sb-txt > span{ font-size:0.82rem; line-height:1.5; color:#E7EDF6; }
  .sb-btn{
    flex-shrink:0; padding:9px 18px; border-radius:10px; cursor:pointer;
    border:0; background: var(--c-legendaire); color:#231a04;
    font:inherit; font-size:0.88rem; font-weight:700;
    box-shadow: 0 3px 0 #B7791F;
  }
  .sb-btn:active{ transform: translateY(2px); box-shadow: 0 1px 0 #B7791F; }
  @media (max-width: 560px){
    .saison-bandeau{ padding:10px 12px; gap:10px; }
    .sb-txt b{ font-size:1.05rem; }
    .sb-btn{ width:100%; }
  }
""")

ecrire('style.css', css)
print(u'patch62 applique.')
