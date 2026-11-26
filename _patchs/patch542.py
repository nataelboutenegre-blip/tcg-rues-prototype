# patch542 (Arkhannou, Maroli ; s3-81) : échanges entre clans : un par jour AVEC CHAQUE CLAN, remis à zéro à minuit.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
A = 'app.js'
rep(A, "      const dispo = e.inter_dispo_le ? new Date(e.inter_dispo_le) : null;\n",
       "      const dejaFait = (e.inter_faits || []).includes(sonClan.tag);   // patch542 : un échange par jour avec chaque clan\n")
rep(A, """        : dispo && dispo.getTime() > Date.now() ? `Un échange entre clans par jour : le prochain le ${dispo.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })} à ${dispo.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}` : '';""",
       """        : dejaFait ? `Tu as déjà fait ton échange du jour avec le clan [${sonClan.tag}] · à nouveau ${e.demain_le ? ceDansH(e.demain_le) : 'à minuit'}` : '';""")
rep(A, "Proposer un échange <small>· 1 par jour</small>", "Proposer un échange <small>· 1 par jour avec chaque clan</small>")
rep(A, """<b>un échange par jour</b>${clanEch.etat && clanEch.etat.inter_dispo_le && new Date(clanEch.etat.inter_dispo_le).getTime() > Date.now() ? ` (ton prochain le ${new Date(clanEch.etat.inter_dispo_le).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })})` : ''}.</li></ul></div>`;   // patch398""",
       """<b>un échange par jour avec chaque clan</b>, remis à zéro à minuit${clanEch.etat && (clanEch.etat.inter_faits || []).length ? ` (déjà fait aujourd’hui avec ${clanEch.etat.inter_faits.map(t => '[' + echapperHtml(t) + ']').join(', ')})` : ''}.</li></ul></div>`;   // patch398, patch542""")
rep(A, "' Un échange entre clans par jour.'", "' Un échange par jour avec chaque clan, remis à zéro à minuit.'")
rep('index.html', "mais <b>un échange par jour</b> par joueur, 2 propositions en attente au plus.</p><!-- patch341, patch398, patch425 -->",
     "mais <b>un échange par jour avec chaque clan</b>, remis à zéro à minuit, et 2 propositions en attente au plus. Une fois par jour, un échange dans ton clan peut aussi se faire avec <b>un cran de rareté d'écart</b> (légendaire contre épique, épique contre rare…).</p><!-- patch341, patch398, patch425, patch542 -->")
