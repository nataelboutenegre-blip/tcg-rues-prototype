# patch305 : annuler un bâtiment en construction (s2-73), construction en 6 h
# - Fiche d'une commune : « Annuler la construction · N lingots rendus », en deux temps
#   (comme Construire). Grisé pendant un assaut sur la commune (le serveur refuse aussi).
# - Défendre › Bâtiments : sur chaque chantier, le temps restant et ce qui est rendu, avec
#   une pastille « Annuler » (deux temps). Le Centre en construction a son bouton.
# - Remboursement : Forteresse et Centre à leur prix, 2e Fonderie à son prix, 1re Fonderie
#   gratuite (rien à rendre). Le serveur (batiment_annuler) fait foi.
# - Règles : 6 h au lieu de 24 h (la durée affichée ailleurs vient déjà de construction_h).
import json, pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

# ---------------------------------------------------------------- app.js
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch305' not in s

s = s.replace("btReglage('construction_h', 24)", "btReglage('construction_h', 6)")

# outils : ce qui est rendu, assaut en cours, le bouton
s = rep(s, """const btReglage = (cle, defaut) => (BATIMENTS && BATIMENTS.reglages && BATIMENTS.reglages[cle] != null) ? BATIMENTS.reglages[cle] : defaut;
""",
"""const btReglage = (cle, defaut) => (BATIMENTS && BATIMENTS.reglages && BATIMENTS.reglages[cle] != null) ? BATIMENTS.reglages[cle] : defaut;
// patch305 : annuler un bâtiment en construction (s2-73), ses lingots sont rendus en entier
function btRembourse(type, code){
  if(type === 'forteresse') return Number(btReglage('forteresse_prix', 20)) || 0;
  if(type === 'centre') return Number(btReglage('centre_prix', 40)) || 0;
  if(type === 'fonderie') return mesFonderies().findIndex(x => x.code === code) > 0 ? Number(btReglage('fonderie2_prix', 30)) || 0 : 0;   // la 1re est gratuite
  return 0;
}
const btSousAssaut = (code) => typeof serieMienne === 'function' && serieMienne(code) > 0;
const btNom = (type) => type === 'fonderie' ? 'Fonderie' : type === 'centre' ? 'Centre de recherche' : 'Forteresse';
function btAnnulerHtml(code, type){
  if(btSousAssaut(code)) return '<button type="button" class="bt-annuler" disabled>Annulation impossible pendant l’assaut</button>';
  const r = btRembourse(type, code), a = btArme === code + '|annuler-' + type, le = type === 'centre' ? 'le' : 'la';
  const attrs = `data-pc="bt-annuler" data-bt="${type}" data-bt-annuler="${echapperTexte(code)}" data-bt-type="${type}"`;
  return `<button type="button" class="bt-annuler${a ? ' arme' : ''}" ${attrs}>${a
      ? (r ? `Confirmer : annuler et récupérer ${r} ${ICONE_LINGOT}` : 'Confirmer : annuler la construction')
      : `Annuler la construction${r ? ` · ${r} ${ICONE_LINGOT} rendus` : ''}`}</button>`
    + (a ? `<p class="bt-annuler-note">Pour ${le} mettre ailleurs : annule, puis construis-${le} sur une autre commune (${btReglage('construction_h', 6)} h).</p>` : '');
}
async function batimentAnnuler(code, type){
  const nom = btNom(type);
  const { data, error } = await sb.rpc('batiment_annuler', { p_code: code, p_type: type });
  if(error) notifier({ type: 'erreur', titre: nom, texte: messageLisible(error.message) });
  else {
    const r = Number(data && data.rembourse) || 0;
    notifier({ type: 'succes', titre: `${nom} annulé${type === 'centre' ? '' : 'e'}`, texte: r ? `${r} lingots rendus.` : 'Tu peux la construire ailleurs.' });
  }
  await chargerBatiments();
  if(panneauCommune === code && collectionMap.get(code)){ const a = panneauAncre; ouvrirPanneau(code, a ? a.x : 40, a ? a.y : 40); }
}
""")

# fiche : le bouton sous chaque bâtiment en construction
s = rep(s, """        Visible de tous : si on te prend ${echapperHtml(c.nom)}, la Fonderie est détruite et l’attaquant pille ${Math.round(btReglage('pillage', 50) / Math.max(1, mesFonderies().length))} % de ta réserve.</p>
    </div>`;""",
"""        Visible de tous : si on te prend ${echapperHtml(c.nom)}, la Fonderie est détruite et l’attaquant pille ${Math.round(btReglage('pillage', 50) / Math.max(1, mesFonderies().length))} % de ta réserve.</p>
      ${prete ? '' : btAnnulerHtml(code, 'fonderie')}
    </div>`;""")
s = rep(s, """      <p class="bt-txt"><b>−${btReglage('forteresse_defense', 15)} %</b> aux chances des attaquants ici, et <b>+${btReglage('forteresse_appui', 5)} %</b> à tes attaques à moins de ${btReglage('rayon_km', 20)} km.</p>
    </div>`;""",
"""      <p class="bt-txt"><b>−${btReglage('forteresse_defense', 15)} %</b> aux chances des attaquants ici, et <b>+${btReglage('forteresse_appui', 5)} %</b> à tes attaques à moins de ${btReglage('rayon_km', 20)} km.</p>
      ${prete ? '' : btAnnulerHtml(code, 'forteresse')}
    </div>`;""")
s = rep(s, """Si on te prend ${echapperHtml(c.nom)}, il est détruit${P ? ' et ta bombe est perdue' : ''}. Tout se gère dans Défendre.</p>
    </div>`;""",
"""Si on te prend ${echapperHtml(c.nom)}, il est détruit${P ? ' et ta bombe est perdue' : ''}. Tout se gère dans Défendre.</p>
      ${pret ? '' : btAnnulerHtml(code, 'centre')}
    </div>`;""")

# fiche : le clic, en deux temps
s = rep(s, """  if(quoi === 'bt-construire'){   // patch243""",
"""  if(quoi === 'bt-annuler'){   // patch305 : deux temps aussi
    const t = b.dataset.bt;
    if(btArme !== code + '|annuler-' + t){ btArme = code + '|annuler-' + t; const a = panneauAncre; ouvrirPanneau(code, a ? a.x : 40, a ? a.y : 40); return; }
    btArme = null;
    b.disabled = true;
    batimentAnnuler(code, t);
    return;
  }
  if(quoi === 'bt-construire'){   // patch243""")

# Défendre : la pastille Annuler sur les chantiers
s = rep(s, """  const ligne = (ic, b, sous) => `<div class="btl"><span class="btl-ic">${ic}</span>
      <span class="btl-t"><button type="button" class="btl-nom" data-voir-carte="${echapperTexte(b.code)}">${echapperTexte(b.nom)} (${echapperTexte(b.dept)})</button><small>${sous}</small></span>${etat(b)}</div>`;""",
"""  const ligne = (ic, b, sous, type) => {   // patch305 : un chantier se montre avec son temps restant et Annuler
    let fin = etat(b);
    if(type && btPretDans(b) > 0){
      const r = btRembourse(type, b.code), a = btArme === b.code + '|annuler-' + type;
      sous = `Prête dans ${formatDuree(btPretDans(b))} · ${btSousAssaut(b.code) ? 'assaut en cours : pas d’annulation' : r ? `${r} lingots rendus si tu annules` : 'gratuite, rien à rendre'}`;
      fin = btSousAssaut(b.code) ? etat(b)
        : `<button type="button" class="gl-r bt-ann${a ? ' arme' : ''}" data-bt-annuler="${echapperTexte(b.code)}" data-bt-type="${type}">${a ? 'Confirmer ?' : 'Annuler'}</button>`;
    }
    return `<div class="btl"><span class="btl-ic">${ic}</span>
      <span class="btl-t"><button type="button" class="btl-nom" data-voir-carte="${echapperTexte(b.code)}">${echapperTexte(b.nom)} (${echapperTexte(b.dept)})</button><small>${sous}</small></span>${fin}</div>`;
  };""")
s = rep(s, """mesFonderies().map(x => ligne(ICONE_FONDERIE, x, btPretDans(x) <= 0 ? `Produit ${B.production} lingots par jour` : 'En construction'))""",
           """mesFonderies().map(x => ligne(ICONE_FONDERIE, x, btPretDans(x) <= 0 ? `Produit ${B.production} lingots par jour` : 'En construction', 'fonderie'))""")
s = rep(s, """forts.map(x => ligne(ICONE_FORTERESSE, x, btPretDans(x) <= 0 ? `−${btReglage('forteresse_defense', 15)} % aux attaquants · +${btReglage('forteresse_appui', 5)} % autour` : 'En construction'))""",
           """forts.map(x => ligne(ICONE_FORTERESSE, x, btPretDans(x) <= 0 ? `−${btReglage('forteresse_defense', 15)} % aux attaquants · +${btReglage('forteresse_appui', 5)} % autour` : 'En construction', 'forteresse'))""")
s = rep(s, """    corps = `<div class="cr">${tete('En construction : prêt dans ' + formatDuree(btPretDans(ce)), badge)}</div>`;""",
           """    corps = `<div class="cr">${tete('En construction : prêt dans ' + formatDuree(btPretDans(ce)), badge)}${btAnnulerHtml(ce.code, 'centre')}</div>`;   // patch305""")
s = rep(s, """    bt.addEventListener('click', (e) => {
      const pr = e.target.closest('[data-bt-prep]');""",
"""    bt.addEventListener('click', (e) => {
      const an = e.target.closest('[data-bt-annuler]');   // patch305 : annuler un chantier, en deux temps
      if(an){
        const k = an.dataset.btAnnuler + '|annuler-' + an.dataset.btType;
        if(btArme !== k){ btArme = k; renderBatimentsBloc(); return; }
        btArme = null; an.disabled = true; batimentAnnuler(an.dataset.btAnnuler, an.dataset.btType); return;
      }
      const pr = e.target.closest('[data-bt-prep]');""")
f.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------- style.css
f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch305' not in s
s = s.rstrip('\n') + """

/* patch305 : annuler un bâtiment en construction */
.bt-annuler{ display:flex; align-items:center; justify-content:center; gap:6px; width:100%; margin-top:9px; padding:8px 10px; border-radius:9px;
  font:inherit; font-size:.78rem; font-weight:600; color:#FFD9B8; background:rgba(10,22,40,.35); border:1px dashed rgba(232,131,58,.55); cursor:pointer; }
.bt-annuler .lingot{ width:13px; height:8px; }
.bt-annuler.arme{ color:#fff; background:rgba(229,72,77,.22); border:1px solid rgba(229,72,77,.7); }
.bt-annuler:disabled{ opacity:.5; cursor:default; }
.bt-annuler-note{ font-size:.7rem; color:#B9A08C; margin:5px 0 0; text-align:center; }
.btl .gl-r.bt-ann{ padding:6px 10px; font-size:.74rem; border-color:rgba(232,131,58,.55); background:rgba(232,131,58,.14); }
.btl .gl-r.bt-ann.arme{ background:rgba(229,72,77,.3); border-color:rgba(229,72,77,.8); }
"""
f.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------- index.html (règles)
f = pathlib.Path('index.html'); s = f.read_text(encoding='utf-8')
assert 'patch305' not in s
s = rep(s, "Un bâtiment met 24 h à se construire, se voit sur la carte",
           "Un bâtiment met <b>6 h</b> à se construire (on peut l'annuler pendant ce temps : ses lingots sont rendus, sauf pendant un assaut sur sa commune)<!-- patch305 -->, se voit sur la carte")
f.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------- nouveautés
f = pathlib.Path('data/nouveautes.json'); d = json.loads(f.read_text(encoding='utf-8'))
e = next((x for x in d if x['date'] == '2026-11-02'), None)
if e is None:
    e = {'date': '2026-11-02', 'nouveautes': [], 'correctifs': []}
    d.insert(0, e)
e['nouveautes'].insert(0, '🏗 Bâtiments : 6 h de construction au lieu de 24 h, et tu peux annuler un bâtiment en construction (ses lingots te sont rendus en entier)')
f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('patch305 appliqué')
