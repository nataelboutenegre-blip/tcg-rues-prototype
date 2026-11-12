# patch422 (12/11/2026) : le clan sur le profil, la fiche d'un clan, les pseudos du tchat (idée d'Oshannir)
# - Profil d'un joueur : son clan sous son titre (blason, nom, sigle, rang des clans) ; le toucher ouvre la fiche du clan.
# - Fiche d'un clan (nouvelle) : blason, sigle, rang, membres (chef, bras droit, actif ou absent, communes) ; chaque
#   pseudo ouvre son profil ; « Voir son territoire » met tous les membres en évidence sur la carte.
# - Tchat du clan : le pseudo de l'auteur ouvre son profil ; « @pseudo » devient un lien vers le profil (le message
#   qui te cite est marqué d'un trait doré) ; taper « @ » propose les pseudos (ton clan d'abord).
# Rien côté serveur : clans_carte, clans_classement, clans_en_formation et clan_membres_voir existent déjà.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, C = 'app.js', 'style.css'
if 'patch422' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')
# une fenêtre peut céder la place à une autre sans refermer le fond (sans laisser traîner son écouteur Échap)
rep(A, """  fond.onclick = (e) => { if(e.target === fond) fermer(null); };
  return fermer;
}""", """  fond.onclick = (e) => { if(e.target === fond) fermer(null); };
  fermer.detacher = () => document.removeEventListener('keydown', surTouche);   // patch422 : passer d'une fiche à l'autre
  return fermer;
}""")
# le profil : le clan du joueur
rep(A, """    chargerStatEchanges(joueurId), chargerTitreJoueur(joueurId)]);""",
"""    chargerStatEchanges(joueurId), chargerTitreJoueur(joueurId), chargerClansInfos()]);   // patch422 : son clan""")
rep(A, """          p.rang > 0 ? ` · <span class="pr-rang">${p.rang}${p.rang === 1 ? 'er' : 'e'}</span>` : ''}</p>
      </div>
      <div class="pr-corps">""", """          p.rang > 0 ? ` · <span class="pr-rang">${p.rang}${p.rang === 1 ? 'er' : 'e'}</span>` : ''}</p>
        ${clanProfilHtml(p)}
      </div>
      <div class="pr-corps">""")
rep(A, """  fermerProfil = ouvrirFenetre(`
    <div class="fenetre profil" role="dialog\"""", """  quitterFiches('profil');   // patch422 : venu de la fiche d'un clan
  if(fermerProfil && fermerProfil.detacher) fermerProfil.detacher();
  fermerProfil = ouvrirFenetre(`
    <div class="fenetre profil" role="dialog\"""")
# le tchat du clan : auteur et @pseudo cliquables, suggestions
rep(A, """  const lignes = tchat.msgs.map((m, i) => {
    const prec = tchat.msgs[i - 1];""", """  const idx = tchatIndex();   // patch422
  const lignes = tchat.msgs.map((m, i) => {
    const prec = tchat.msgs[i - 1];""")
rep(A, """    return `<div class="tc-msg${moi ? ' moi' : ''}${suite ? ' suite' : ''}" data-tc-id="${m.id}">
      ${suite ? '' : `<div class="tc-tete"><b class="${role(m.auteur)}">${echapperTexte(m.pseudo || 'Joueur')}</b><span>${tchatHeure(m.le)}</span></div>`}
      <div class="tc-bulle">${m.supprime ? '<i>Message supprimé</i>' : echapperTexte(m.texte)}</div>""",
"""    const tx = m.supprime ? null : tchatTexteHtml(m.texte, idx);   // patch422 : les @pseudo
    return `<div class="tc-msg${moi ? ' moi' : ''}${suite ? ' suite' : ''}${tx && tx.moi && !moi ? ' mentionne' : ''}" data-tc-id="${m.id}">
      ${suite ? '' : `<div class="tc-tete"><button type="button" class="tc-qui ${role(m.auteur)}" data-tc-profil="${echapperTexte(m.auteur || '')}">${echapperTexte(m.pseudo || 'Joueur')}</button><span>${tchatHeure(m.le)}</span></div>`}
      <div class="tc-bulle">${m.supprime ? '<i>Message supprimé</i>' : tx.html}</div>""")
rep(A, """    <form class="tc-saisie" id="tcForm">""", """    <div class="tc-suggest" id="tcSuggest" hidden></div>
    <form class="tc-saisie" id="tcForm">""")
rep(A, """    <p class="tc-note">Visible seulement par les membres du clan. Les messages s’effacent au bout de 7 jours.</p>""",
"""    <p class="tc-note">Visible seulement par les membres du clan. Les messages s’effacent au bout de 7 jours. Tape @ pour citer un joueur.</p>""")
open(A, 'a', encoding='utf-8').write(open('_patchs/patch422-clans.js', encoding='utf-8').read())
open(C, 'a', encoding='utf-8').write(open('_patchs/patch422-clans.css', encoding='utf-8').read())
print('patch422 OK')
