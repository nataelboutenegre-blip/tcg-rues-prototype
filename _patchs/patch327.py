# patch327 (3/11/2026) : échanges de clan, 3 par jour AVEC CHAQUE coéquipier (s2-88)
# Décision de Nataël (idée d'Oshannir et Maroli). Aperçu : apercu-echanges-par-membre.png.
#  - « Échanges du clan » : la puce dit « 3 par jour avec chaque coéquipier » ;
#    chaque coéquipier montre « encore N » ou « demain » (grisé à 3) ;
#  - la fiche d'une commune d'un coéquipier : « Plus d'échange possible
#    aujourd'hui avec lui » seulement si VOUS avez fait vos 3 ensemble ;
#  - les règles (bloc du clan et Règles du jeu).
# Tant que s2-88 n'est pas lancé (pas de « par_membre »), l'écran reste comme avant.
import pathlib

def patcher(nom, remplacements):
    F = pathlib.Path(nom)
    s = F.read_text(encoding='utf-8')
    for avant, apres, n in remplacements:
        c = s.count(avant)
        assert c == n, f'{nom} : {c} fois au lieu de {n} : {avant[:70]!r}'
        s = s.replace(avant, apres)
    F.write_text(s, encoding='utf-8')

patcher('app.js', [
    # la fiche d'une commune d'un coéquipier
    ("""    const raison = !e ? '' : e.pret_le ? 'Échanges possibles 48 h après ton arrivée dans le clan'
      : Math.max(0, (e.max || 3) - (e.faits || 0)) === 0 ? 'Plus d’échange possible aujourd’hui' : '';""",
     """    const mb = e && e.par_membre ? (e.membres || []).find(x => x.id === c.joueurId) : null;   // patch327
    const raison = !e ? '' : e.pret_le ? 'Échanges possibles 48 h après ton arrivée dans le clan'
      : e.par_membre ? (mb && Number(mb.faits || 0) >= (e.max || 3) ? 'Vous avez fait vos 3 échanges du jour ensemble' : '')
      : Math.max(0, (e.max || 3) - (e.faits || 0)) === 0 ? 'Plus d’échange possible aujourd’hui' : '';""", 1),
    # le bloc « Échanges du clan »
    ("""  const restant = Math.max(0, (e.max || 3) - (e.faits || 0));   // patch250""",
     """  const maxEch = e.max || 3, parMembre = !!e.par_membre;   // patch327 : par coéquipier (s2-88)
  const resteAvec = (m) => Math.max(0, maxEch - Number(m.faits || 0));
  const restant = parMembre ? ((e.membres || []).some(m => resteAvec(m) > 0) ? maxEch : 0)
                            : Math.max(0, maxEch - (e.faits || 0));   // patch250""", 1),
    ("""    : restant === 0 ? '<p class="clan-note">Tu as fait tes 3 échanges du jour. Reviens demain.</p>'""",
     """    : restant === 0 ? (parMembre ? '<p class="clan-note">Tu as fait tes 3 échanges du jour avec chaque coéquipier. Reviens demain.</p>'
                                 : '<p class="clan-note">Tu as fait tes 3 échanges du jour. Reviens demain.</p>')""", 1),
    ("""        <div class="ce-membres">${membres.map(m => `<button type="button" class="ce-membre" data-ce-qui="${echapperTexte(m.id)}" aria-pressed="${m.id === clanEch.qui}"><span class="av" style="--clan:${(clanCache && clanCache.moi && clanCache.moi.clan || {}).couleur || '#E07A2E'}">${echapperTexte((m.pseudo || '?')[0].toUpperCase())}</span>${echapperTexte(m.pseudo)}</button>`).join('')}</div></div>""",
     """        <div class="ce-membres">${membres.map(m => `<button type="button" class="ce-membre" data-ce-qui="${echapperTexte(m.id)}" aria-pressed="${m.id === clanEch.qui}"${parMembre && !resteAvec(m) ? ' disabled' : ''}><span class="av" style="--clan:${(clanCache && clanCache.moi && clanCache.moi.clan || {}).couleur || '#E07A2E'}">${echapperTexte((m.pseudo || '?')[0].toUpperCase())}</span>${echapperTexte(m.pseudo)}${parMembre ? `<span class="ce-reste">· ${resteAvec(m) ? 'encore ' + resteAvec(m) : 'demain'}</span>` : ''}</button>`).join('')}</div></div>""", 1),
    ("""  return `<div class="ce-bloc"><div class="ce-tete"><h2>Échanges du clan</h2><span class="puce">${restant ? `<b>${restant}</b> échange${restant > 1 ? 's' : ''} possible${restant > 1 ? 's' : ''} aujourd'hui` : 'plus d\\'échange aujourd\\'hui'}</span></div>""",
     """  return `<div class="ce-bloc"><div class="ce-tete"><h2>Échanges du clan</h2><span class="puce">${parMembre ? `<b>${maxEch}</b> par jour avec chaque coéquipier` : restant ? `<b>${restant}</b> échange${restant > 1 ? 's' : ''} possible${restant > 1 ? 's' : ''} aujourd'hui` : 'plus d\\'échange aujourd\\'hui'}</span></div>""", 1),
    ("""<li>3 échanges par jour et par joueur, 3 propositions en attente au plus. Une proposition expire au bout de 24 h.</li>""",
     """<li>${parMembre ? '<b>3 échanges par jour avec chaque coéquipier</b>, 3 propositions en attente par coéquipier' : '3 échanges par jour et par joueur, 3 propositions en attente au plus'}. Une proposition expire au bout de 24 h.</li>""", 1),
])

patcher('index.html', [
    ("""3 échanges par jour au plus (et 3 propositions en attente)""",
     """3 échanges par jour avec chaque coéquipier (et 3 propositions en attente par coéquipier)""", 1),
])

F = pathlib.Path('style.css')
s = F.read_text(encoding='utf-8')
if 'patch327' not in s:
    s = s.rstrip('\n') + """

/* patch327 : échanges de clan par coéquipier */
.ce-reste{ font-size:.72rem; color:var(--brume, #A9BCD4); margin-left:2px; font-weight:600; }
.ce-membre:disabled{ opacity:.45; cursor:default; }
"""
    F.write_text(s, encoding='utf-8')
print('patch327 appliqué')
