# -*- coding: utf-8 -*-
u"""
patch97 — Communauté : classement par saison. SQL : _sql/s2-10-classements.sql
(à passer avant le push ; sans lui, les deux nouveaux boutons restent cachés).

- « Général » devient « Saison en cours » (saison 1) / « Front » (saison 2).
- « Terra » (saison 2 seulement) : la collection Terra, communes différentes.
- « Palmarès » : apparaît dès qu'une saison terminée a un palmarès archivé ;
  une puce par saison, le classement figé de la saison choisie.
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
assert 'palmaresSaisons' not in js, u'patch97 deja applique'

js = rempl(js, u"""async function loadClassement(){
  const bloc = document.getElementById('classement');
  const { data, error } = await sb.rpc('classement', { p_mode: classementMode, p_limite: classementComplet ? 50 : 10 });
  if(error){""", u"""// patch97 : classement par saison (Terra, Palmares)
let palmaresSaisons = [], palmaresChoisie = null, palmaresCharge = false;
async function initModesClassement(){
  const general = document.querySelector('#classement [data-mode="general"]');
  if(general) general.textContent = SAISON2 ? 'Front' : 'Saison en cours';
  const terra = document.querySelector('#classement [data-mode="terra"]');
  if(terra) terra.hidden = !SAISON2;
  if(palmaresCharge) return;
  palmaresCharge = true;
  const { data, error } = await sb.rpc('palmares_saisons');
  palmaresSaisons = error ? [] : (data || []);
  if(!palmaresChoisie && palmaresSaisons.length) palmaresChoisie = palmaresSaisons[0].saison;
  const b = document.querySelector('#classement [data-mode="palmares"]');
  if(b) b.hidden = !palmaresSaisons.length;
}

function renderSaisonsPalmares(){
  const el = document.getElementById('clSaisons');
  if(!el) return;
  el.hidden = classementMode !== 'palmares' || !classementOuvert;
  if(el.hidden) return;
  const s = palmaresSaisons.find(x => x.saison === palmaresChoisie);
  const fin = s && s.fin ? new Date(s.fin).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' }) : '';
  el.innerHTML = `<div class="cl-saisons-puces">${palmaresSaisons.map(x =>
      `<button class="filter-pill ${x.saison === palmaresChoisie ? 'active' : ''}" data-saison="${echapperTexte(x.saison)}">${echapperTexte(x.nom)}</button>`).join('')}</div>
    ${s ? `<p class="cl-saisons-info">🏆 Classement final${fin ? ` · terminée le ${fin}` : ''} · ${Number(s.joueurs).toLocaleString('fr-FR')} joueurs</p>` : ''}`;
}

async function loadClassement(){
  const bloc = document.getElementById('classement');
  await initModesClassement();
  const limite = classementComplet ? 50 : 10;
  let appel;
  if(classementMode === 'terra') appel = sb.rpc('terra_classement', { p_limite: limite });
  else if(classementMode === 'palmares') appel = sb.rpc('palmares', { p_saison: palmaresChoisie, p_limite: limite });
  else appel = sb.rpc('classement', { p_mode: classementMode, p_limite: limite });
  const { data, error } = await appel;
  if(error && classementMode !== 'general' && classementMode !== 'mois'){
    console.error('Classement :', error.message);
    classementDonnees = [];
    renderClassement();
    return;
  }
  if(error){""", 'load')

js = rempl(js, u"""function renderClassement(){
  const podium = document.getElementById('clPodium');""", u"""function renderClassement(){
  renderSaisonsPalmares();
  const podium = document.getElementById('clPodium');""", 'render')

js = rempl(js, u"""    liste.innerHTML = `<p class="collection-empty">${classementMode === 'mois' ? 'Aucune commune prise ce mois-ci pour le moment.' : 'Le classement apparaîtra dès que des communes seront possédées.'}</p>`;""",
           u"""    liste.innerHTML = `<p class="collection-empty">${classementMode === 'mois' ? 'Aucune commune prise ce mois-ci pour le moment.'
      : classementMode === 'terra' ? 'Le classement Terra apparaîtra dès les premiers paquets ouverts.'
      : classementMode === 'palmares' ? 'Pas de palmarès pour cette saison.'
      : 'Le classement apparaîtra dès que des communes seront possédées.'}</p>`;""", 'vide')

js = rempl(js, u"""  const mode = e.target.closest('[data-mode]');
  if(mode){""", u"""  const saison = e.target.closest('[data-saison]');
  if(saison){
    palmaresChoisie = saison.dataset.saison;
    classementComplet = false;
    loadClassement();
    return;
  }
  const mode = e.target.closest('[data-mode]');
  if(mode){""", 'clic saison')
ecrire('app.js', js)

html = lire('index.html')
html = rempl(html, u"""            <button class="filter-pill" data-mode="mois">Ce mois-ci</button>
          </div>
        </div>""", u"""            <button class="filter-pill" data-mode="mois">Ce mois-ci</button>
            <button class="filter-pill" data-mode="terra" hidden>Terra</button>
            <button class="filter-pill" data-mode="palmares" hidden>Palmarès</button>
          </div>
        </div>
        <div class="cl-saisons" id="clSaisons" hidden></div>""", 'html')
ecrire('index.html', html)

css = lire('style.css')
assert '.cl-saisons' not in css
css = rempl(css, u"  .cl-modes{ display:flex; gap:8px; }\n", u"""  .cl-modes{ display:flex; gap:8px; flex-wrap:wrap; }
  .cl-modes [hidden]{ display:none; }
  .cl-saisons{ margin:4px 0 10px; }
  .cl-saisons[hidden]{ display:none; }
  .cl-saisons-puces{ display:flex; gap:6px; flex-wrap:wrap; }
  .cl-saisons-puces .filter-pill{ font-size:.78rem; padding:5px 11px; }
  .cl-saisons-info{ margin:8px 0 0; font-size:.8rem; color: var(--brume); }
""", 'css')
ecrire('style.css', css)
print(u'patch97 applique')
