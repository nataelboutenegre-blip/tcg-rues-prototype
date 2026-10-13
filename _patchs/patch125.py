# -*- coding: utf-8 -*-
u"""
patch125 — Combat : la recherche trouve aussi les communes et peu communes
(signalé par Oshannir : « dans le 01 j'ai une seule carte »).

Cause : avec le filtre « Toutes », l'onglet Combat ne charge que les rares,
épiques et légendaires (patch95, pour la vitesse). Taper « 01 » ne montrait
donc que les rares de l'Ain. Et une commune libre ne s'attaque pas : elle se
tire dans un paquet. Rien ne le disait.

1. Dès qu'on tape une recherche (département, nom, joueur), les communes et
   peu communes sont chargées aussi (une fois, puis gardées).
2. Une ligne sous la liste explique ce qu'on voit :
   - « Toutes » sans recherche : seules les rares et plus sont affichées ;
   - avec une recherche : seules les communes qui ont un propriétaire
     s'attaquent, les libres se tirent dans les paquets.
"""
import io, os

ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI

def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f:
        return f.read()

def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f:
        f.write(s)

def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)

js = lire('app.js')
css = lire('style.css')
assert 'majAideCombat' not in js, u'patch125 deja applique'

# 1. une recherche charge aussi les communes et peu communes
js = rempl(js, u"""function combatBasVoulus(){
  if(COMBAT_TIERS_BAS.indexOf(combatFilterTier) >= 0) return [combatFilterTier];
  if(combatProximite && combatFilterTier === 'tous') return COMBAT_TIERS_BAS.slice();
  return [];
}""", u"""function combatBasVoulus(){
  if(COMBAT_TIERS_BAS.indexOf(combatFilterTier) >= 0) return [combatFilterTier];
  if(combatProximite && combatFilterTier === 'tous') return COMBAT_TIERS_BAS.slice();
  // patch125 : une recherche reduit la liste, on peut tout charger
  const champ = document.getElementById('combatSearch');
  if(combatFilterTier === 'tous' && champ && champ.value.trim()) return COMBAT_TIERS_BAS.slice();
  return [];
}""", u'bas voulus')

js = rempl(js, u"""document.getElementById('combatSearch').addEventListener('input', renderCombatGrid);""",
u"""document.getElementById('combatSearch').addEventListener('input', () => {
  // patch125 : la premiere recherche charge aussi les communes et peu communes
  if(combatBasVoulus().some(t => !combatBasCharges.has(t))) assurerCiblesBas();
  renderCombatGrid();
});""", u'recherche')

# 2. la ligne d'aide sous la liste
js = rempl(js, u"""function renderCombatGrid(){
  if(rendreALOuverture('combat', renderCombatGrid)) return;
  renderIntensite();""", u"""// patch125 : ce que la liste montre, et ce qu'elle ne montre pas
function majAideCombat(searchText){
  const grid = document.getElementById('combatGrid');
  if(!grid) return;
  let aide = document.getElementById('combatAide');
  if(!aide){
    aide = document.createElement('p');
    aide.id = 'combatAide';
    aide.className = 'combat-aide';
    grid.after(aide);
  }
  let texte = '';
  if(combatEnCours) texte = '';
  else if(searchText) texte = 'Seules les communes qui ont déjà un propriétaire s\\'attaquent. Les communes libres se tirent dans les paquets.';
  else if(combatFilterTier === 'tous' && !combatProximite) texte = '« Toutes » affiche les rares, épiques et légendaires. Pour les communes et peu communes, choisis leur filtre ou tape un département.';
  aide.textContent = texte;
  aide.hidden = !texte;
}

function renderCombatGrid(){
  if(rendreALOuverture('combat', renderCombatGrid)) return;
  renderIntensite();""", u'aide fonction')

js = rempl(js, u"""  const searchText = sansAccents(searchEl ? searchEl.value.trim() : '');

  if(combatBasChargement && combatBasVoulus().some(t => !combatBasCharges.has(t))){""",
u"""  const searchText = sansAccents(searchEl ? searchEl.value.trim() : '');
  majAideCombat(searchText);

  if(combatBasChargement && combatBasVoulus().some(t => !combatBasCharges.has(t))){""", u'aide appel')

css += u"""
/* ---------- patch125 : aide sous la liste du Combat ---------- */
.combat-aide{ margin:12px 2px 0; font-size:.8rem; line-height:1.5; color:var(--brume); max-width:70ch; }
.combat-aide[hidden]{ display:none; }
"""

ecrire('app.js', js)
ecrire('style.css', css)
print(u'patch125 applique')
