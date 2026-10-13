# -*- coding: utf-8 -*-
u"""
patch121 — le siège suit la commune, côté écran (demandé par Wally et Akan).

À pousser APRÈS siege-suit-la-commune.sql et siege-suit-2-cibles.sql.

1. « Vendre une commune » : sur une commune assiégée, le bouton « Vendre au
   jeu » est grisé (« Assiégée · vente au jeu dans 5 h ») au lieu de laisser
   choisir puis refuser. La règle est celle du serveur : un attaquant avec au
   moins une victoire, qui a attaqué dans les dernières 24 h.
   « Mettre en vente » reste possible : l'attaque suit la commune.
2. Étiquette « ⚔ assiégée 2/3 » partout où une commune peut changer de
   main : communes des autres dans « Proposer un échange », mes communes
   dans la même liste, propositions reçues et envoyées (ce que je reçois,
   ce que je donne), annonces de la bourse, et mes lignes de vente.
   Celui qui reçoit la commune sait ce qu'il prend.
Front seulement : en Terra il n'y a pas de siège.
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
assert 'tagSiege' not in js, u'patch121 deja applique'

# ---------------------------------------------------------------- outils
js = rempl(js, u"""let menaces = [];
""", u"""let menaces = [];
// patch121 : le siege suit la commune
// une de mes communes : bloquee pour la vente au jeu tant qu'un attaquant
// avec au moins une victoire a attaque dans les 24 h (meme regle que
// commune_assiegee cote serveur). Renvoie la fin du blocage, ou 0.
function finSiegeMienne(code){
  let fin = 0;
  for(const m of menaces){
    if(m.commune_code !== code || !(m.victoires_consecutives > 0) || !m.dernier_round) continue;
    fin = Math.max(fin, new Date(m.dernier_round).getTime() + 24 * 3600e3);
  }
  return fin > Date.now() ? fin : 0;
}
function serieMienne(code){
  let s = 0;
  for(const m of menaces) if(m.commune_code === code) s = Math.max(s, Number(m.victoires_consecutives) || 0);
  return s;
}
// communes des autres : commune_code -> serie en cours
let siegesConnus = new Map();
async function chargerSieges(codes){
  if(marcheTerra()) return;
  const liste = [...new Set(codes)].filter(Boolean).slice(0, 300);
  if(!liste.length) return;
  const { data, error } = await sb.rpc('sieges_communes', { p_codes: liste });
  if(error){ console.error('Sieges :', error.message); return; }
  liste.forEach(c => siegesConnus.delete(c));
  (data || []).forEach(s => siegesConnus.set(s.commune_code, Number(s.serie) || 0));
}
const tagSiege = (serie) => !marcheTerra() && serie > 0
  ? `<span class="tg-siege" title="Un joueur l'attaque : sa série continue contre le nouveau propriétaire">⚔ assiégée ${serie}/3</span>`
  : '';
""", u'outils')

# ---------------------------------------------------------------- 1. vendre au jeu grise
js = rempl(js, u"""      : `<div class="ligne-actions">${entry.conquiseLe && entry.conquiseLe + REVENTE_BLOQUEE_MS > Date.now()""",
u"""      : `<div class="ligne-actions">${finSiegeMienne(entry.code)
            ? `<button class="btn-p contour" disabled title="Un joueur l'attaque : la vente au jeu reprend 24 h après sa dernière attaque. Tu peux toujours la mettre en vente ou l'échanger, l'attaque suit la commune.">Assiégée · vente au jeu dans ${formatDuree(finSiegeMienne(entry.code) - Date.now())}</button>`
            : entry.conquiseLe && entry.conquiseLe + REVENTE_BLOQUEE_MS > Date.now()""", u'vendre au jeu')

js = rempl(js, u"""          <span class="ligne-nom">${entry.nom}</span>
          <span class="ligne-detail">${DEPT_NAMES[entry.dept] ? DEPT_NAMES[entry.dept] + ' ' : ''}(${entry.dept}), ${entry.tier.label.toLowerCase()}</span>""",
u"""          <span class="ligne-nom">${entry.nom}${tagSiege(serieMienne(entry.code))}</span>
          <span class="ligne-detail">${DEPT_NAMES[entry.dept] ? DEPT_NAMES[entry.dept] + ' ' : ''}(${entry.dept}), ${entry.tier.label.toLowerCase()}</span>""", u'ligne vente')

# ---------------------------------------------------------------- 2. bourse
js = rempl(js, u"""  renderMarketGrid(market || [], uid);""", u"""  await chargerSieges((market || []).map(a => a.commune_code));
  renderMarketGrid(market || [], uid);""", u'bourse chargement')
js = rempl(js, u"""          <span class="ligne-nom">${echapperTexte(c.nom)}${a.je_l_ai === false && !isMine ? TAG_NEUF : ''}</span>""",
u"""          <span class="ligne-nom">${echapperTexte(c.nom)}${a.je_l_ai === false && !isMine ? TAG_NEUF : ''}${tagSiege(isMine ? serieMienne(a.commune_code) : siegesConnus.get(a.commune_code))}</span>""", u'bourse ligne')

# ---------------------------------------------------------------- 3. proposer un echange
js = rempl(js, u"""  echangeCibles = data || [];
  renderEchangeCibles();""", u"""  echangeCibles = data || [];
  await chargerSieges(echangeCibles.map(c => c.commune_code));
  renderEchangeCibles();""", u'cibles chargement')
js = rempl(js, u"""      <b>${echapperTexte(c.nom)}${c.nouvelle === true ? TAG_NEUF : ''}</b>
      <small>${echapperTexte(c.departement)} · ${echapperTexte(c.pseudo || 'un joueur')}</small>""",
u"""      <b>${echapperTexte(c.nom)}${c.nouvelle === true ? TAG_NEUF : ''}</b>
      <small>${echapperTexte(c.departement)} · ${echapperTexte(c.pseudo || 'un joueur')}</small>${tagSiege(siegesConnus.get(c.commune_code))}""", u'cibles ligne')
js = rempl(js, u"""      <b>${echapperTexte(c.nom)}</b>
      <small>${echapperTexte(DEPT_NAMES[c.dept] || '')} (${echapperTexte(c.dept)})</small>""",
u"""      <b>${echapperTexte(c.nom)}</b>
      <small>${echapperTexte(DEPT_NAMES[c.dept] || '')} (${echapperTexte(c.dept)})</small>${tagSiege(serieMienne(c.code))}""", u'mien ligne')

# ---------------------------------------------------------------- 4. propositions
js = rempl(js, u"""  echangesEnCours = data || [];""", u"""  echangesEnCours = data || [];
  await chargerSieges(echangesEnCours.map(e => e.je_recois_code));""", u'propositions chargement', 2)
js = rempl(js, u"""          <small>(${echapperTexte(e.je_recois_dept)})</small>${e.nouvelle === true ? TAG_NEUF : ''}""",
u"""          <small>(${echapperTexte(e.je_recois_dept)})</small>${e.nouvelle === true ? TAG_NEUF : ''}${tagSiege(siegesConnus.get(e.je_recois_code))}""", u'prop recois')
js = rempl(js, u"""          <small>(${echapperTexte(e.je_donne_dept)})</small>
        </div>""", u"""          <small>(${echapperTexte(e.je_donne_dept)})</small>${tagSiege(serieMienne(e.je_donne_code))}
        </div>""", u'prop donne')

css += u"""
/* ---------- patch121 : le siege suit la commune ---------- */
.tg-siege{ display:inline-block; margin-left:7px; padding:2px 7px; border-radius:999px; background:rgba(229,72,77,.16);
  color:#FF8A8E; border:1px solid rgba(229,72,77,.45); font-size:.56rem; font-weight:800; letter-spacing:.04em; vertical-align:2px; white-space:nowrap; }
.tg-siege, .ech-face .tg-siege, .ligne-nom .tg-siege{ font-family: var(--texte); color:#FF8A8E; }
.ech-item > .tg-siege, .ech-face > .tg-siege{ align-self:flex-start; margin:4px 0 0; }
"""

ecrire('app.js', js)
ecrire('style.css', css)
print(u'patch121 applique')
