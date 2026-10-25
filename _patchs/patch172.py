# -*- coding: utf-8 -*-
u"""
patch172 — Plus ou moins dans les listes du QG : « Tes derniers duels »
(filtre Plus ou moins, et dans Tous) et « Classement » (bouton Plus ou
moins). SQL : _sql/pom-3-historique.sql (les parties en attente).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)
h = lire('index.html')
assert 'data-hist="pom"' not in h, u'patch172 deja applique'
h = rempl(h, u'''<button type="button" data-hist="rafale">Rafale</button></div></div>''',
          u'''<button type="button" data-hist="rafale">Rafale</button><button type="button" data-hist="pom">Plus ou moins</button></div></div>''', 'hist')
h = rempl(h, u'''<button type="button" data-cl="rafale">Rafale</button></div></div>''',
          u'''<button type="button" data-cl="rafale">Rafale</button><button type="button" data-cl="pom">Plus ou moins</button></div></div>''', 'cl')
ecrire('index.html', h)

js = lire('app.js')
js = rempl(js, u"""  const tag = tous ? `<span class="qg-jeu ${jeu}">${jeu === 'radar' ? 'Radar' : 'Rafale'}</span>` : '';""",
u"""  const tag = tous ? `<span class="qg-jeu ${jeu}">${jeu === 'radar' ? 'Radar' : jeu === 'pom' ? 'Plus ou moins' : 'Rafale'}</span>` : '';
  const pom = (n) => `${Number(n || 0)} / 10`;   // patch172""", 'tag')
js = rempl(js, u"""      <span class="qg-adv">${tag}pas encore d’adversaire<small>${jeu === 'radar' ? kmQG(x.total_km) + ' km' : score(x.score)}${lettre}</small></span>""",
u"""      <span class="qg-adv">${tag}pas encore d’adversaire<small>${jeu === 'radar' ? kmQG(x.total_km) + ' km' : jeu === 'pom' ? pom(x.justes) : score(x.score)}${lettre}</small></span>""", 'attente')
js = rempl(js, u"""  const detail = jeu === 'radar'
    ? `${kmQG(x.total_km)} km contre ${kmQG(x.adversaire_km)} km`""", u"""  const detail = jeu === 'radar'
    ? `${kmQG(x.total_km)} km contre ${kmQG(x.adversaire_km)} km`
    : jeu === 'pom' ? `${pom(x.justes)} contre ${pom(x.adversaire_justes)}`""", 'detail')
js = rempl(js, u"""  const rd = radarEtat || {}, rf = rafaleEtat || {};
  // l'historique""", u"""  const rd = radarEtat || {}, rf = rafaleEtat || {};
  let pm = {};   // patch172 (pomDuelEtat est declare plus bas)
  try{ pm = pomDuelEtat || {}; }catch(err){}
  // l'historique""", 'pm')
js = rempl(js, u"""  let lignes = [...prendre('radar', rd), ...prendre('rafale', rf)];""",
               u"""  let lignes = [...prendre('radar', rd), ...prendre('rafale', rf), ...prendre('pom', pm)];""", 'lignes')
js = rempl(js, u"""    : `<li class="qg-vide">Aucun duel ${qgFiltreHist === 'radar' ? 'Radar ' : qgFiltreHist === 'rafale' ? 'Rafale ' : ''}pour l’instant.</li>`;""",
               u"""    : `<li class="qg-vide">Aucun duel ${qgFiltreHist === 'radar' ? 'Radar ' : qgFiltreHist === 'rafale' ? 'Rafale ' : qgFiltreHist === 'pom' ? 'Plus ou moins ' : ''}pour l’instant.</li>`;""", 'vide')
js = rempl(js, u"""  const c = (qgFiltreCl === 'rafale' ? rf.classement : rd.classement) || [];
  const prefixe = qgFiltreCl === 'rafale' ? 'rang-rf-' : 'rang-';""",
u"""  const c = (qgFiltreCl === 'rafale' ? rf.classement : qgFiltreCl === 'pom' ? pm.classement : rd.classement) || [];
  const prefixe = qgFiltreCl === 'rafale' ? 'rang-rf-' : qgFiltreCl === 'pom' ? 'rang-pom-' : 'rang-';""", 'cl')
js = rempl(js, u"""    : `<li class="qg-vide">Aucun duel ${qgFiltreCl === 'rafale' ? 'Rafale' : 'Radar'} joué pour l’instant.</li>`;""",
               u"""    : `<li class="qg-vide">Aucun duel ${qgFiltreCl === 'rafale' ? 'Rafale' : qgFiltreCl === 'pom' ? 'Plus ou moins' : 'Radar'} joué pour l’instant.</li>`;""", 'clvide')
js = rempl(js, u"""function ouvrirResumeDuel(li){
  const id = Number(li.dataset.id);""", u"""function ouvrirResumeDuel(li){
  if(li.dataset.jeu === 'pom') return;   // patch172 : pas encore de resume
  const id = Number(li.dataset.id);""", 'resume')
js = rempl(js, u"""  const d = document.getElementById('qgPomDuel');
  d.textContent = e.en_cours ? 'Reprendre le duel' : 'Duel classé';""", u"""  const d = document.getElementById('qgPomDuel');
  d.textContent = e.en_cours ? 'Reprendre le duel' : 'Duel classé';
  try{ renderQGListes(); }catch(err){}   // patch172""", 'refresh')
js = rempl(js, u"""return ['tous', 'radar', 'rafale'].includes(v) ? v : 'tous';""", u"""return ['tous', 'radar', 'rafale', 'pom'].includes(v) ? v : 'tous';""", 'filtre-h')
js = rempl(js, u"""return localStorage.getItem('tf-qg-cl') === 'rafale' ? 'rafale' : 'radar';""", u"""const v = localStorage.getItem('tf-qg-cl'); return v === 'rafale' || v === 'pom' ? v : 'radar';""", 'filtre-c')
ecrire('app.js', js)
css = lire('style.css')
css = rempl(css, u".qg-jeu.rafale{ color:#FFD27A; background: rgba(240,180,41,.14); }",
u""".qg-jeu.rafale{ color:#FFD27A; background: rgba(240,180,41,.14); }
.qg-jeu.pom{ color:#9CF7C9; background: rgba(61,214,140,.14); }   /* patch172 */
.rang-pom-arpenteur{ color: var(--brume); } .rang-pom-cartographe{ color:#9DC3FF; } .rang-pom-geometre{ color: var(--c-peucommun); }
.rang-pom-recenseur{ color: var(--c-epique, #B07CFF); } .rang-pom-prefet{ color: var(--c-legendaire); }""", 'css')
ecrire('style.css', css)
print(u'patch172 applique. Lancer : python3 maj-version.py')
