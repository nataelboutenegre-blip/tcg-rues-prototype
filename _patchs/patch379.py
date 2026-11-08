# patch379 (8/11/2026) : un volet « Bâtiments » dans Combat (idée de Maroli et ASMFCB
# sur Discord, 8/11 : « il y a trop de trucs dans l'onglet Défendre »).
#   - Combat : Mon front | Attaquer | Défendre | Bâtiments ;
#   - le bloc des bâtiments (lingots, Fonderies, Forteresses, Centre et bombe, Radar,
#     Banque) quitte Défendre pour ce volet ; Défendre garde les communes attaquées,
#     Libérer, les rébellions, les garnisons et les défenses ;
#   - en haut du volet : la galerie (« Mes bâtiments » et « Les autres ») ;
#   - « Mes bâtiments » dans Mon front, la cloche (Déplacer, Déménager) et les liens
#     « Fonderie » mènent au volet ; les textes « Défendre › Bâtiments » suivent.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:80]!r}'
    return s.replace(avant, apres)

# ---------- index.html ----------
H = pathlib.Path('index.html'); h = H.read_text(encoding='utf-8')
assert 'patch379' not in h
h = rep(h, """        Défense
      </div>""", """        Défense
      </div>

      <div class="tab onglet-fusionne" data-tab="batiments" aria-hidden="true"><!-- patch379 -->
        <div class="icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round">
            <path d="M4 20V10l5-3v13M9 20V5l7-2v17M16 20V9l4 2v9M3 20h18"/>
          </svg>
        </div>
        Bâtiments
      </div>""")
VD = """<button type="button" class="volet" data-volet="defense" role="tab" aria-selected="false">Défendre<span class="volet-badge" data-badge-defense hidden></span></button>"""
h = rep(h, VD, VD + """
        <button type="button" class="volet" data-volet="batiments" role="tab" aria-selected="false">Bâtiments</button><!-- patch379 -->""")
VA = """<button type="button" class="volet actif" data-volet="defense" role="tab" aria-selected="true">Défendre<span class="volet-badge" data-badge-defense hidden></span></button>"""
h = rep(h, VA, VA + """
        <button type="button" class="volet" data-volet="batiments" role="tab" aria-selected="false">Bâtiments</button><!-- patch379 -->""")
h = rep(h, """    <section class="tab-panel" id="panel-defense">""", """    <section class="tab-panel" id="panel-batiments"><!-- patch379 : idée de Maroli et ASMFCB -->
      <h1>Combat</h1>
      <div class="volets" role="tablist" aria-label="Combat">
        <button type="button" class="volet" data-volet="monfront" role="tab" aria-selected="false">Mon front</button>
        <button type="button" class="volet" data-volet="combat" role="tab" aria-selected="false">Attaquer</button>
        <button type="button" class="volet" data-volet="defense" role="tab" aria-selected="false">Défendre<span class="volet-badge" data-badge-defense hidden></span></button>
        <button type="button" class="volet actif" data-volet="batiments" role="tab" aria-selected="true">Bâtiments</button>
      </div>
      <div class="sub">Tes lingots et tes bâtiments. Pour construire, touche une de tes communes sur la carte ; ici, tu les gères, tu les déplaces, et tu prépares ta bombe.</div>
      <div class="btv-galerie"><button type="button" class="filter-pill" data-btv="miens">Mes bâtiments en images ›</button><button type="button" class="filter-pill" data-btv="autres">Les bâtiments des autres ›</button></div>
    </section>

    <section class="tab-panel" id="panel-defense">""")
h = rep(h, "(Défendre › Bâtiments, ou la fiche de la commune) : 6 h de chantier sans effet",
           "(Combat › Bâtiments, ou la fiche de la commune) : 6 h de chantier sans effet")
h = rep(h, "Pour les dépenser, retire-les (Défendre › Bâtiments).", "Pour les dépenser, retire-les (Combat › Bâtiments).")
h = rep(h, "(Défendre › Bâtiments, ou la fiche de la commune) : son contenu la suit",
           "(Combat › Bâtiments, ou la fiche de la commune) : son contenu la suit")
h = rep(h, "Tu peux <b>déménager ton centre</b> sur une autre de tes communes (Défendre › Bâtiments)",
           "Tu peux <b>déménager ton centre</b> sur une autre de tes communes (Combat › Bâtiments)")
h = rep(h, "ils apparaissent sur ta carte et dans Défendre, et leur propriétaire est prévenu.",
           "ils apparaissent sur ta carte et dans Combat › Bâtiments, et leur propriétaire est prévenu.")
H.write_text(h, encoding='utf-8')

# ---------- app.js ----------
F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch379' not in s
s = rep(s, "const ONGLETS_FUSIONNES = ['defense', ", "const ONGLETS_FUSIONNES = ['defense', 'batiments', ")   # patch379
s = rep(s, "const ONGLET_PARENT = { defense: 'combat', ", "const ONGLET_PARENT = { defense: 'combat', batiments: 'combat', ")
s = rep(s, "const ONGLETS_CONNUS = ['tirage', 'collection', 'territoire', 'bourse', 'combat', 'defense', ",
           "const ONGLETS_CONNUS = ['tirage', 'collection', 'territoire', 'bourse', 'combat', 'defense', 'batiments', ")
# le bloc va dans le nouveau volet ; les rébellions et « Libérer » restent dans Défendre
s = rep(s, """    bt.hidden = true;
    g.insertAdjacentElement('beforebegin', bt);
    // lot 8/11 : les rébellions qui couvent dans mes villes
    const rbb = document.createElement('div');
    rbb.id = 'rebellionsBloc';
    rbb.className = 'garnisons-bloc rebellions-bloc';
    bt.insertAdjacentElement('beforebegin', rbb);""",
"""    bt.hidden = true;
    const pBat = document.getElementById('panel-batiments');   // patch379 : son propre volet
    if(pBat) pBat.appendChild(bt); else g.insertAdjacentElement('beforebegin', bt);
    // lot 8/11 : les rébellions qui couvent dans mes villes
    const rbb = document.createElement('div');
    rbb.id = 'rebellionsBloc';
    rbb.className = 'garnisons-bloc rebellions-bloc';
    g.insertAdjacentElement('beforebegin', rbb);""")
s = rep(s, "    const g = document.getElementById('batimentsBloc') || document.getElementById('garnisonsBloc') || defense.querySelector('.bourse-section');",
           "    const g = document.getElementById('rebellionsBloc') || document.getElementById('garnisonsBloc') || defense.querySelector('.bourse-section');   // patch379 : les bâtiments ont leur volet")
s = rep(s, "  el.innerHTML = `<h2>Bâtiments</h2>${alertesBombesHtml()}",
           "  el.innerHTML = `${document.getElementById('panel-batiments') ? '' : '<h2>Bâtiments</h2>'}${alertesBombesHtml()}")
s = rep(s, """    if(tab.dataset.tab === 'defense'){ loadMenaces().then(loadReveil); loadCombat(); renderIntensite('defense'); if(SAISON2) chargerGarnisons(); }""",
"""    if(tab.dataset.tab === 'defense'){ loadMenaces().then(loadReveil); loadCombat(); renderIntensite('defense'); if(SAISON2) chargerGarnisons(); }
    if(tab.dataset.tab === 'batiments' && SAISON2){ chargerBatiments(); window.scrollTo({ top: 0 }); }   // patch379""")
# la galerie depuis le volet
s = rep(s, """// ouvrir un autre écran depuis Mon front
function mfoVers(quoi, tier){""",
"""// patch379 : la galerie depuis le volet Bâtiments
document.getElementById('panel-batiments')?.addEventListener('click', (e) => {
  const b = e.target.closest('[data-btv]');
  if(b) btEcranOuvrir(b.dataset.btv);
});
// ouvrir un autre écran depuis Mon front
function mfoVers(quoi, tier){""")
s = rep(s, "  if(quoi === 'batiments') return btEcranOuvrir('miens');   // patch366",
           "  if(quoi === 'batiments') return tab('batiments');   // patch379 : le volet (la galerie est en haut)")
# la cloche et les liens « Fonderie »
s = rep(s, "        a: 'Déplacer', aller: () => ncAller('front', 'defense') });", "        a: 'Déplacer', aller: () => ncAller('front', 'batiments') });")
s = rep(s, "        a: 'Déménager', aller: () => ncAller('front', 'defense') });", "        a: 'Déménager', aller: () => ncAller('front', 'batiments') });")
s = rep(s, "  if(quoi === 'fonderie'){ ncAller('front', 'defense'); return; }", "  if(quoi === 'fonderie'){ ncAller('front', 'batiments'); return; }   // patch379")
s = rep(s, "  if(a === 'fonderie'){ pcFermer(); ncAller('front', 'defense'); return; }", "  if(a === 'fonderie'){ pcFermer(); ncAller('front', 'batiments'); return; }   // patch379")
# les textes
s = rep(s, "Ton épargne : dépose des lingots dans Défendre, ils rapportent", "Ton épargne : dépose des lingots dans Combat › Bâtiments, ils rapportent")
s = rep(s, "lingots : Défendre › Bâtiments, ou « Déplacer une forteresse ici »", "lingots : Combat › Bâtiments, ou « Déplacer une forteresse ici »")
s = rep(s, "il est détruit. Le détail est dans Défendre.</p>", "il est détruit. Le détail est dans Combat › Bâtiments.</p>")
s = rep(s, ". Tout se gère dans Défendre.</p>", ". Tout se gère dans Combat › Bâtiments.</p>")
F.write_text(s, encoding='utf-8')

C = pathlib.Path('style.css'); c = C.read_text(encoding='utf-8')
assert 'patch379' not in c
c += """
/* patch379 : le volet Bâtiments */
.btv-galerie{ display:flex; flex-wrap:wrap; gap:8px; margin:4px 0 14px; }
#panel-batiments .batiments-bloc{ margin-top:0; }
#panel-batiments .volet{ white-space:nowrap; }
@media (max-width: 720px){
  #panel-combat .volet, #panel-defense .volet, #panel-batiments .volet{ padding-left:8px; padding-right:8px; }
}
@media (max-width: 380px){
  #panel-combat .volet, #panel-defense .volet, #panel-batiments .volet{ padding-left:5px; padding-right:5px; font-size:.86rem; }
}
"""
C.write_text(c, encoding='utf-8')
print('patch379 ok')
