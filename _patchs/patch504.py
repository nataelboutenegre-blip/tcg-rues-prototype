# patch504 : le centre de notifications passe à la saison 3 (va avec s3-55). Décision de Nataël 22/11 22 h 08.
# - « On assiège ta commune » : la cloche lit les sièges de la saison 3 (sieges_contre_moi_v2) au lieu des séries
#   de la saison 2 (vides depuis le lancement) : attaquant, jauge, temps avant la chute, bouton Renforcer.
#   Une nouvelle ligne quand la jauge passe un tiers puis deux tiers. Sourdine, seuil et « Laisser filer » respectés.
# - « Mes sièges » remplace « Défenses » (on t'a défendu, il manque de l'énergie, ton siège est tombé), avec un
#   interrupteur Téléphone ; « Clan » gagne aussi son interrupteur Téléphone.
# - « Avant toi » : la jauge en % pour les sièges de la saison 3 (au lieu de « x / 3 »).
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
A = 'app.js'
rep(A, "                    tel: { attaque: true, paquet: true }, seuil: 'commun',",
       "                    tel: { attaque: true, paquet: true, defense: true, clan: true }, seuil: 'commun',")
rep(A, "  const [prefs, journal, sieges, ech, clanE, alertes, quetes, recolte, clan, effaces, diplo, merv, siegeAl] = await Promise.all([",
       "  const [prefs, journal, sieges, ech, clanE, alertes, quetes, recolte, clan, effaces, diplo, merv, siegeAl, sieges3] = await Promise.all([")
rep(A, "    SAISON2 ? rpc('mes_alertes_siege') : null,   // patch485\n  ]);",
       "    SAISON2 ? rpc('mes_alertes_siege') : null,   // patch485\n    SAISON2 ? rpc('sieges_contre_moi_v2') : null,   // patch504 : les sièges de la saison 3\n  ]);")
rep(A, "clan, effaces, diplo, merv, siegeAl };", "clan, effaces, diplo, merv, siegeAl, sieges3 };   // patch504")
rep(A, "  if(p.jeu.attaque && Array.isArray(d.sieges)){\n    for(const m of d.sieges){",
       """  if(p.jeu.attaque && Array.isArray(d.sieges3)){   // patch504 : les sièges de la saison 3
    const laisses = typeof sgLaisses === 'function' ? sgLaisses() : new Set();
    for(const m of d.sieges3){
      const code = String(m.commune || ''), depM = ncDepDe(code);
      if(!code || laisses.has(m.id) || p.sourdine.includes(code) || p.sourdine_dep.includes(depM)) continue;
      if(!p.alerte_dep.includes(depM) && sousSeuil(code)) continue;
      const res = nb(m.resistance), deg = Math.floor(nb(m.degats)), pc = res ? Math.min(100, Math.floor(100 * deg / res)) : 0;
      const palier = pc >= 66 ? 2 : pc >= 33 ? 1 : 0;
      const tombe = m.tombe_le ? new Date(m.tombe_le).getTime() - Date.now() : 0;
      items.push({ cle: `sg3|${m.id}|${palier}`, sec: 'afaire', c: 'danger', i: '⚔️', mode: 'front',
        t: `<b>${echapperTexte(m.attaquant_pseudo || 'Un joueur')}</b> assiège <button type="button" class="nc-lien" data-nc-voir="${echapperTexte(code)}" title="Voir sur la carte">${echapperTexte(m.nom || nomDe(code))}</button> ${badgeDept(m.dept || depDuCode(code))}`,
        s: `Jauge ${deg} / ${res} · ${pc} %${m.long ? ' · siège long' : ''}${tombe > 0 ? ` · sans nouvelle vague, son siège s’arrête dans ${formatDuree(tombe)}` : ''}`,
        a: 'Renforcer', rouge: palier === 2, sourdine: code, aller: () => ncAller('front', 'defense') });
    }
  }
  if(p.jeu.attaque && Array.isArray(d.sieges)){
    for(const m of d.sieges){""")
rep(A, "        s: `Ton siège est effacé : tu en étais à ${nb(x.victoires)} / 3 · ${ilYA(x.le)}` });",
       "        s: `Ton siège est effacé : ${x.pct != null ? `ta jauge était à ${nb(x.pct)} %` : `tu en étais à ${nb(x.victoires)} / 3`} · ${ilYA(x.le)}` });   // patch504")
rep(A, "  if(Array.isArray(d.siegeAl)){\n", "  if(p.jeu.defense && Array.isArray(d.siegeAl)){   // patch504 : « Mes sièges »\n")
rep(A, """  ['attaque', 'On t’attaque', 'Une série en cours contre une de tes communes', true],
  ['perdue', 'Commune perdue', 'Un joueur t’a pris une commune', false],
  ['defense', 'Défenses', 'Tes défenses réussies', false],""",
"""  ['attaque', 'On assiège ta commune', 'Un siège commence, puis quand sa jauge monte', true],   // patch504
  ['perdue', 'Commune perdue', 'Un joueur t’a pris une commune', false],
  ['defense', 'Mes sièges', 'On t’a défendu, il te manque de l’énergie, ou ton siège est tombé', true],   // patch504""")
rep(A, "  ['clan', 'Clan', 'Invitations, échanges de clan', false],",
       "  ['clan', 'Clan', 'Invitations, échanges, ordres du chef, appels à l’aide', true],   // patch504")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = next(x for x in d if x.get('date') == '2026-11-22')
l = "🔔 La cloche passe à la saison 3 : elle montre les sièges contre tes communes (jauge, temps avant la chute, bouton Renforcer). Dans ses réglages, « Mes sièges » et « Clan » peuvent maintenant être coupés sur le téléphone."
if l not in e['nouveautes']: e['nouveautes'].insert(0, l)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('nouveautes.json : ok')
