# patch493 : les textes du jeu suivent s3-48 (échanges de clan : 6 par jour avec chaque coéquipier, idée de H34VEN).
# Le nombre vient du serveur (clan_ech_etat().max, réglage config_jeu 'clans_s3'.echanges_jour) : les textes ne
# l'écrivent plus en dur. Règles et cloche.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A, H = 'app.js', 'index.html'
rep(A, "e.par_membre ? (mb && Number(mb.faits || 0) >= (e.max || 3) ? 'Vous avez fait vos 3 échanges du jour ensemble' : '')",
       "e.par_membre ? (mb && Number(mb.faits || 0) >= (e.max || 6) ? `Vous avez fait vos ${e.max || 6} échanges du jour ensemble` : '')   // patch493")
rep(A, "parMembre ? '<p class=\"clan-note\">Tu as fait tes 3 échanges du jour avec chaque coéquipier. Reviens demain.</p>'",
       "parMembre ? `<p class=\"clan-note\">Tu as fait tes ${maxEch} échanges du jour avec chaque coéquipier. Reviens demain.</p>`")
rep(A, ": '<p class=\"clan-note\">Tu as fait tes 3 échanges du jour. Reviens demain.</p>')",
       ": `<p class=\"clan-note\">Tu as fait tes ${maxEch} échanges du jour. Reviens demain.</p>`)")
rep(A, "${parMembre ? '<b>3 échanges par jour avec chaque coéquipier</b>, 3 propositions en attente par coéquipier' : '3 échanges par jour et par joueur, 3 propositions en attente au plus'}",
       "${parMembre ? `<b>${maxEch} échanges par jour avec chaque coéquipier</b>, ${maxEch} propositions en attente par coéquipier` : `${maxEch} échanges par jour et par joueur, ${maxEch} propositions en attente au plus`}")
rep(H, "3 échanges par jour avec chaque coéquipier (et 3 propositions en attente par coéquipier)",
       "6 échanges par jour avec chaque coéquipier (et 6 propositions en attente par coéquipier)")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = next(x for x in d if x.get('date') == '2026-11-22')
l = "🤝 Échanges de clan : 6 par jour avec chaque coéquipier au lieu de 3, pour finir vos départements et vos régions entre vous (idée de H34VEN)."
if l not in e['nouveautes']: e['nouveautes'].insert(1, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
