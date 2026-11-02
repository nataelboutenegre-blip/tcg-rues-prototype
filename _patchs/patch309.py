# patch309 : « Comment c'est calculé ? » dans le classement (aperçu validé le 2/11 : « parfait »)
# Au bout de la légende « cartes · combats · territoires » (Communauté › Classement), un lien
# ouvre le détail du score juste au-dessus du podium : cartes (points par rareté), combats
# (+10 par victoire, limites), territoires (paliers par département, région). En mode Clans,
# la moyenne par membre actif. Fermé par défaut, le choix est gardé sur l'appareil.
# Les chiffres sont ceux des Règles (même barème, écrits ici aussi).
import json, pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch309' not in s

s = rep(s, """function blClassement(nom, l, grand){""",
"""// patch309 : le détail du calcul, sous la légende
let clCalcOuvert = (() => { try{ return localStorage.getItem('tf-cl-calcul') === '1'; }catch(e){ return false; } })();
const CL_CALC_FRONT = `<div class="cl-calc-l"><i class="sc-pt c"></i><div><b>Cartes</b><span>Chaque commune que tu tiens : commune <b>1</b> · peu commune <b>3</b> · rare <b>12</b> · épique <b>25</b> · légendaire <b>60</b>.</span></div></div>
  <div class="cl-calc-l"><i class="sc-pt co"></i><div><b>Combats</b><span><b>+10</b> par victoire : conquête, défense, garnison qui repousse. 10 par jour au plus, 2 par jour contre un même joueur. Acquis même si tu reperds la commune.</span></div></div>
  <div class="cl-calc-l"><i class="sc-pt t"></i><div><b>Territoires</b><span>Par département, ton meilleur palier : 5 % <b>+100</b> · 10 % <b>+200</b> · 25 % <b>+300</b> (seul en tête) · 50 % <b>+600</b> · 75 % <b>+900</b> · 100 % <b>+1&nbsp;400</b>. Région : <b>+1&nbsp;200</b> si plus de la moitié de ses départements sont à 10 % ou plus.</span></div></div>
  <p class="cl-calc-pied">Cartes et territoires se comptent en direct : perdre une commune fait baisser ton score. Les combats restent acquis.</p>`;
const CL_CALC_CLANS = `<p class="cl-calc-txt">Le nombre de communes du Front de chaque membre <b>actif</b> (jeu ouvert dans les 7 derniers jours), divisé par le nombre de membres actifs. Jamais le total : un gros clan n’a pas d’avantage, et un membre absent ne fait pas baisser son clan. Un clan est classé à partir de <b>3 membres</b>.</p>`;
// quoi : 'front', 'clans' ou null (rien à expliquer : palmarès, classement replié…)
function clCalcRendre(legende, quoi){
  let panneau = document.getElementById('clCalc');
  if(!panneau && legende){
    panneau = document.createElement('div');
    panneau.id = 'clCalc'; panneau.className = 'cl-calc';
    legende.after(panneau);
  }
  if(!legende || !panneau) return;
  if(!quoi){ legende.hidden = true; panneau.hidden = true; return; }
  const bouton = `<button type="button" class="cl-calc-btn" data-cl-calc aria-expanded="${clCalcOuvert}">${clCalcOuvert ? 'Masquer le calcul' : 'Comment c’est calculé ?'}</button>`;
  legende.innerHTML = (quoi === 'clans' ? 'Moyenne par membre actif'
    : '<i class="sc-pt c"></i>cartes <i class="sc-pt co"></i>combats <i class="sc-pt t"></i>territoires') + bouton;
  legende.hidden = false;
  panneau.hidden = !clCalcOuvert;
  if(clCalcOuvert) panneau.innerHTML = quoi === 'clans' ? CL_CALC_CLANS : CL_CALC_FRONT;
}
document.addEventListener('click', (e) => {
  if(!e.target.closest('[data-cl-calc]')) return;
  clCalcOuvert = !clCalcOuvert;
  try{ localStorage.setItem('tf-cl-calcul', clCalcOuvert ? '1' : '0'); }catch(err){}
  renderClassement();
});

function blClassement(nom, l, grand){""")

# mode Clans : la légende explique la moyenne (au lieu de disparaître)
s = rep(s, """function renderClassementClans(podium, liste, plus){
  const leg = document.getElementById('clLegende');
  if(leg) leg.hidden = true;""",
"""function renderClassementClans(podium, liste, plus){
  let leg = document.getElementById('clLegende');
  if(!leg && podium){ leg = document.createElement('p'); leg.id = 'clLegende'; leg.className = 'sc-legende'; podium.before(leg); }   // patch309
  clCalcRendre(leg, classementOuvert && classementDonnees.length ? 'clans' : null);   // patch309""")
# replié : ni légende ni calcul
s = rep(s, """  if(classementMode === 'clans'){ renderClassementClans(podium, liste, plus); return; }   // patch210
  if(!classementOuvert){""",
"""  if(classementMode === 'clans'){ renderClassementClans(podium, liste, plus); return; }   // patch210
  if(!classementOuvert || classementMode === 'palmares') clCalcRendre(document.getElementById('clLegende'), null);   // patch309
  if(!classementOuvert){""")
# Front : la légende porte le lien
s = rep(s, """  legende.hidden = scoreDetail.size === 0;
""", """  clCalcRendre(legende, scoreDetail.size === 0 || classementMode === 'palmares' ? null : 'front');   // patch309
""")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch309' not in s
s = s.rstrip('\n') + """

/* patch309 : le calcul du classement */
.sc-legende .cl-calc-btn{ margin-left:auto; border:0; background:none; padding:2px 0; font:inherit; font-size:.74rem; font-weight:700; color:#FFB27A; text-decoration:underline; text-underline-offset:3px; cursor:pointer; }
.cl-calc{ background:rgba(10,22,40,.5); border:1px solid rgba(169,188,212,.16); border-radius:12px; padding:10px 12px; margin:-2px 0 12px; }
.cl-calc[hidden]{ display:none; }
.cl-calc-l{ display:grid; grid-template-columns:10px minmax(0,1fr); gap:9px; padding:7px 0; border-top:1px solid rgba(169,188,212,.1); }
.cl-calc-l:first-child{ border-top:0; padding-top:2px; }
.cl-calc-l .sc-pt{ margin:5px 0 0; }
.cl-calc-l b{ color:#fff; }
.cl-calc-l > div > b{ display:block; font-size:.84rem; margin-bottom:2px; }
.cl-calc-l span{ display:block; font-size:.76rem; color:#C9D3E3; line-height:1.45; }
.cl-calc-pied, .cl-calc-txt{ font-size:.74rem; color:#A9BCD4; margin:6px 0 0; line-height:1.45; }
.cl-calc-txt{ margin:0; color:#C9D3E3; }
.cl-calc-txt b{ color:#fff; }
"""
f.write_text(s, encoding='utf-8')

f = pathlib.Path('data/nouveautes.json'); d = json.loads(f.read_text(encoding='utf-8'))
e = next(x for x in d if x['date'] == '2026-11-02')
e['nouveautes'].insert(0, '🏆 Classement : « Comment c’est calculé ? » détaille le score (cartes, combats, territoires) et la moyenne des clans')
f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch309 appliqué')
