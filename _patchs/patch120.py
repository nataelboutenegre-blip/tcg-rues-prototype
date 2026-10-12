# -*- coding: utf-8 -*-
u"""
patch120 — classement : lignes réparées + détail du score de la saison 2.

1. CORRECTIF (en ligne depuis patch110, 10 octobre) : les règles CSS du
   classement des clans (.cl-ligne en grille, « pts » à la ligne)
   s'appliquaient à TOUTE la page et déformaient le classement de la
   Communauté à partir de la 4e place. Elles sont limitées aux clans
   (.clan-carte .cl-ligne).
2. Saison 2 (caché tant que SAISON2 = false) : sous chaque joueur, une barre
   en trois couleurs — cartes (bleu), combats (rouge), territoires (vert) —
   avec une légende sous le titre. Au survol, la barre donne les chiffres.
   Seulement dans le classement « Saison en cours » (pas « Ce mois-ci »).
   Les chiffres viennent de score_detail() (s2-21-score.sql) ; si l'appel
   échoue, le classement s'affiche comme avant, sans barre.
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
assert 'scoreDetail' not in js, u'patch120 deja applique'

# ---------------------------------------------------------------- CSS
css = rempl(css, u""".cl-ligne{ display:grid; grid-template-columns:22px 30px minmax(0,1fr) auto; gap:10px; align-items:center; padding:8px 4px; border-top:1px solid rgba(169,188,212,0.1); }
.cl-ligne.moi{ background: rgba(240,180,41,0.08); border-radius:8px; }
.cl-ligne .cl-score{ font-family: var(--titre); font-size:1.1rem; text-align:right; }
.cl-ligne .cl-score small{ display:block; font-family: var(--texte); font-size:.68rem; color: var(--brume); }""",
u"""/* patch120 : limite aux clans (ces regles deformaient le classement de la Communaute) */
.clan-carte .cl-ligne{ display:grid; grid-template-columns:22px 30px minmax(0,1fr) auto; gap:10px; align-items:center; padding:8px 4px; border-top:1px solid rgba(169,188,212,0.1); }
.clan-carte .cl-ligne.moi{ background: rgba(240,180,41,0.08); border-radius:8px; }
.clan-carte .cl-ligne .cl-score{ font-family: var(--titre); font-size:1.1rem; text-align:right; }
.clan-carte .cl-ligne .cl-score small{ display:block; font-family: var(--texte); font-size:.68rem; color: var(--brume); }""", u'css clans')

css += u"""
/* ---------- patch120 : detail du score (saison 2) ---------- */
.sc-legende{ display:flex; align-items:center; gap:6px; flex-wrap:wrap; font-size:.74rem; color: var(--brume); margin:-4px 0 10px; }
.sc-legende[hidden]{ display:none; }
.sc-pt{ display:inline-block; width:8px; height:8px; border-radius:2px; margin:0 1px 0 4px; }
.sc-pt:first-child{ margin-left:0; }
.sc-pt.c{ background: var(--c-rare); } .sc-pt.co{ background: var(--c-rouge); } .sc-pt.t{ background: var(--c-peucommun); }
.sc-nom{ flex:1; min-width:0; display:flex; flex-direction:column; gap:4px; }
.sc-nom .cl-pseudo{ flex:none; }
.sc-barre{ display:flex; gap:2px; height:5px; width:100%; max-width:160px; border-radius:3px; overflow:hidden; }
.cl-marche .sc-barre{ max-width:96px; margin-top:4px; }
.sc-barre i{ display:block; min-width:3px; }
.sc-barre .c{ background: var(--c-rare); } .sc-barre .co{ background: var(--c-rouge); } .sc-barre .t{ background: var(--c-peucommun); }
"""

# ---------------------------------------------------------------- JS
js = rempl(js, u"let classementDonnees = [];", u"""let classementDonnees = [];
// patch120 : detail du score de la saison 2 (joueur_id -> {cartes, combats, territoires})
let scoreDetail = new Map();
async function chargerScoreDetail(){
  scoreDetail = new Map();
  if(!SAISON2 || classementMode !== 'general' || !classementDonnees.length) return;
  const { data, error } = await sb.rpc('score_detail', { p_joueurs: classementDonnees.map(l => l.joueur_id) });
  if(error){ console.error('Detail du score :', error.message); return; }
  (data || []).forEach(d => scoreDetail.set(d.joueur_id, d));
  if(scoreDetail.size) renderClassement();
}
function scoreBarre(id){
  const d = scoreDetail.get(id);
  if(!d) return '';
  const nb = (n) => Number(n || 0).toLocaleString('fr-FR');
  const part = (v, cl) => Number(v) > 0 ? `<i class="${cl}" style="flex:${Number(v)}"></i>` : '';
  return `<span class="sc-barre" title="cartes ${nb(d.cartes)} · combats ${nb(d.combats)} · territoires ${nb(d.territoires)}">`
    + part(d.cartes, 'c') + part(d.combats, 'co') + part(d.territoires, 't') + '</span>';
}""", u'etat')

js = rempl(js, u"""  classementDonnees = data || [];
  renderClassement();
}""", u"""  classementDonnees = data || [];
  scoreDetail = new Map();
  renderClassement();
  chargerScoreDetail();
}""", u'chargement')

js = rempl(js, u"""  const couleur = (l) => l.est_moi ? COULEUR_MOI : colorForPlayer(l.joueur_id);
  const nb = (n) => Number(n).toLocaleString('fr-FR');
""", u"""  const couleur = (l) => l.est_moi ? COULEUR_MOI : colorForPlayer(l.joueur_id);
  const nb = (n) => Number(n).toLocaleString('fr-FR');
  // patch120 : legende du detail du score (saison 2)
  let legende = document.getElementById('clLegende');
  if(!legende){
    legende = document.createElement('p');
    legende.id = 'clLegende';
    legende.className = 'sc-legende';
    legende.innerHTML = '<i class="sc-pt c"></i>cartes <i class="sc-pt co"></i>combats <i class="sc-pt t"></i>territoires';
    podium.before(legende);
  }
  legende.hidden = scoreDetail.size === 0;
""", u'legende')

js = rempl(js, u"""      <span class="cl-score">${nb(l.score)}<small>pts</small></span>
      <span class="cl-detail">${nb(l.communes)} commune${l.communes > 1 ? 's' : ''}</span>
    </button>`).join('');""", u"""      <span class="cl-score">${nb(l.score)}<small>pts</small></span>
      <span class="cl-detail">${nb(l.communes)} commune${l.communes > 1 ? 's' : ''}</span>
      ${scoreBarre(l.joueur_id)}
    </button>`).join('');""", u'podium')

js = rempl(js, u"""      <span class="cl-pseudo">${l.est_moi ? '<b>Toi</b>' : echapperTexte(l.pseudo)}</span>
      <span class="cl-mini">""", u"""      ${scoreDetail.size
        ? `<span class="sc-nom"><span class="cl-pseudo">${l.est_moi ? '<b>Toi</b>' : echapperTexte(l.pseudo)}</span>${scoreBarre(l.joueur_id)}</span>`
        : `<span class="cl-pseudo">${l.est_moi ? '<b>Toi</b>' : echapperTexte(l.pseudo)}</span>`}
      <span class="cl-mini">""", u'liste')

ecrire('app.js', js)
ecrire('style.css', css)
print(u'patch120 applique')
