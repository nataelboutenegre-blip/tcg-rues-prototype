# patch531 (H34VEN, Saaslil) : les échanges de clan disent quand ils redeviennent possibles (s3-69).
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

# l'aide : « dans 5 h », « dans 40 min »
rep('app.js', "function ceDans(iso){",
"""function ceDansH(iso){   // patch531
  const ms = new Date(iso).getTime() - Date.now();
  if(!(ms > 0)) return 'maintenant';
  return ms < 3600000 ? `dans ${Math.max(1, Math.ceil(ms / 60000))} min` : `dans ${Math.ceil(ms / 3600000)} h`;
}
function cePret(m){ return m && m.pret_le && new Date(m.pret_le).getTime() > Date.now(); }   // patch531 : coéquipier arrivé il y a moins de 48 h
function ceDans(iso){""")

# la liste des coéquipiers (onglet Clan)
rep('app.js', """aria-pressed="${m.id === clanEch.qui}"${parMembre && !resteAvec(m) ? ' disabled' : ''}>""",
              """aria-pressed="${m.id === clanEch.qui}"${(parMembre && !resteAvec(m)) || cePret(m) ? ' disabled' : ''}>""")
rep('app.js', """${parMembre ? `<span class="ce-reste">· ${resteAvec(m) ? 'encore ' + resteAvec(m) : 'demain'}</span>` : ''}</button>`""",
              """${cePret(m) ? `<span class="ce-reste" title="Arrivé il y a moins de 48 h">· ${ceDansH(m.pret_le)}</span>` : parMembre ? `<span class="ce-reste">· ${resteAvec(m) ? 'encore ' + resteAvec(m) : e.demain_le ? ceDansH(e.demain_le) : 'demain'}</span>` : ''}</button>`""")
rep('app.js', """(48 h après ton arrivée).</p>`""", """(48 h après ton arrivée, ${ceDansH(e.pret_le)}).</p>`""")
rep('app.js', """? (parMembre ? `<p class="clan-note">Tu as fait tes ${maxEch} échanges du jour avec chaque coéquipier. Reviens demain.</p>`""",
              """? (parMembre ? `<p class="clan-note">Tu as fait tes ${maxEch} échanges du jour avec chaque coéquipier. À nouveau possible ${e.demain_le ? ceDansH(e.demain_le) : 'demain'}.</p>`""")

# la fiche d'une commune d'un coéquipier
rep('app.js', """      : e.par_membre ? (mb && Number(mb.faits || 0) >= (e.max || 6) ? `Vous avez fait vos ${e.max || 6} échanges du jour ensemble` : '')   // patch493""",
              """      : cePret(mb) ? `${c.pseudo || 'Ton coéquipier'} est arrivé il y a moins de 48 h : échange possible ${ceDansH(mb.pret_le)}`   // patch531
      : e.par_membre ? (mb && Number(mb.faits || 0) >= (e.max || 6) ? `Vous avez fait vos ${e.max || 6} échanges du jour ensemble · à nouveau ${e.demain_le ? ceDansH(e.demain_le) : 'demain'}` : '')   // patch493""")
rep('app.js', "    const raison = !e ? '' : e.pret_le ? 'Échanges possibles 48 h après ton arrivée dans le clan'",
              "    const raison = !e ? '' : e.pret_le ? `Échanges possibles 48 h après ton arrivée dans le clan (${ceDansH(e.pret_le)})`")
rep('app.js', "      const raison = e.pret_le ? 'Échanges possibles 48 h après ton arrivée dans ton clan'",
              "      const raison = e.pret_le ? `Échanges possibles 48 h après ton arrivée dans ton clan (${ceDansH(e.pret_le)})`")


p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = d[0]; assert e['date'] == '2026-11-24'
l = "⏳ Échanges de clan : le jeu dit maintenant quand ils redeviennent possibles (coéquipier arrivé il y a moins de 48 h, échanges du jour faits, commune prise ou échangée récemment : « dans 6 h »). Merci H34VEN et Saaslil."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
