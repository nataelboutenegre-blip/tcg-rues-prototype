# -*- coding: utf-8 -*-
u"""
patch143 — QG : compteur des victoires payées (« 3 / 5 victoires payées »,
« 5 / 5 · reviens demain ») sur Radar et Rafale, et points gagnés à la
Commune du jour. Lit gains_du_jour() (_sql/gains-du-jour.sql) ; sans la
fonction, rien ne s'affiche de plus.
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
assert 'gainsJour' not in js, u'patch143 deja applique'

# --- chargement
js = rempl(js, u"""async function chargerRadar(){
  const { data, error } = await sb.rpc('radar_etat');""", u"""// patch143 : victoires payees aujourd'hui (Radar, Rafale) et gain de la Commune du jour
let gainsJour = null;
async function chargerGainsJour(){
  try{ const { data, error } = await sb.rpc('gains_du_jour'); gainsJour = error ? null : data; }
  catch(e){ gainsJour = null; }
}
const etiquetteGains = (n, max) => n >= max ? `${max} / ${max} · reviens demain` : `${n} / ${max} victoire${max > 1 ? 's' : ''} payée${max > 1 ? 's' : ''}`;

async function chargerRadar(){
  chargerGainsJour().then(() => { const qg = document.getElementById('panel-qg'); if(qg && qg.classList.contains('active')) renderQG(); });
  const { data, error } = await sb.rpc('radar_etat');""", u'chargement radar')
js = rempl(js, u"""async function chargerRafale(){
  const { data, error } = await sb.rpc('rafale_etat');""", u"""async function chargerRafale(){
  await chargerGainsJour();
  const { data, error } = await sb.rpc('rafale_etat');""", u'chargement rafale')

# --- Radar
js = rempl(js, u"""  document.getElementById('qgRestants').textContent = r.en_cours ? 'partie en cours'
    : sansLimite ? ''
    : (r.restants > 0 ? `${r.restants} duel${r.restants > 1 ? 's' : ''} aujourd’hui` : 'reviens demain');""",
u"""  document.getElementById('qgRestants').textContent = r.en_cours ? 'partie en cours'
    : sansLimite ? (gainsJour ? etiquetteGains(Number(gainsJour.radar) || 0, Number(gainsJour.max_radar) || 5) : '')
    : (r.restants > 0 ? `${r.restants} duel${r.restants > 1 ? 's' : ''} aujourd’hui` : 'reviens demain');""", u'radar etiquette')
js = rempl(js, u"""  document.getElementById('qgAttente').textContent = r.en_attente > 0
    ? `${r.en_attente} partie${r.en_attente > 1 ? 's' : ''} en attente d’un adversaire` : '';""",
u"""  document.getElementById('qgAttente').textContent = r.en_attente > 0
    ? `${r.en_attente} partie${r.en_attente > 1 ? 's' : ''} en attente d’un adversaire`
    : (gainsJour && Number(gainsJour.radar) >= Number(gainsJour.max_radar || 5) ? 'Les duels restent ouverts, sans points jusqu’à demain' : '');""", u'radar attente')

# --- Rafale
js = rempl(js, u"""  document.getElementById('rfEtiquette').textContent = r.en_cours ? 'partie en cours' : '';""",
u"""  document.getElementById('rfEtiquette').textContent = r.en_cours ? 'partie en cours'
    : (gainsJour ? etiquetteGains(Number(gainsJour.rafale) || 0, Number(gainsJour.max_rafale) || 5) : '');
""", u'rafale etiquette')
js = rempl(js, u"""  document.getElementById('rfAttente').textContent = r.en_attente > 0
    ? `${r.en_attente} partie${r.en_attente > 1 ? 's' : ''} en attente d’un adversaire` : '';""",
u"""  document.getElementById('rfAttente').textContent = r.en_attente > 0
    ? `${r.en_attente} partie${r.en_attente > 1 ? 's' : ''} en attente d’un adversaire`
    : (gainsJour && Number(gainsJour.rafale) >= Number(gainsJour.max_rafale || 5) ? 'Les duels restent ouverts, sans points jusqu’à demain' : '');""", u'rafale attente')

# --- Commune du jour
js = rempl(js, u"""    info.textContent = (e.serie > 0 ? `Série de ${e.serie} jour${e.serie > 1 ? 's' : ''} · ` : '') + 'nouvelle commune à minuit';""",
u"""    const gainCdj = gainsJour && gainsJour.cdj ? Number(gainsJour.cdj) : 0;
    info.textContent = (e.serie > 0 ? `Série de ${e.serie} jour${e.serie > 1 ? 's' : ''} · ` : '')
      + (gainCdj > 0 ? `+${gainCdj} pts gagnés · ` : '') + 'nouvelle commune à minuit';""", u'cdj')

ecrire('app.js', js)
print(u'patch143 applique')
