# -*- coding: utf-8 -*-
u"""
patch210 — le classement : Front · Clans · Palmarès.
« Ce mois-ci » et « Terra » disparaissent (Terra est faussé : les joueurs ont
gardé leurs cartes de la saison 1). Nouvel onglet « Clans » : podium et liste
des clans (même calcul que l'écran Clan : moyenne de communes du Front par
membre actif), mon clan surligné ; toucher un clan ouvre l'écran Clan sur ses
membres. Aucun SQL (clans_classement et mon_clan existent).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rep(s, a, b, n=1):
    c = s.count(a)
    assert c == n, (a[:90], c, n)
    return s.replace(a, b)

h = lire('index.html')
assert 'data-mode="clans"' not in h
h = rep(h, u"""            <button class="filter-pill" data-mode="mois">Ce mois-ci</button>
            <button class="filter-pill" data-mode="terra" hidden>Terra</button>
""", u"""            <button class="filter-pill" data-mode="clans" hidden>Clans</button>
""")
ecrire('index.html', h)

js = lire('app.js')
assert 'patch210' not in js
js = rep(js, u"""  const terra = document.querySelector('#classement [data-mode="terra"]');
  if(terra) terra.hidden = !SAISON2;
""", u"""  const clans = document.querySelector('#classement [data-mode="clans"]');   // patch210
  if(clans) clans.hidden = !CLANS;
""")
js = rep(js, u"""  const limite = classementComplet ? 50 : 10;
  let appel;
  if(classementMode === 'terra')""", u"""  if(classementMode === 'clans'){ await chargerClassementClans(); return; }   // patch210
  const limite = classementComplet ? 50 : 10;
  let appel;
  if(classementMode === 'terra')""")
js = rep(js, u"""function renderClassement(){
  renderSaisonsPalmares();""", u"""// patch210 : le classement des clans (même calcul que l'écran Clan)
let clanAOuvrir = null;
async function chargerClassementClans(){
  const [cl, mc] = await Promise.all([sb.rpc('clans_classement'), sb.rpc('mon_clan')]);
  if(cl.error) console.error('Classement des clans :', cl.error.message);
  const monClan = !mc.error && mc.data && mc.data.clan ? mc.data.clan.id : null;
  const tous = cl.error ? [] : (cl.data || []).map((x, i) => ({ ...x, rang: i + 1, est_moi: x.clan_id === monClan }));
  classementDonnees = classementComplet ? tous : tous.filter(x => x.rang <= 10 || x.est_moi);
  classementDonnees.total = tous.length;
  scoreDetail = new Map();
  renderClassement();
}
function renderClassementClans(podium, liste, plus){
  const leg = document.getElementById('clLegende');
  if(leg) leg.hidden = true;
  const nb = (n) => Number(n || 0).toLocaleString('fr-FR');
  const d = classementDonnees;
  const qui = (x) => x.actifs != null ? `${nb(x.actifs)} actif${x.actifs > 1 ? 's' : ''} sur ${nb(x.membres)}` : `${nb(x.membres)} membres`;
  const ligne = (x) => `<button class="cl-ligne cl-clan${x.est_moi ? ' moi' : ''}" data-clan-voir="${echapperTexte(x.clan_id)}" title="Voir les membres de ce clan">
      <span class="cl-rang">${x.rang}</span>${blasonHtml(x.tag, x.couleur, true)}
      <span class="cl-pseudo">${x.est_moi ? '<b>' + echapperTexte(x.nom) + '</b>' : echapperTexte(x.nom)}</span>
      <span class="cl-detail">${qui(x)}</span>
      <span class="cl-score">${nb(x.moyenne)}<small>/ membre</small></span>
    </button>`;
  if(!classementOuvert){
    const moi = d.find(x => x.est_moi);
    podium.innerHTML = '';
    liste.innerHTML = moi ? ligne(moi) : '';
    if(plus) plus.hidden = true;
    return;
  }
  if(!d.length){
    podium.innerHTML = '';
    liste.innerHTML = `<p class="collection-empty">Le classement des clans apparaîtra dès qu'un clan aura 3 membres.</p>`;
    if(plus) plus.hidden = true;
    return;
  }
  const ordre = [2, 1, 3].map(r => d.find(x => x.rang === r)).filter(Boolean);
  podium.innerHTML = ordre.map(x => `
    <button class="cl-marche cl-clan r${x.rang}${x.est_moi ? ' moi' : ''}" data-clan-voir="${echapperTexte(x.clan_id)}" title="Voir les membres de ce clan">
      <span class="cl-rang">${x.rang}</span>
      ${blasonHtml(x.tag, x.couleur)}
      <span class="cl-pseudo">${echapperTexte(x.nom)}</span>
      <span class="cl-score">${nb(x.moyenne)}<small>/ membre</small></span>
      <span class="cl-detail">${qui(x)}</span>
    </button>`).join('');
  liste.innerHTML = d.filter(x => x.rang > 3).map(ligne).join('')
    + `<p class="cl-note-clans">Moyenne de communes du Front par membre actif (jeu ouvert dans les 7 derniers jours) : un gros clan n'a pas d'avantage.</p>`;
  if(plus) plus.hidden = classementComplet || (d.total || 0) <= 10;
}

function renderClassement(){
  renderSaisonsPalmares();""")
js = rep(js, u"""      : classementMode === 'terra' ? 'Le classement Terra apparaîtra dès les premiers paquets ouverts.'
""", u"")
# le rendu des clans prend la main avant celui des joueurs
js = rep(js, u"""    bouton.setAttribute('aria-label', classementOuvert ? 'Replier le classement' : 'Afficher le classement');
  }
  if(!classementOuvert){""", u"""    bouton.setAttribute('aria-label', classementOuvert ? 'Replier le classement' : 'Afficher le classement');
  }
  if(classementMode === 'clans'){ renderClassementClans(podium, liste, plus); return; }   // patch210
  if(!classementOuvert){""")
# toucher un clan : l'écran Clan, ses membres dépliés
js = rep(js, u"""  const ligne = e.target.closest('[data-joueur-id]');
  if(ligne) ouvrirProfil(ligne.dataset.joueurId);
});""", u"""  const clan = e.target.closest('[data-clan-voir]');   // patch210
  if(clan){
    clanAOuvrir = clan.dataset.clanVoir;
    const t = document.querySelector('.tab[data-tab="clan"]');
    if(t) t.click();
    return;
  }
  const ligne = e.target.closest('[data-joueur-id]');
  if(ligne) ouvrirProfil(ligne.dataset.joueurId);
});""")
js = rep(js, u"""                activite: ac.error ? null : new Map((ac.data || []).map(a => [a.joueur_id, a])) };
  renderClan();
}""", u"""                activite: ac.error ? null : new Map((ac.data || []).map(a => [a.joueur_id, a])) };
  renderClan();
  // patch210 : venu du classement, le clan touché est déplié et montré
  if(clanAOuvrir){
    const id = clanAOuvrir; clanAOuvrir = null;
    const estLeMien = clanCache.moi.clan && clanCache.moi.clan.id === id;
    if(!estLeMien && !clansOuverts.has(id)) await basculerClanVu(id);
    const el = document.querySelector('#clanZone [data-clan-voir="' + CSS.escape(id) + '"]');
    if(el && !estLeMien) el.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }
}""")
ecrire('app.js', js)

css = lire('style.css')
assert 'patch210' not in css
css = css.rstrip('\n') + u"""

/* ---------- patch210 : le classement des clans ---------- */
.cl-marche.cl-clan .blason{ width:40px; height:46px; font-size:.82rem; margin:2px 0; }
.cl-ligne.cl-clan .cl-detail{ width:auto; white-space:nowrap; }
.cl-ligne.cl-clan .cl-score small{ white-space:nowrap; }
.cl-note-clans{ margin:6px 2px 0; font-size:.74rem; line-height:1.4; color: var(--brume); }
@media (max-width: 420px){ .cl-ligne.cl-clan .cl-detail{ display:none; } }
"""
ecrire('style.css', css)
print(u'patch210 applique. Lancer : python3 maj-version.py')
