# patch492 : le motif de territoire (demande de Nataël, 21-22/11). Va avec _sql/s3-46-motifs.sql.
# - Boutique › Atelier › Mon territoire : « Mon motif », avec l'éditeur (8 calques, 64 formes, 3 lettres au plus,
#   modèles, hasard, aperçu sur une carte d'exemple). Le fond du motif, c'est la couleur du joueur.
# - Sur la carte : le motif de chaque joueur se pose sur sa couleur, de près seulement (il s'efface de loin).
#   Nouveau calque « Motifs » pour les cacher. Pas en couleurs de rareté ni en Clans « Plein ».
# - 4 packs de formes à 1,99 € (articles « motifs-… ») : on essaie tout, on paie pour enregistrer.
# - La fiche d'un joueur montre son motif et permet de le signaler ; la modération (Nataël) retire ou classe
#   depuis Boutique › Atelier › Mon territoire.
# S'éteint côté serveur : config_jeu 'interface'.motifs = 0. Sans s3-46, rien ne change (l'ancien « Bientôt ici » reste).
import os, sys, shutil
R = sys.argv[1] if len(sys.argv) > 1 else '.'
ICI = os.path.dirname(os.path.abspath(__file__))
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A = 'app.js'
# 1. l'état, déclaré tôt
rep(A, "const COULEURS_CHOISIES = new Map();\n",
       "const COULEURS_CHOISIES = new Map();\n"
       "// patch492 : le motif de territoire de chaque joueur (posé sur sa couleur)\n"
       "const MOTIFS = new Map();\n"
       "const MTF = { ouvert: null, lu: false, lecture: null, formes: null, formesP: null, FORME: {}, moi: null, packs: [], bloque: null, modo: false, signalements: 0, signales: [], pats: new Map() };\n")
# 2. chargement, avec les couleurs
rep(A, "  await chargerCouleursTerritoire();   // patch158\n",
       "  await chargerCouleursTerritoire();   // patch158\n  motifsCharger();   // patch492\n")
# 3. la carte : le motif par-dessus la couleur
rep(A, "        ctx.fillStyle = j.couleur; ctx.fill(p);\n        const bord = bordsTerritoires(deps, possedees).get(id);   // patch335 : le tour, à l'intérieur",
       "        ctx.fillStyle = j.couleur; ctx.fill(p);\n        if(!(j.clan && clanPlein())) motPeindre(ctx, id, p, k);   // patch492\n        const bord = bordsTerritoires(deps, possedees).get(id);   // patch335 : le tour, à l'intérieur")
# 4. le calque « Motifs »
rep(A, "raretes: true, passage: false, clans: false, batiments: true, couleur: 'joueurs', clanVue: 'contour' };",
       "raretes: true, passage: false, clans: false, batiments: true, motifs: true, couleur: 'joueurs', clanVue: 'contour' };")
rep(A, "    ordre.splice(ordre.indexOf('raretes') + 1, 0, 'batiments');\n  }\n",
       "    ordre.splice(ordre.indexOf('raretes') + 1, 0, 'batiments');\n  }\n"
       "  if(MOTIFS.size){   // patch492\n"
       "    NOMS.motifs = 'Motifs';\n"
       "    ICONES.motifs = '<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linejoin=\"round\"><path d=\"M4 4h16v16H4z\"/><path d=\"m8 6.2.9 1.9 2.1.3-1.5 1.5.4 2.1L8 11l-1.9 1 .4-2.1L5 8.4l2.1-.3zM16 12.2l.9 1.9 2.1.3-1.5 1.5.4 2.1-1.9-1-1.9 1 .4-2.1-1.5-1.5 2.1-.3z\"/></svg>';\n"
       "    ordre.push('motifs');\n"
       "  }\n")
# 5. Boutique › Atelier › Mon territoire
rep(A, """    corps.innerHTML = `<div class="atb-bloc atb-terr">${blocCouleur()}
      <p class="atb-note">Bientôt ici : <b>ton motif de territoire</b>, à composer toi-même (formes, lignes, symboles, couleurs).</p></div>`;
    return;""",
       """    corps.innerHTML = `<div class="atb-bloc atb-terr">${blocCouleur()}</div>${motBlocAtelier()}`;   // patch492
    motApresRendu(corps);
    return;""")
rep(A, """document.getElementById('panel-atelierbq').addEventListener('click', async (e) => {
  const vue = e.target.closest('[data-atb-vue]');
  if(vue){ atbVue = vue.dataset.atbVue; atbRendre(); return; }""",
       """document.getElementById('panel-atelierbq').addEventListener('click', async (e) => {
  const vue = e.target.closest('[data-atb-vue]');
  if(vue){ atbVue = vue.dataset.atbVue; atbRendre(); return; }
  if(e.target.closest('[data-mot], [data-mot-modo]')){ await motClicAtelier(e); return; }   // patch492""")
# 6. la fiche d'un joueur
rep(A, """        <h3>Territoire</h3>
        <div class="pr-puces">${puces}</div>
""", """        <h3>Territoire</h3>
        <div class="pr-puces">${puces}</div>
        ${motProfilHtml(p)}
""")
rep(A, """amisEtat.get(p.id) === 'bloque' ? 'Débloquer ce joueur' : 'Bloquer ce joueur'}</button>`}
      </div>
    </div>`, () => { profilEnCours = null; fermerProfil = null; });
}""", """amisEtat.get(p.id) === 'bloque' ? 'Débloquer ce joueur' : 'Bloquer ce joueur'}</button>`}
        ${motProfilSignalerHtml(p)}
      </div>
    </div>`, () => { profilEnCours = null; fermerProfil = null; });
  motProfilApres();   // patch492
}""")
# 7. la boutique : les packs de formes
rep(A, "  if(a.type === 'effet') return atlGrandApercu(a);   // patch270\n  if(a.type === 'collection'){\n    const d = c.find",
       "  if(a.type === 'effet') return atlGrandApercu(a);   // patch270\n  if(a.type === 'motif') return motApercuPack(a);   // patch492\n  if(a.type === 'collection'){\n    const d = c.find")
rep(A, "    : a.type === 'effet' ? atlQuoiAchat(a, nom)   // patch270\n",
       "    : a.type === 'effet' ? atlQuoiAchat(a, nom)   // patch270\n    : a.type === 'motif' ? `<b>le pack ${echapperTexte(nom)}</b> pour ton motif de territoire`   // patch492\n")
rep(A, "pass: 'Pass de saison', effet: atlLibelleArticle(a.id) }[a.type]", "pass: 'Pass de saison', motif: 'Motif de territoire', effet: atlLibelleArticle(a.id) }[a.type]")
rep(A, "a.type === 'effet' ? 'C\\'est déjà à toi, dans l\\'atelier (Profil › Personnaliser).'",
       "a.type === 'motif' ? 'C\\'est déjà à toi, dans Boutique › Atelier › Mon territoire.' : a.type === 'effet' ? 'C\\'est déjà à toi, dans l\\'atelier (Profil › Personnaliser).'")
rep(A, "texte: 'Rien n\\'a été débité.' }); if(retour === 'atelier') atlOuvrirQuandPret(); return; }",
       "texte: 'Rien n\\'a été débité.' }); if(retour === 'atelier') atlOuvrirQuandPret(); if(retour === 'motif') motRetourAchat(); return; }")
rep(A, "  if(retour === 'atelier') atlOuvrirQuandPret();   // patch270\n}",
       "  if(retour === 'atelier') atlOuvrirQuandPret();   // patch270\n  if(retour === 'motif') motRetourAchat();   // patch492\n}")
# 8. le bloc : dessin, éditeur
bloc = open(os.path.join(ICI, 'patch492-bloc.js'), encoding='utf-8').read()
rep(A, "// ---------- patch486 : l'onglet Atelier de la boutique ----------\n",
       bloc.rstrip('\n') + "\n\n// ---------- patch486 : l'onglet Atelier de la boutique ----------\n")
# 9. le style
p = os.path.join(R, 'style.css'); t = open(p, encoding='utf-8').read()
css = open(os.path.join(ICI, 'patch492-style.css'), encoding='utf-8').read()
if css.split('\n')[0] in t: print('style.css : déjà fait')
else: open(p, 'w', encoding='utf-8').write(t.rstrip('\n') + '\n\n' + css); print('style.css : ok')
# 10. les données : les 64 formes, la carte d'exemple de l'éditeur
for src, dst in (('patch492-formes.json', 'motifs-formes.json'), ('patch492-apercu.json', 'motifs-apercu.json')):
    shutil.copyfile(os.path.join(ICI, src), os.path.join(R, dst)); print(dst, ': ok')
