# -*- coding: utf-8 -*-
u"""
patch101 — les quêtes de la saison 2 (CACHÉ tant que SAISON2 = false).
SQL : _sql/s2-12-quetes.sql.

- Le bloc Objectifs du Tirage montre, en saison 2, les quêtes du mode
  affiché : Terra (points) ou Front (énergie, plafond 20 / jour affiché).
- Récompenses : « 30 pts », « +5 ⚡ », ou les deux (« 50 pts · +3 ⚡ »).
- Récupérer : reclamer_quete ; énergie et solde rechargés.
Rien ne change en saison 1 (missions habituelles).
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
assert 'quetesTout' not in js, u'patch101 deja applique'

js = rempl(js, u"""async function loadObjectifs(){
  const { data, error } = await sb.rpc('objectifs');""", u"""// patch101 : en saison 2, les quetes du mode affiche
let quetesTout = [];
async function loadQuetes(){
  const { data, error } = await sb.rpc('quetes');
  const bloc = document.getElementById('objectifs');
  if(error){ if(bloc) bloc.hidden = true; return; }
  quetesTout = data || [];
  renderObjectifs();
}

async function loadObjectifs(){
  if(SAISON2) return loadQuetes();
  const { data, error } = await sb.rpc('objectifs');""", 'load')

js = rempl(js, u"""  const recompense = o.recompense === 'points'
    ? `${Number(o.valeur).toLocaleString('fr-FR')} pts`
    : (o.valeur > 1 ? `${o.valeur} paquets` : '1 paquet');""", u"""  const recompense = o.points !== undefined
    ? [o.points ? `${Number(o.points).toLocaleString('fr-FR')} pts` : '', o.energie ? `+${o.energie} ⚡` : ''].filter(Boolean).join(' · ')
    : o.recompense === 'points'
    ? `${Number(o.valeur).toLocaleString('fr-FR')} pts`
    : (o.valeur > 1 ? `${o.valeur} paquets` : '1 paquet');""", 'recompense')
js = rempl(js, u"""        <span class="obj-gain gain-${o.recompense}">${recompense}</span>""",
           u"""        <span class="obj-gain gain-${o.points !== undefined ? (o.energie && !o.points ? 'energie' : 'points') : o.recompense}">${recompense}</span>""", 'classe gain')

js = rempl(js, u"""function renderObjectifs(){
  const bloc = document.getElementById('objectifs');
  if(!bloc) return;""", u"""function renderObjectifs(){
  const bloc = document.getElementById('objectifs');
  if(!bloc) return;
  if(SAISON2) objectifsListe = quetesTout.filter(q => q.mode === modeJeu);""", 'render mode')

js = rempl(js, u"""  document.getElementById('objJour').innerHTML =
    `<h3>Aujourd'hui</h3>` + jour.map(carteObjectif).join('');
  document.getElementById('objUnique').innerHTML =
    `<h3>${objectifsTout ? 'Tous les défis' : 'Tes prochains défis'}</h3>` + visibles.map(carteObjectif).join('');""",
           u"""  const ej = SAISON2 && modeJeu === 'front' && objectifsListe.length ? Number(objectifsListe[0].energie_jour) || 0 : null;
  document.getElementById('objJour').innerHTML =
    `<h3>Aujourd'hui${ej !== null ? `<span class="obj-plafond">⚡ ${ej} / 20 d'énergie de quêtes</span>` : ''}</h3>` + jour.map(carteObjectif).join('');
  const blocUnique = document.getElementById('objUnique');
  blocUnique.hidden = uniques.length === 0;
  blocUnique.innerHTML = uniques.length
    ? `<h3>${objectifsTout ? 'Tous les défis' : 'Tes prochains défis'}</h3>` + visibles.map(carteObjectif).join('') : '';""", 'render groupes')

js = rempl(js, u"""    const { data, error } = await sb.rpc('reclamer_objectif', { p_id: btn.dataset.objectif });
    if(error) throw error;
    const r = data && data[0];
    notifier({ type: 'succes', titre: 'Objectif atteint', texte: r ? r.message : 'Récompense récupérée' });""",
           u"""    const { data, error } = await sb.rpc(SAISON2 ? 'reclamer_quete' : 'reclamer_objectif', { p_id: btn.dataset.objectif });
    if(error) throw error;
    const r = data && data[0];
    notifier({ type: 'succes', titre: SAISON2 ? 'Quête accomplie' : 'Objectif atteint', texte: r ? r.message : 'Récompense récupérée' });
    if(SAISON2) majEnergie();""", 'reclamer')

# changer de mode : les quetes suivent
js = rempl(js, u"""  // patch90 : le statut des paquets et la collection suivent le mode
  loadPackStatus();""", u"""  // patch90 : le statut des paquets et la collection suivent le mode
  loadPackStatus();
  if(quetesTout.length) renderObjectifs(); else loadObjectifs();""", 'mode')
ecrire('app.js', js)

html = lire('index.html')
html = rempl(html, u"""          <h2>Objectifs</h2>""", u"""          <h2 id="objTitre">Objectifs</h2>""", 'titre')
ecrire('index.html', html)

css = lire('style.css')
assert '.obj-plafond' not in css
css += u"""
/* patch101 : quetes de la saison 2 */
.obj-gain.gain-energie{ color:#5FD39D; }
.obj-plafond{ margin-left:8px; font-family: var(--corps, inherit); font-size:.72rem; font-weight:600; color:#5FD39D; text-transform:none; letter-spacing:0; }
.obj-groupe[hidden]{ display:none; }
"""
ecrire('style.css', css)
print(u'patch101 applique')
