# patch458 : clans S3 — défense alliée, classement des 5 meilleurs, objectif de la semaine (s3-28)
import sys, os
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(fichier, a, b, n=1):
    p = os.path.join(R, fichier); s = open(p, encoding='utf-8').read()
    assert s.count(a) == n, (fichier, a[:80], s.count(a)); s = s.replace(a, b); open(p, 'w', encoding='utf-8').write(s)
A = 'app.js'
# classement : les étiquettes suivent le mode du serveur
rep(A, "${nb(x.moyenne)}<small>/ membre</small>", "${nb(x.moyenne)}<small>${clScoreUnite()}</small>", 2)
rep(A, "+ `<p class=\"cl-note-clans\">Moyenne de communes du Front par membre actif (jeu ouvert dans les 7 derniers jours) : un gros clan n'a pas d'avantage.</p>`;",
       "+ `<p class=\"cl-note-clans\">${clNoteClassement()}</p>`;   // patch458")
rep(A, "legende.innerHTML = (quoi === 'clans' ? 'Moyenne par membre actif'", "legende.innerHTML = (quoi === 'clans' ? (CL_TOP5 ? 'Communes des 5 meilleurs membres actifs' : 'Moyenne par membre actif')")
rep(A, "panneau.innerHTML = quoi === 'clans' ? CL_CALC_CLANS : CL_CALC_FRONT;", "panneau.innerHTML = quoi === 'clans' ? (CL_TOP5 ? CL_CALC_CLANS_TOP5 : CL_CALC_CLANS) : CL_CALC_FRONT;   // patch458")
rep(A, "<span class=\"cl-score\">${nbClan(x.moyenne)}<small>${x.actifs != null ? 'par membre actif' : 'par membre'}</small>", "<span class=\"cl-score\">${nbClan(x.moyenne)}<small>${clScoreUniteLong(x.actifs != null)}</small>")
rep(A, "<p class=\"clan-note\">À la moyenne de communes du Front par membre actif (jeu ouvert dans les 7 derniers jours), jamais au total : un gros clan n'a pas d'avantage, et un membre absent ne fait pas baisser son clan.</p>${blocFormation}",
       "<p class=\"clan-note\">${CL_TOP5 ? clNoteClassement() : 'À la moyenne de communes du Front par membre actif (jeu ouvert dans les 7 derniers jours), jamais au total : un gros clan n\\'a pas d\\'avantage, et un membre absent ne fait pas baisser son clan.'}</p>${blocFormation}")
rep(A, "<span class=\"puce\">Moyenne par membre${actifs ? ' actif' : ''} <b>${nbClan(moyenne)}</b></span>",
       "<span class=\"puce\">${CL_TOP5 ? 'Score (5 meilleurs)' : `Moyenne par membre${actifs ? ' actif' : ''}`} <b>${nbClan(CL_TOP5 ? clScoreClan(c.membres, act) : moyenne)}</b></span>")
rep(A, "if(c.rang && c.moyenne != null) chiffres.push([nb(c.moyenne), 'par membre actif']);", "if(c.rang && c.moyenne != null) chiffres.push([nb(c.moyenne), CL_TOP5 ? 'points' : 'par membre actif']);   // patch458")
rep(A, "  const tous = cl.error ? [] : (cl.data || []).map((x, i) => ({ ...x, rang: i + 1, est_moi: x.clan_id === monClan }));",
       "  if(!cl.error && typeof clModeMaj === 'function') clModeMaj(cl.data);   // patch458\n  const tous = cl.error ? [] : (cl.data || []).map((x, i) => ({ ...x, rang: i + 1, est_moi: x.clan_id === monClan }));")
rep(A, "  clanCache = { moi: mc.data || {}, classement: cl.error ? [] : (cl.data || []), formation: cf.error ? [] : (cf.data || []),",
       "  if(!cl.error && typeof clModeMaj === 'function') clModeMaj(cl.data);   // patch458\n  if(typeof objCharger === 'function') await objCharger(true);   // patch458\n  clanCache = { moi: mc.data || {}, classement: cl.error ? [] : (cl.data || []), formation: cf.error ? [] : (cf.data || []),")
rep(A, "    (cl.error ? [] : cl.data || []).forEach((x, i) => { const o = { ...x, id: x.clan_id, rang: i + 1 };",
       "    if(!cl.error && typeof clModeMaj === 'function') clModeMaj(cl.data);   // patch458\n    (cl.error ? [] : cl.data || []).forEach((x, i) => { const o = { ...x, id: x.clan_id, rang: i + 1 };")
# défense alliée : chargée avec les sièges contre moi ; Mon front
rep(A, "  renderMenacesSiege();\n  sgRafraichirFiche();   // patch406\n", "  renderMenacesSiege();\n  if(typeof sgaCharger === 'function') sgaCharger();   // patch458\n  sgRafraichirFiche();   // patch406\n")
rep(A, "z.innerHTML = blocDanger + (typeof s3MfoOrdres === 'function' ? s3MfoOrdres() : '') + blocEnergie",
       "z.innerHTML = blocDanger + (typeof sgaMfo === 'function' ? sgaMfo() : '') + (typeof s3MfoOrdres === 'function' ? s3MfoOrdres() : '') + (typeof objMfo === 'function' ? objMfo() : '') + blocEnergie")
# objectif : dans l'onglet Clan (avec la Centrale et les ordres) et chargé avec eux
rep(A, "function s3ClanHtml(){\n  let h = '';", "function s3ClanHtml(){\n  let h = typeof objHtml === 'function' ? objHtml() : '';   // patch458")
rep(A, "    if(typeof s3Charger === 'function') s3Charger();   // patch456\n", "    if(typeof s3Charger === 'function') s3Charger();   // patch456\n    if(typeof objCharger === 'function') objCharger();   // patch458\n")
# le code et le style
s = open(os.path.join(R, A), encoding='utf-8').read().rstrip('\n') + '\n' + open(os.path.join(R, '_patchs', 'patch458.js'), encoding='utf-8').read()
open(os.path.join(R, A), 'w', encoding='utf-8').write(s)
c = open(os.path.join(R, 'style.css'), encoding='utf-8').read().rstrip('\n') + '\n' + open(os.path.join(R, '_patchs', 'patch458.css'), encoding='utf-8').read()
open(os.path.join(R, 'style.css'), 'w', encoding='utf-8').write(c)
# les règles
H = 'index.html'
rep(H, "Le classement des clans fait la <b>moyenne</b> de leurs membres actifs (jeu ouvert dans les 7 derniers jours) ; il faut 3 membres pour être classé.",
       "<span data-s3=\"moyenne\">Le classement des clans fait la <b>moyenne</b> de leurs membres actifs (jeu ouvert dans les 7 derniers jours) ; il faut 3 membres pour être classé.</span><span data-s3=\"top5\">Le classement des clans additionne les communes de leurs <b>5 meilleurs membres actifs</b> (jeu ouvert dans les 7 derniers jours) : une recrue ne fait jamais baisser son clan ; il faut 3 membres pour être classé.</span>")
rep(H, """            <p data-s3="ordres"><b>Ordres du chef</b>""", """            <p data-s3="allie"><b>Défense alliée</b> (Front) : quand la commune d'un membre de ton clan est assiégée, elle apparaît dans Défendre (« Ton clan est assiégé ») et tout le clan est prévenu quand la jauge passe les deux tiers. Tu la renforces avec ton énergie : <b>× 1</b> par énergie (le propriétaire, lui, × 1,2), <b>60 énergie au plus</b> par siège pour toi. La défense réussie compte pour le propriétaire.</p>
            <p data-s3="objectif"><b>Objectif de la semaine</b> (onglet Clan) : les communes prises par les membres du lundi au dimanche. Trois paliers, fixés le lundi selon le nombre de membres actifs (2, 4 et 7 communes par actif, 3 actifs au moins) : <b>bronze</b> +5 lingots, <b>argent</b> +10 lingots et +10 énergie, <b>or</b> +20 lingots et +20 énergie. Chaque membre qui a pris une commune ou renforcé un allié dans la semaine ramasse sa part, jusqu'à la fin de la semaine suivante.</p>
            <p data-s3="ordres"><b>Ordres du chef</b>""")
print('patch458 : ok')
