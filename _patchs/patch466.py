# patch466 : classement des clans aux POINTS des 5 meilleurs membres actifs (s3-33, idée d'Oshannir).
# Seulement les textes du mode « 5 meilleurs » (éteint tant que clans_s3.classement_top5 = 0) ;
# la page Clan prend le score du serveur au lieu de recompter les communes.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if b in t and a not in t: print(f'{f} : déjà fait'); return
    assert t.count(a) == 1, (f, t.count(a), a[:70])
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

A = 'app.js'
rep(A, "(CL_TOP5 ? 'Communes des 5 meilleurs membres actifs' : 'Moyenne par membre actif')",
       "(CL_TOP5 ? 'Points des 5 meilleurs membres actifs' : 'Moyenne par membre actif')")
rep(A, "return CL_TOP5 ? 'Les communes du Front des 5 meilleurs membres actifs (jeu ouvert dans les 7 derniers jours), additionnées : une recrue ne fait jamais baisser son clan.'",
       "return CL_TOP5 ? 'Les points du classement du Front des 5 meilleurs membres actifs (jeu ouvert dans les 7 derniers jours), additionnés : une recrue ne fait jamais baisser son clan.'")
rep(A, "<p class=\"cl-calc-txt\">On additionne les communes du Front des <b>5 meilleurs membres actifs</b> du clan (jeu ouvert dans les 7 derniers jours).",
       "<p class=\"cl-calc-txt\">On additionne les <b>points du classement du Front</b> (cartes, combats, territoires, bâtiments) des <b>5 meilleurs membres actifs</b> du clan (jeu ouvert dans les 7 derniers jours).")
# la page Clan : le score du serveur (le même que dans le classement)
rep(A, "<b>${nbClan(CL_TOP5 ? clScoreClan(c.membres, act) : moyenne)}</b>",
       "<b>${CL_TOP5 ? clScoreServeur(c) : nbClan(moyenne)}</b>")
rep(A, "function clScoreClan(membres, act){",
"""function clScoreServeur(c){   // patch466 : les points viennent du serveur (clans_classement), pas d'un recomptage
  const r = (clanCache && clanCache.classement || []).find(x => c && x.clan_id === c.id);
  return r ? nbClan(r.moyenne) : '—';
}
function clScoreClan(membres, act){""")

I = 'index.html'
rep(I, "<span data-s3=\"top5\">Le classement des clans additionne les communes de leurs <b>5 meilleurs membres actifs</b>",
       "<span data-s3=\"top5\">Le classement des clans additionne les <b>points</b> du classement du Front de leurs <b>5 meilleurs membres actifs</b>")
