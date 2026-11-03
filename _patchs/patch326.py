# patch326 (3/11/2026) : la course à la commune (s2-87), idée d'Oshannir
# Quand un joueur prend une commune, les sièges des autres sur cette commune
# sont effacés (côté serveur, s2-87). Ici :
#  - la cloche prévient ceux dont le siège a été effacé (« X a pris Y avant
#    toi · ton siège est effacé : tu en étais à 2 / 3 »), réglage « Commune
#    perdue » ; lu par mes_sieges_effaces() (si la fonction manque : rien) ;
#  - la règle dans les Règles du jeu (Front) et l'aide de l'onglet Combat.
# Aperçu validé : apercu-sieges-effaces.png.
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
    ("""  const [prefs, journal, sieges, ech, clanE, alertes, quetes, recolte, clan] = await Promise.all([""",
     """  const [prefs, journal, sieges, ech, clanE, alertes, quetes, recolte, clan, effaces] = await Promise.all([""", 1),
    ("""    CLANS ? rpc('mon_clan') : null,
  ]);
  if(!NC.prefs){""",
     """    CLANS ? rpc('mon_clan') : null,
    SAISON2 ? rpc('mes_sieges_effaces') : null,   // patch326
  ]);
  if(!NC.prefs){""", 1),
    ("""  NC.d = { journal, sieges, ech, clanE, alertes, quetes, recolte: Array.isArray(recolte) ? recolte[0] : recolte, clan };""",
     """  NC.d = { journal, sieges, ech, clanE, alertes, quetes, recolte: Array.isArray(recolte) ? recolte[0] : recolte, clan, effaces };""", 1),
    ("""  // --- Depuis ta dernière visite (7 jours) ---
  const limite = Date.now() - 7 * 864e5;
""",
     """  // --- Depuis ta dernière visite (7 jours) ---
  const limite = Date.now() - 7 * 864e5;
  // patch326 : la course à la commune, un autre l'a prise avant moi (s2-87)
  if(p.jeu.perdue && Array.isArray(d.effaces)){
    for(const x of d.effaces){
      if(new Date(x.le).getTime() < limite) continue;
      items.push({ cle: `se|${x.commune_code}|${x.le}`, sec: 'histo', c: 'histo', i: '💨', mode: 'front',
        t: `<b>${echapperTexte(x.par_pseudo || 'Un joueur')}</b> a pris <b>${echapperTexte(x.commune_nom || x.commune_code)}</b> ${badgeDept(depDuCode(x.commune_code))} avant toi`,
        s: `Ton siège est effacé : tu en étais à ${nb(x.victoires)} / 3 · ${ilYA(x.le)}` });
    }
  }
""", 1),
])

patcher('index.html', [
    ("""            <p><b>Défendre</b> : quand un joueur gagne un round contre toi, tu peux tenter une défense pour <b>1 énergie</b>, deux fois par attaque. Réussie, l'attaquant perd une victoire.</p>""",
     """            <p><b>Défendre</b> : quand un joueur gagne un round contre toi, tu peux tenter une défense pour <b>1 énergie</b>, deux fois par attaque. Réussie, l'attaquant perd une victoire.</p>
            <p><b>Course à la commune</b> : quand un joueur prend une commune, les sièges des autres attaquants sur cette commune sont effacés. Ils repartent de zéro contre le nouveau propriétaire, et la cloche les prévient.</p><!-- patch326 -->""", 1),
    ("""              <li><b>3 victoires</b> et la commune est à toi, pas forcément d'affilée. <b>Une défaite ne te fait rien perdre.</b></li>""",
     """              <li><b>3 victoires</b> et la commune est à toi, pas forcément d'affilée. <b>Une défaite ne te fait rien perdre.</b></li>
              <li>Si un autre joueur prend la commune avant toi, <b>ta série est effacée</b>.</li><!-- patch326 -->""", 1),
])
print('patch326 appliqué')
