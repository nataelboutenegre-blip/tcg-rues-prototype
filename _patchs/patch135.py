# -*- coding: utf-8 -*-
u"""
patch135 — Combat plus léger (latences signalées par les joueurs, 17 octobre).

Constat (vidéos de joueurs) : après CHAQUE assaut depuis l'onglet Combat, le
jeu rechargeait toute la liste des cibles (toutes les possessions des autres
joueurs, par pages, avec les communes), puis le solde, les paquets et les
objectifs ; après une conquête, en plus, toute sa collection et toutes les
possessions des autres. En enchaînant les assauts, ces rechargements se
chevauchaient : liste qui disparaît et revient, boutons « Attaquer » encore
actifs sur une cible en attente (« Tu dois attendre encore un peu »), et
requêtes coupées par le téléphone (« TypeError: Load failed »).

1. Après un assaut, la carte visée est mise à jour sur place à partir de la
   réponse du serveur (série, prochain round), sans rien recharger. Le solde
   se relit seul (un appel).
2. Le rechargement complet (liste, paquets, objectifs, et après une conquête
   la collection et la carte) part une seule fois, 8 s après le DERNIER
   assaut : enchaîner dix assauts ne fait plus qu'un rechargement.
3. Ouvrir l'onglet Combat affiche tout de suite la liste déjà connue ; elle
   ne se recharge que si elle date de plus d'une minute (et en arrière-plan).
4. « Load failed » (iPhone) et « Failed to fetch » : message clair.
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
js = lire('app.js')
assert 'combatRafraichirPlusTard' not in js, u'patch135 deja applique'

# 4. message
js = rempl(js, u"""    [/failed to fetch|network/i, 'Connexion impossible. Vérifie ta connexion internet.'],""",
u"""    [/load failed|failed to fetch|network/i, 'Connexion interrompue. Vérifie ta connexion, puis réessaie.'],""", u'message')

# 1 + 2. apres un assaut
js = rempl(js, u"""        mettreEnSceneAssaut(cibleVueCombat, result);
        if(result.conquise){
          await loadMyCollection();
          await loadOthersPossessions();
        }
        await loadCombat();
        loadPackStatus();
        loadObjectifs();
      } finally {
        combatActionEnCours = false;
      }
      return;""", u"""        mettreEnSceneAssaut(cibleVueCombat, result);
        // patch135 : la carte se met a jour sur place, le reste plus tard
        combatApresAssaut(code, result);
      } catch(err){
        // connexion coupee : l'assaut a pu passer, la liste se relira
        combatRafraichirPlusTard(false);
        throw err;
      } finally {
        combatActionEnCours = false;
      }
      return;""", u'apres assaut')

js = rempl(js, u"""// ---------- Combat ----------
// Ces deux valeurs doivent rester alignees avec le SQL""", u"""// ---------- patch135 : Combat plus leger ----------
let combatChargeLe = 0;
let combatRafraichTimer = null, combatConquisePendante = false;
// la reponse du serveur suffit a mettre la carte a jour : pas de rechargement
function combatApresAssaut(code, r){
  const s = combatSieges.get(code) || { commune_code: code, victoires_consecutives: 0 };
  s.victoires_consecutives = r.conquise ? 0 : Number(r.victoires_consecutives || 0);
  s.dernier_round = new Date().toISOString();
  combatSieges.set(code, s);
  if(r.conquise){
    combatCibles = combatCibles.filter(c => c.commune_code !== code);
    combatSieges.delete(code);
    othersMap.delete(code);
  }
  renderCombatGrid();
  monEtat().then(row => {
    if(!row) return;
    ['soldeValueCombat', 'soldeValueDefense'].forEach(id => { const el = document.getElementById(id); if(el) el.textContent = row.solde; });
  });
  combatRafraichirPlusTard(!!r.conquise);
}
// un seul rechargement complet, 8 s apres le dernier assaut
function combatRafraichirPlusTard(conquise){
  if(conquise) combatConquisePendante = true;
  clearTimeout(combatRafraichTimer);
  combatRafraichTimer = setTimeout(async () => {
    combatRafraichTimer = null;
    if(combatActionEnCours){ combatRafraichirPlusTard(false); return; }
    const avecConquete = combatConquisePendante;
    combatConquisePendante = false;
    if(avecConquete){ await loadMyCollection(); await loadOthersPossessions(); renderMapOverlay(); }
    await loadCombat();
    loadPackStatus();
    loadObjectifs();
  }, 8000);
}

// ---------- Combat ----------
// Ces deux valeurs doivent rester alignees avec le SQL""", u'fonctions')

# horodatage du chargement
js = rempl(js, u"""  calculerDistancesCibles();
  loadMenaces();
  combatSieges = new Map((mesSieges || []).map(s => [s.commune_code, s]));
  renderCombatGrid();
  demanderChances();
}""", u"""  calculerDistancesCibles();
  loadMenaces();
  combatSieges = new Map((mesSieges || []).map(s => [s.commune_code, s]));
  combatChargeLe = Date.now();   // patch135
  renderCombatGrid();
  demanderChances();
}""", u'horodatage')

# 3. ouverture de l'onglet
js = rempl(js, u"""    if(tab.dataset.tab === 'combat') loadCombat();""", u"""    if(tab.dataset.tab === 'combat'){
      // patch135 : la liste connue s'affiche tout de suite ; rechargee si elle a plus d'une minute
      if(combatCibles.length) renderCombatGrid();
      if(!combatRafraichTimer && Date.now() - combatChargeLe > 60000) loadCombat();
    }""", u'onglet')

ecrire('app.js', js)
print(u'patch135 applique')
