# -*- coding: utf-8 -*-
u"""
patch68 — Echange : les propositions en cours passent sous le formulaire.

POURQUOI
  Demande de Natael (5 octobre) : « faire passer tous les echanges en cours
  en dessous des echanges a proposer ». Le formulaire est ce qu'on vient
  faire dans l'onglet ; la liste des propositions poussait tout vers le bas
  des qu'il y en avait plusieurs.

CE QUI CHANGE
  Seul l'ordre des deux blocs dans la page. La pastille de l'onglet, les
  notifications et les boutons Accepter / Refuser / Annuler ne changent pas.
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

def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)

BLOC = u"""      <div class="bourse-section" id="echPropositions" hidden>
        <h2>Propositions en cours</h2>
        <div class="ech-liste" id="echListe"></div>
      </div>
"""

html = lire('index.html')
html = rempl(html, BLOC + u"\n", u"", 'retrait du bloc')
html = rempl(html,
u"""        <button class="open-btn" id="echEnvoyer" disabled>Choisis deux communes</button>
      </div>
""",
u"""        <button class="open-btn" id="echEnvoyer" disabled>Choisis deux communes</button>
      </div>

""" + BLOC, 'bloc sous le formulaire')
ecrire('index.html', html)

print(u'patch68 : bloc deplace')


# ---------------- le raccourci en haut ----------------
# Avec 300 communes dans « Tu donnes », la liste descend tres bas : un
# joueur qui arrive apres une notification ne verrait pas ses propositions.
html = lire('index.html')
html = rempl(html,
u"""      <div class="puces"><span class="puce solde">Solde <b id="soldeValueEchange">—</b></span></div>
""",
u"""      <div class="puces"><span class="puce solde">Solde <b id="soldeValueEchange">—</b></span>
        <button type="button" class="ech-raccourci" id="echRaccourci" hidden></button></div>
""", 'raccourci')
ecrire('index.html', html)

js = lire('app.js')
js = rempl(js,
u"""  bloc.hidden = echangesEnCours.length === 0;
  liste.innerHTML = echangesEnCours.map(ligneEchange).join('');""",
u"""  bloc.hidden = echangesEnCours.length === 0;
  liste.innerHTML = echangesEnCours.map(ligneEchange).join('');
  // le raccourci du haut : combien, et combien attendent une reponse
  const raccourci = document.getElementById('echRaccourci');
  if(raccourci){
    const n = echangesEnCours.length;
    const recues = echangesEnCours.filter(e => e.sens === 'recu').length;
    raccourci.hidden = n === 0;
    raccourci.classList.toggle('urgent', recues > 0);
    const s = (k) => k > 1 ? 's' : '';
    raccourci.textContent = recues > 0
      ? `${recues} proposition${s(recues)} en attente ↓`
      : `${n} proposition${s(n)} envoyée${s(n)} ↓`;
  }""", 'rendu raccourci')
js = rempl(js,
u"""document.getElementById('echListe').addEventListener('click', async (e) => {""",
u"""document.getElementById('echRaccourci').addEventListener('click', () => {
  const bloc = document.getElementById('echPropositions');
  if(bloc) bloc.scrollIntoView({ behavior: 'smooth', block: 'start' });
});

document.getElementById('echListe').addEventListener('click', async (e) => {""", 'clic raccourci')
ecrire('app.js', js)

css = lire('style.css')
css += u"""

/* ---------- Echange : raccourci vers les propositions (patch68) ---------- */
.ech-raccourci{ font: inherit; font-size:.9rem; font-weight:600; padding:6px 12px; border-radius:20px; cursor:pointer;
  background:transparent; color: var(--brume); border:1px solid rgba(169,188,212,.3); }
.ech-raccourci.urgent{ color: var(--nuit); background: var(--c-legendaire); border-color: var(--c-legendaire); }
.ech-raccourci:focus-visible{ outline:2px solid #fff; outline-offset:2px; }
#echPropositions{ scroll-margin-top: 16px; }
"""
ecrire('style.css', css)
print(u'patch68 applique : index.html, app.js, style.css')
