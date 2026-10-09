# -*- coding: utf-8 -*-
u"""
patch88 — La rarete « Epique » cote jeu (saison 2, socle)
(apercu « epique.png », couleur A Amethyste, validee le 9 octobre).

SANS EFFET VISIBLE EN SAISON 1 : aucune commune n'est epique avant la
bascule. Le jeu apprend seulement a dessiner et a ranger une epique :
- liste des raretes (entre legendaire et rare), couleurs, dessins des cartes ;
- tables par rarete alignees sur s2-1-socle.sql : rachat 300, delai 1 h,
  attaque 30, commission 60 ;
- rang dans l'ouverture de paquet (sort juste avant la legendaire), lueur et
  lumiere violettes, son propre ;
- carte du Territoire : pastille comme les rares ;
- liste des cibles du Combat : les epiques y entrent comme les rares ;
- regles : le calcul des tranches de population saute un palier absent
  (sinon, sans epique en base, la rare afficherait « 5 000 et plus »).

EPIQUE_VISIBLE = false cache la ligne Epique des statistiques de tirage et
le filtre Epique de la Collection tant que la saison 2 n'est pas lancee
(le filtre apparait quand meme si le joueur possede une epique).

Volontairement pas touche : boucliers (refaits en energie pour le Front),
contrats (Terra), page d'accueil.
"""
import io, os

ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI

def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f:
        return f.read()

def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f:
        f.write(s)

def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)

def apres(src, ancre, ajout, etiquette):
    return rempl(src, ancre, ancre + ajout, etiquette)

js = lire('app.js')
assert "'epique'" not in js, u'patch88 deja applique'

# --- la liste des raretes et ses dessins -----------------------------------
js = apres(js, u"  {id:'legendaire', label:'Légendaire', color:'#B0862C'},\n",
           u"  {id:'epique', label:'Épique', color:'#7A3FD1'},\n", 'TIERS')
js = apres(js, u"  {id:'commun', label:'Commun', color:'#7C8798'},\n];\n",
           u"// patch88 : la ligne Epique des statistiques et le filtre de la Collection\n"
           u"// restent caches jusqu'au lancement de la saison 2\n"
           u"const EPIQUE_VISIBLE = false;\n", 'EPIQUE_VISIBLE')
js = apres(js, u"  rare:       ['#4E92FF', '#1D4FB8'],\n",
           u"  epique:     ['#B58BFF', '#5B2BB5'],\n", 'TEINTES_CARTE')

# --- compteurs de la session de tirage ------------------------------------
js = rempl(js, u"let session = {commun:0, peucommun:0, rare:0, legendaire:0, total:0};",
           u"let session = {commun:0, peucommun:0, rare:0, epique:0, legendaire:0, total:0};", 'session 1')
js = rempl(js, u"\n  session = {commun:0, peucommun:0, rare:0, legendaire:0, total:0};",
           u"\n  session = {commun:0, peucommun:0, rare:0, epique:0, legendaire:0, total:0};", 'session 2')
js = rempl(js, u"  for(const t of TIERS){\n    const n = session[t.id];",
           u"  for(const t of TIERS){\n    if(t.id === 'epique' && !EPIQUE_VISIBLE && !session.epique) continue;\n    const n = session[t.id];",
           'renderStats')

# --- carte du Territoire ----------------------------------------------------
js = rempl(js, u"const RAYON_ZONE = {commun: 4.5, peucommun: 6.5, rare: 10, legendaire: 15};",
           u"const RAYON_ZONE = {commun: 4.5, peucommun: 6.5, rare: 10, epique: 12, legendaire: 15};", 'RAYON_ZONE')
js = rempl(js, u"const ZOOM_MINI = {commun: 2.6, peucommun: 1.8, rare: 1, legendaire: 1};",
           u"const ZOOM_MINI = {commun: 2.6, peucommun: 1.8, rare: 1, epique: 1, legendaire: 1};", 'ZOOM_MINI')
js = rempl(js, u"const LIBELLE_TIER = {commun: 'commun', peucommun: 'peu commun', rare: 'rare', legendaire: 'légendaire'};",
           u"const LIBELLE_TIER = {commun: 'commun', peucommun: 'peu commun', rare: 'rare', epique: 'épique', legendaire: 'légendaire'};",
           'LIBELLE_TIER')
js = rempl(js, u"if(c.tier !== 'legendaire' && (legendairesSeules || c.tier !== 'rare')) continue;",
           u"if(c.tier !== 'legendaire' && (legendairesSeules || (c.tier !== 'rare' && c.tier !== 'epique'))) continue;",
           'marqueurs canvas')
js = rempl(js, u"    } else if(c.tier === 'rare'){\n      g.marqueurs += `<circle cx=\"${cx}\"",
           u"    } else if(c.tier === 'rare' || c.tier === 'epique'){\n      g.marqueurs += `<circle cx=\"${cx}\"",
           'marqueurs svg')
js = rempl(js, u"      } else if(c.tier === 'rare'){\n        g.marqueurs += `<circle cx=\"${x.toFixed(1)}\"",
           u"      } else if(c.tier === 'rare' || c.tier === 'epique'){\n        g.marqueurs += `<circle cx=\"${x.toFixed(1)}\"",
           'marqueurs contours')

# --- assaut, ouverture de paquet --------------------------------------------
js = rempl(js, u"const grand = tierId === 'rare' || tierId === 'legendaire';",
           u"const grand = tierId === 'rare' || tierId === 'epique' || tierId === 'legendaire';", 'assaut grand')
js = rempl(js, u"const RANG_TIER = { commun: 0, peucommun: 1, rare: 2, legendaire: 3 };",
           u"const RANG_TIER = { commun: 0, peucommun: 1, rare: 2, epique: 3, legendaire: 4 };", 'RANG_TIER')
js = rempl(js, u"prochaine.tier.id === 'legendaire' ? 'lueur-leg' : 'lueur-rare'",
           u"prochaine.tier.id === 'legendaire' ? 'lueur-leg' : prochaine.tier.id === 'epique' ? 'lueur-epi' : 'lueur-rare'",
           'lueur pile')
js = rempl(js, u"k = tier === 'legendaire' ? 1 : 0.8;",
           u"k = tier === 'legendaire' ? 1 : tier === 'epique' ? 0.9 : 0.8;", 'son tension')
js = apres(js, u"      else if(tier === 'rare') [523, 659, 784, 1047].forEach((f, i) => note(f, i * 0.07, 0.35, 'triangle', 0.35));\n",
           u"      else if(tier === 'epique') [523, 659, 784, 1047, 1319].forEach((f, i) => note(f, i * 0.07, 0.45, 'triangle', 0.34));\n",
           'son revele')
js = rempl(js, u"lum === 'lum-leg' ? 392 : lum === 'lum-rare' ? 330 : 262",
           u"lum === 'lum-leg' ? 392 : lum === 'lum-epi' ? 360 : lum === 'lum-rare' ? 330 : 262", 'son coupe')
js = rempl(js, u"return ids.includes('legendaire') ? 'lum-leg' : ids.includes('rare') ? 'lum-rare' : '';",
           u"return ids.includes('legendaire') ? 'lum-leg' : ids.includes('epique') ? 'lum-epi' : ids.includes('rare') ? 'lum-rare' : '';",
           'lumierePaquet')
js = rempl(js, u"pack.classList.remove('coupe', 'attente', 'lum-rare', 'lum-leg');",
           u"pack.classList.remove('coupe', 'attente', 'lum-rare', 'lum-epi', 'lum-leg');", 'abandon coupe')

# --- valeurs par rarete (alignees sur s2-1-socle.sql) -----------------------
js = rempl(js, u"const PRIX_RACHAT = {commun: 5, peucommun: 20, rare: 100, legendaire: 1000};",
           u"const PRIX_RACHAT = {commun: 5, peucommun: 20, rare: 100, epique: 300, legendaire: 1000};", 'PRIX_RACHAT')
js = apres(js, u"  rare: 10 * 60 * 1000,\n", u"  epique: 3600 * 1000,\n", 'DELAI_ATTAQUE_MS')
js = rempl(js, u"const COUT_ATTAQUE = { commun: 3, peucommun: 5, rare: 10, legendaire: 100 };",
           u"const COUT_ATTAQUE = { commun: 3, peucommun: 5, rare: 10, epique: 30, legendaire: 100 };", 'COUT_ATTAQUE')
js = rempl(js, u"const COMMISSION_ECHANGE = { commun: 1, peucommun: 4, rare: 20, legendaire: 200 };",
           u"const COMMISSION_ECHANGE = { commun: 1, peucommun: 4, rare: 20, epique: 60, legendaire: 200 };", 'COMMISSION')

# --- couleurs, filtres, regles ----------------------------------------------
js = rempl(js, u"const COULEURS_FILTRE = {legendaire:'#F0B429', rare:'#2F7CF6', peucommun:'#22A06B', commun:'#7E8BA0'};",
           u"const COULEURS_FILTRE = {legendaire:'#F0B429', epique:'#9B5CF6', rare:'#2F7CF6', peucommun:'#22A06B', commun:'#7E8BA0'};",
           'COULEURS_FILTRE')
js = rempl(js, u"    .concat(TIERS.map(t => `<button class=\"coll-filtre ${collectionFilterTier === t.id",
           u"    .concat(TIERS.filter(t => t.id !== 'epique' || EPIQUE_VISIBLE || compte.epique).map(t => `<button class=\"coll-filtre ${collectionFilterTier === t.id",
           'filtres Collection')
js = rempl(js, u"  legendaire: 'var(--c-legendaire)', rare: 'var(--c-rare)',\n",
           u"  legendaire: 'var(--c-legendaire)', epique: 'var(--c-epique)', rare: 'var(--c-rare)',\n", 'COULEUR_TIER')
js = rempl(js, u"""  const ordre = ['commun', 'peucommun', 'rare', 'legendaire'];
  const i = ordre.indexOf(id);
  if(i < 0 || !m[id]) return null;
  const bas = Number(m[id].pop_min);
  const suivant = m[ordre[i + 1]];""",
           u"""  const ordre = ORDRE_PALIERS;
  const i = ordre.indexOf(id);
  if(i < 0 || !m[id]) return null;
  const bas = Number(m[id].pop_min);
  // patch88 : on saute un palier absent de la base (l'epique avant la saison 2)
  const suivant = m[ordre.slice(i + 1).find(t => m[t])];""", 'libellePopulation')
js = rempl(js, u"function libellePopulation(id, m){",
           u"const ORDRE_PALIERS = ['commun', 'peucommun', 'rare', 'epique', 'legendaire'];\nfunction libellePopulation(id, m){",
           'ORDRE_PALIERS')
js = rempl(js, u"  for(const id of ['commun', 'peucommun', 'rare', 'legendaire']){\n    if(!m[id]) continue;",
           u"  for(const id of ORDRE_PALIERS){\n    if(!m[id]) continue;", 'majChiffresPaliers')
js = rempl(js, u"""      const suivant = { commun: 'peucommun', peucommun: 'rare',
                        rare: 'legendaire' }[id];""",
           u"""      const suivant = ORDRE_PALIERS.slice(ORDRE_PALIERS.indexOf(id) + 1).find(t => m[t]);""",
           'seuil accueil')

# --- cibles du Combat ----------------------------------------------------------
js = rempl(js, u".in('communes.tier', ['rare','legendaire'])",
           u".in('communes.tier', ['rare','epique','legendaire'])", 'cibles', n_attendu=2)

ecrire('app.js', js)

# =============================================================================
css = lire('style.css')
assert '--c-epique' not in css, u'patch88 deja applique (css)'

css = apres(css, u"    --rare: #2A5FA8;\n", u"    --epique: #7A3FD1;\n", 'var epique')
css = apres(css, u"    --c-rare: #2F7CF6;\n", u"    --c-epique: #9B5CF6;\n", 'var c-epique')

css = apres(css, u"  .card.rare .carte-cadre{ background: linear-gradient(160deg, #7FB0FF, var(--c-rare) 45%, #1D4FB8); }\n",
            u"  .card.epique .carte-cadre{ background: linear-gradient(160deg, #D6BCFF, var(--c-epique) 45%, #5B2BB5);\n"
            u"    box-shadow: 0 14px 28px rgba(0,0,0,0.45), 0 0 18px rgba(155,92,246,0.28); }\n", 'cadre')
css = apres(css, u"  .card.rare .carte-rarete{ background: var(--c-rare); }\n",
            u"  .card.epique .carte-rarete{ background: var(--c-epique); }\n", 'pastille carte')
css = apres(css, u"  .combat-card.rare .cc-badge{ background: var(--rare); }\n",
            u"  .combat-card.epique{ background: linear-gradient(180deg, var(--paper) 70%, #F3EEFC 100%); }\n"
            u"  .combat-card.epique .cc-badge{ background: var(--epique); }\n", 'combat-card')
css = apres(css, u"  .mini.rare{ background: linear-gradient(160deg, #7FB0FF, var(--c-rare) 45%, #1D4FB8); }\n",
            u"  .mini.epique{ background: linear-gradient(160deg, #D6BCFF, var(--c-epique) 45%, #5B2BB5); }\n", 'mini')
css = apres(css, u"  .mini.rare .mini-rarete{ color:#1D4FB8; }\n",
            u"  .mini.epique .mini-rarete{ color:#5B2BB5; }\n", 'mini rarete')
css = apres(css, u"  .pr-tag.rare{ background:var(--c-rare); }\n",
            u"  .pr-tag.epique{ background:var(--c-epique); }\n", 'pr-tag')
css = apres(css, u"  .conquete.rare{ border-color: var(--c-rare); }\n",
            u"  .conquete.epique{ border-color: var(--c-epique); }\n", 'conquete')
css = apres(css, u"  .conquete.rare .conquete-eclat{ background: radial-gradient(circle, rgba(47,124,246,0.35), transparent 65%); }\n",
            u"  .conquete.epique .conquete-eclat{ background: radial-gradient(circle, rgba(155,92,246,0.38), transparent 65%); }\n",
            'conquete eclat')
css = apres(css, u"  .conquete.rare .conquete-sur{ color:#8DB8FF; }\n",
            u"  .conquete.epique .conquete-sur{ color:#C9A7FF; }\n", 'conquete sur')
css = apres(css, u"  .conquete.rare .conquete-rarete{ background: var(--c-rare); color:#fff; }\n",
            u"  .conquete.epique .conquete-rarete{ background: var(--c-epique); color:#fff; }\n", 'conquete rarete')
css = apres(css, u"  .cible.rare{ background: linear-gradient(160deg, #7FB0FF, var(--c-rare) 45%, #1D4FB8); }\n",
            u"  .cible.epique{ background: linear-gradient(160deg, #D6BCFF, var(--c-epique) 45%, #5B2BB5); }\n", 'cible')
css = apres(css, u"  .cible.rare .cible-rarete{ background: var(--c-rare); }\n",
            u"  .cible.epique .cible-rarete{ background: var(--c-epique); }\n", 'cible rarete')
css = apres(css, u"  .ligne.rare{ border-left-color: var(--c-rare); }\n",
            u"  .ligne.epique{ border-left-color: var(--c-epique); }\n", 'ligne')
css = apres(css, u"  .auth-carte.rare .auth-carte-badge{ background: var(--c-rare); }\n",
            u"  .auth-carte.epique .auth-carte-badge{ background: var(--c-epique); }\n", 'auth')
css = apres(css, u"  #panel-regles .rarete.rare{ background:var(--c-rare); }\n",
            u"  #panel-regles .rarete.epique{ background:var(--c-epique); }\n", 'regles')
css = apres(css, u"  .mini.rare       .art-voile, .fiche.rare       .art-voile{ background:linear-gradient(180deg, rgba(10,22,41,0) 34%, rgba(28,84,178,0.80) 100%); }\n",
            u"  .mini.epique     .art-voile, .fiche.epique     .art-voile{ background:linear-gradient(180deg, rgba(10,22,41,0) 34%, rgba(91,43,181,0.80) 100%); }\n",
            'voile photo')
css = apres(css, u"  .ct-halo.rare{ background: var(--c-rare); }\n",
            u"  .ct-halo.epique{ background: var(--c-epique); }\n", 'halo contrat')
css = apres(css, u"  .jr-commune.rare{ color:#8DB8FF; }\n",
            u"  .jr-commune.epique{ color:#C9A7FF; }\n", 'journal')
css = apres(css, u"  .ech-item.rare{ border-left-color: var(--c-rare); }\n",
            u"  .ech-item.epique{ border-left-color: var(--c-epique); }\n", 'echange')
css = apres(css, u"  .pc-rarete.rare{ background:rgba(47,124,246,.2); color:#6FA5FA; }\n",
            u"  .pc-rarete.epique{ background:rgba(155,92,246,.2); color:#B794FF; }\n", 'bulle carte')
css = apres(css, u".fiche.rare       .fc-ch .fc-rar{ color: #2F7CF6; font-size: 1.05rem; }\n",
            u".fiche.epique     .fc-ch .fc-rar{ color: #9B5CF6; font-size: 1.05rem; }\n", 'fiche')
css = apres(css, u".ouv-dos.lueur-leg .face-back{ box-shadow: 0 0 0 2px var(--c-legendaire), 0 0 34px 8px rgba(240,180,41,.8); }\n",
            u".ouv-dos.lueur-epi .face-back{ box-shadow: 0 0 0 2px var(--c-epique), 0 0 30px 6px rgba(155,92,246,.78); }\n",
            'lueur')
css = rempl(css, u".ouv-dos.lueur-rare .face-back::after, .ouv-dos.lueur-leg .face-back::after{",
            u".ouv-dos.lueur-rare .face-back::after, .ouv-dos.lueur-epi .face-back::after, .ouv-dos.lueur-leg .face-back::after{",
            'lueur calque')
css = apres(css, u".ouv-dos.lueur-leg .face-back::after{ background: radial-gradient(circle at 50% 42%, rgba(255,236,170,.6), rgba(255,236,170,.14) 70%); animation-duration:.8s; }\n",
            u".ouv-dos.lueur-epi .face-back::after{ background: radial-gradient(circle at 50% 42%, rgba(226,208,255,.58), rgba(226,208,255,.14) 70%); animation-duration:.95s; }\n",
            'lueur epique')
css = rempl(css, u".as-carte.rare{ --as-c: var(--c-rare); } .as-carte.legendaire{ --as-c: var(--c-legendaire); }",
            u".as-carte.rare{ --as-c: var(--c-rare); } .as-carte.epique{ --as-c: var(--c-epique); } .as-carte.legendaire{ --as-c: var(--c-legendaire); }",
            'assaut carte')
css = apres(css, u".paquet.lum-rare, .coupe-rayons.lum-rare{ --lum: rgba(90,160,255,.95); }\n",
            u".paquet.lum-epi, .coupe-rayons.lum-epi{ --lum: rgba(185,140,255,.97); }\n", 'lumiere paquet')

ecrire('style.css', css)
print(u'patch88 : OK')
