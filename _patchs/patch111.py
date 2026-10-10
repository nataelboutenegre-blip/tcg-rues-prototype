# -*- coding: utf-8 -*-
u"""
patch111 — les cartes Aurore (saison 2, dès le premier jour).

Une carte Aurore est une carte « full art » : la photo de la commune couvre
toute la carte, un voile d'aurore boréale ondule dessus, un sceau « Aurore »
la signale. Mêmes stats, même rareté : c'est purement visuel.

- Terra : quand un paquet tire une des 233 communes de la liste, 1 chance
  sur 3 qu'elle sorte en Aurore. C'est le SERVEUR qui tire (s2-17) et dit,
  carte par carte, si elle est Aurore. Le jeu l'affiche à la révélation,
  dans le bilan et dans la collection (dès qu'on en possède au moins une).
- Front : les 233 communes s'affichent en Aurore pour qui les possède.
- Les exemplaires Aurore ne se vendent pas et ne s'échangent pas : le jeu
  ne les compte plus comme doublons (le serveur les protège déjà).
- Crédit photo (CC BY / BY-SA) en bas de la grande carte ; dans la grille,
  au survol (comme les photos actuelles, qui n'en ont pas du tout).

Images : aurore/<code>.jpg, crédits : data/aurore.json — produits par
_sql/aurore-telecharger.py. Sans ces fichiers, rien ne casse : la carte
Aurore garde son voile et sa couleur, sur fond dégradé.
Le tout ne s'affiche qu'avec SAISON2 = true.
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

js = lire('app.js')
assert 'fondAurore' not in js, u'patch111 deja applique'

# ---------- la révélation du paquet ----------
js = rempl(js, u"wrap.className = 'card ' + draw.tier.id + (mon ? ' a-monument' : '');",
           u"wrap.className = 'card ' + draw.tier.id + (mon ? ' a-monument' : '') + (draw.aurore ? ' aurore' : '');",
           'classe carte')
js = rempl(js, u"""          <div class="carte-int">
            <div class="carte-haut">""",
u"""          <div class="carte-int">
            ${draw.aurore ? fondAurore(draw.code, draw.tier.id, true) : ''}
            <div class="carte-haut">""", 'fond carte')
js = rempl(js, u"""                <div><span>Rang</span><b>${draw.rank.toLocaleString('fr-FR')}</b></div>
              </div>
            </div>""",
u"""                <div><span>Rang</span><b>${draw.rank.toLocaleString('fr-FR')}</b></div>
              </div>
              ${draw.aurore ? creditAurore(draw.code) : ''}
            </div>""", 'credit carte')

# Front : la commune de la liste s'affiche en Aurore
js = rempl(js, u"lat: row.latitude, lon: row.longitude, tier, rank: row.rang, tierSize: row.palier_total\n    });",
           u"lat: row.latitude, lon: row.longitude, tier, rank: row.rang, tierSize: row.palier_total,\n      aurore: auroreFront(row.code)\n    });",
           'tirage front')
# Terra : c'est le serveur qui dit si la carte est sortie en Aurore
js = rempl(js, u"terraNouvelle: !!row.nouvelle, terraExemplaires: Number(row.exemplaires) || 1,\n  }));\n  terraDernier = draws;",
           u"terraNouvelle: !!row.nouvelle, terraExemplaires: Number(row.exemplaires) || 1,\n    aurore: !!row.aurore,\n  }));\n  terraDernier = draws;\n  prechargerAurore(draws);",
           'tirage terra')

# ---------- la collection Terra ----------
js = rempl(js, u"  if(e) e.exemplaires = draw.terraExemplaires;",
           u"  if(e){ e.exemplaires = draw.terraExemplaires; if(draw.aurore) e.aurore = (e.aurore || 0) + 1; }",
           'retournee maj')
js = rempl(js, u"pop: draw.pop, exemplaires: draw.terraExemplaires, rank: draw.rank, tierSize: draw.tierSize });",
           u"pop: draw.pop, exemplaires: draw.terraExemplaires, rank: draw.rank, tierSize: draw.tierSize,\n    aurore: draw.aurore ? 1 : 0 });",
           'retournee nouvelle')
js = rempl(js, u"""  return `<div class="mini ${e.tier.id}" title="${nom} (${e.dept}) — ${e.tier.label}${e.exemplaires > 1 ? ' — ' + e.exemplaires + ' exemplaires' : ''}">
    <div class="mini-int">""",
u"""  const au = e.aurore > 0;
  return `<div class="mini ${e.tier.id}${au ? ' aurore' : ''}" title="${nom} (${e.dept}) — ${e.tier.label}${au ? ' — Aurore' + (e.aurore > 1 ? ' ×' + e.aurore : '') : ''}${e.exemplaires > 1 ? ' — ' + e.exemplaires + ' exemplaires' : ''}${au ? titreCreditAurore(e.code) : ''}">
    <div class="mini-int">
      ${au ? fondAurore(e.code, e.tier.id, false) : ''}""", 'mini terra')
js = rempl(js, u"miniTerra({ code: d.code, nom: d.nom, dept: d.dept, tier: d.tier, exemplaires: d.terraExemplaires, rank: d.rank, tierSize: d.tierSize })",
           u"miniTerra({ code: d.code, nom: d.nom, dept: d.dept, tier: d.tier, exemplaires: d.terraExemplaires, rank: d.rank, tierSize: d.tierSize, aurore: d.aurore ? 1 : 0 })",
           'bilan')
js = rempl(js, u"exemplaires: Number(r.exemplaires) || 1, rank: r.rang, tierSize: r.palier_total });",
           u"exemplaires: Number(r.exemplaires) || 1, aurore: Number(r.aurore) || 0, rank: r.rang, tierSize: r.palier_total });",
           'chargement collection')

# ---------- les doublons : les exemplaires Aurore sont gardés ----------
js = rempl(js, u".filter(e => e.exemplaires > 1 || myListings.has(e.code))",
           u".filter(e => libresTerra(e) > 0 || myListings.has(e.code))", 'bourse liste')
js = rempl(js, u"    const n = e.exemplaires - 1;\n    const prixAnnonce",
           u"    const n = libresTerra(e);\n    const prixAnnonce", 'bourse ligne')
js = rempl(js, u"    if(e.exemplaires < 2) continue;\n    parTier[e.tier.id] = (parTier[e.tier.id] || 0) + e.exemplaires - 1;",
           u"    if(libresTerra(e) < 1) continue;\n    parTier[e.tier.id] = (parTier[e.tier.id] || 0) + libresTerra(e);", 'doublons')
js = rempl(js, u"(terraFiltre === 'doublons' ? e.exemplaires > 1 : e.tier.id === terraFiltre)",
           u"(terraFiltre === 'doublons' ? libresTerra(e) > 0 : e.tier.id === terraFiltre)", 'filtre doublons')
js = rempl(js, u"if(choix.includes(e.tier.id) && e.exemplaires > 1) e.exemplaires = 1;",
           u"if(choix.includes(e.tier.id) && libresTerra(e) > 0) e.exemplaires = Math.max(1, e.aurore || 0);", 'apres vente')
js = rempl(js, u".filter(c => c.tier.id === echangeTier && c.exemplaires > 1);",
           u".filter(c => c.tier.id === echangeTier && libresTerra(c) > 0);", 'echange filtre')
js = rempl(js, u"libres: c.exemplaires - 1 - (promis[c.code] || 0)",
           u"libres: libresTerra(c) - (promis[c.code] || 0)", 'echange libres')
js = rempl(js, u"On garde toujours un exemplaire de chaque commune.",
           u"On garde toujours un exemplaire de chaque commune, et toutes tes cartes Aurore.", 'texte vente')

# ---------- Front : collection et fiche ----------
js = rempl(js, u"""    <div class="mini ${entry.tier.id}${entry.perdue ? ' perdue' : ''}""",
           u"""    <div class="mini ${entry.tier.id}${auroreFront(entry.code) ? ' aurore' : ''}${entry.perdue ? ' perdue' : ''}""", 'mini front')
js = rempl(js, u"""      <div class="mini-int">
        ${entry.perdue ?""",
u"""      <div class="mini-int">
        ${auroreFront(entry.code) ? fondAurore(entry.code, entry.tier.id, false) : ''}
        ${entry.perdue ?""", 'mini front fond')
js = rempl(js, u"""        <div class="fc-carte">""",
           u"""        <div class="fc-carte${auroreFront(entry.code) ? ' aurore ' + tier.id : ''}">""", 'fiche classe')
js = rempl(js, u"""            <div class="carte-int">
              <div class="carte-haut">
                <span class="carte-rarete">${tier.label}</span>""",
u"""            <div class="carte-int">
              ${auroreFront(entry.code) ? fondAurore(entry.code, tier.id, true) : ''}
              <div class="carte-haut">
                <span class="carte-rarete">${tier.label}</span>""", 'fiche fond')
js = rempl(js, u"        ${creditPhoto(entry)}",
           u"        ${auroreFront(entry.code) ? creditPhoto(photoAurore(entry.code)) : creditPhoto(entry)}", 'fiche credit')

js += u"""

// ---------- patch111 : les cartes Aurore ----------
// La liste qui fait foi pour le tirage est cote serveur (aurore_communes).
// data/aurore.json ne porte que les credits des photos, et sert de liste
// pour l'affichage en Front.
const AURORE_V = '1';
let AURORE = null;   // { code: { a: auteur, l: licence, s: page Commons } }
async function chargerAurore(){
  try{
    const rep = await fetch('data/aurore.json?v=' + AURORE_V);
    AURORE = rep.ok ? ((await rep.json()).cartes || {}) : {};
  } catch(e){ AURORE = {}; }
  // la collection Front a pu s'afficher avant : on la repeint
  const ouvert = document.querySelector('.tab.active[data-tab]');
  if(ouvert && ouvert.dataset.tab === 'collection' && !enTerra() && Object.keys(AURORE).length) renderCollection();
}
if(SAISON2) chargerAurore();
const auroreFront = (code) => SAISON2 && !enTerra() && !!(AURORE && AURORE[code]);
const auroreImage = (code) => AURORE && AURORE[code] ? 'aurore/' + code + '.jpg?v=' + AURORE_V : null;
// les exemplaires qu'on peut vendre ou echanger : jamais le dernier, jamais une Aurore
const libresTerra = (e) => e.exemplaires - Math.max(1, e.aurore || 0);

// le fond de la carte : photo, teinte, voile d'aurore, etoiles, reflet, sceau
function fondAurore(code, tierId, grande){
  const u = auroreImage(code);
  const rnd = aleatoireStable(hashTexte('aurore' + code));
  let etoiles = '';
  for(let i = 0; i < (grande ? 9 : 4); i++){
    etoiles += `<i style="left:${(4 + rnd() * 92).toFixed(1)}%;top:${(3 + rnd() * 45).toFixed(1)}%;animation-delay:${(rnd() * 3).toFixed(2)}s"></i>`;
  }
  return `<div class="au-fond" aria-hidden="true">`
    + (u ? `<img class="au-photo" src="${u}" alt=""${grande ? '' : ' loading="lazy"'} decoding="async" onerror="this.remove()">` : '')
    + `<span class="au-teinte"></span><span class="au-voile"><i></i><i></i><i></i></span>`
    + `<span class="au-etoiles">${etoiles}</span><span class="au-reflet"></span>`
    + `<span class="au-sceau"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.4 7.2H22l-6.2 4.5 2.4 7.3L12 16.5 5.8 21l2.4-7.3L2 9.2h7.6z"/></svg>${grande ? 'Aurore' : ''}</span>`
    + `</div>`;
}
// la grande carte se revele des la fin de la dechirure : l'image doit etre la
function prechargerAurore(draws){
  for(const d of draws){
    const u = d.aurore && auroreImage(d.code);
    if(u){ const img = new Image(); img.src = u; }
  }
}
function photoAurore(code){
  const c = AURORE && AURORE[code];
  return c ? { photo: 1, photoAuteur: c.a, photoLicence: c.l, photoSource: c.s } : null;
}
function creditAurore(code){
  const c = AURORE && AURORE[code];
  return c ? `<p class="au-credit">Photo : ${echapperTexte(c.a)}${c.l ? ' · ' + echapperTexte(c.l) : ''}</p>` : '';
}
function titreCreditAurore(code){
  const c = AURORE && AURORE[code];
  return c ? ' — photo : ' + echapperTexte(c.a) + (c.l ? ', ' + echapperTexte(c.l) : '') : '';
}
"""
ecrire('app.js', js)

css = lire('style.css')
assert 'patch111' not in css, u'patch111 deja applique (css)'
css += u"""
/* ---------- patch111 : cartes Aurore ---------- */
.aurore.commun    { --au-t:#9AA8BC; --au-fond:radial-gradient(120% 90% at 40% 30%, #4A5A73, #121A28 70%); --au-a1:#7FF2D0; --au-a2:#8FB4FF; --au-a3:#C9A6FF; }
.aurore.peucommun { --au-t:var(--c-peucommun); --au-fond:radial-gradient(120% 90% at 40% 30%, #1E7A55, #06231A 70%); --au-a1:#7CFFB2; --au-a2:#3DD6F2; --au-a3:#C4F26B; }
.aurore.rare      { --au-t:var(--c-rare); --au-fond:radial-gradient(120% 90% at 40% 30%, #1D4FB8, #0A1A3D 70%); --au-a1:#3DF2C0; --au-a2:#5B8CFF; --au-a3:#B06CFF; }
.aurore.epique    { --au-t:var(--c-epique); --au-fond:radial-gradient(120% 90% at 40% 30%, #5B2BB5, #160B33 70%); --au-a1:#FF6BD6; --au-a2:#8D6BFF; --au-a3:#3DE0F2; }
.aurore.legendaire{ --au-t:var(--c-legendaire); --au-fond:radial-gradient(120% 90% at 40% 30%, #9A6418, #241505 72%); --au-a1:#FFD86B; --au-a2:#4CF2A6; --au-a3:#FF7AA8; }

.au-fond{ position:absolute; inset:0; z-index:-1; overflow:hidden; background:var(--au-fond); pointer-events:none; border-radius:inherit; }
.au-photo{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; display:block; filter:saturate(1.1) contrast(1.05); }
.au-teinte{ position:absolute; inset:0; mix-blend-mode:soft-light; background:linear-gradient(180deg, var(--au-t), transparent 55%); opacity:.7; }
.au-fond::after{ content:''; position:absolute; left:0; right:0; top:0; height:30%; background:linear-gradient(180deg, rgba(5,10,24,.55), transparent); }
.au-voile{ position:absolute; inset:-30%; mix-blend-mode:screen; filter:blur(22px); opacity:.75; }
.au-voile i{ position:absolute; border-radius:50%; }
.au-voile i:nth-child(1){ width:120%; height:28%; left:-10%; top:22%; background:linear-gradient(90deg, transparent, var(--au-a1), transparent); transform:rotate(-14deg); animation:auOndule1 9s ease-in-out infinite alternate; }
.au-voile i:nth-child(2){ width:110%; height:22%; left:0; top:36%; background:linear-gradient(90deg, transparent, var(--au-a2), transparent); transform:rotate(-8deg); animation:auOndule2 12s ease-in-out infinite alternate; opacity:.8; }
.au-voile i:nth-child(3){ width:90%; height:18%; left:10%; top:14%; background:linear-gradient(90deg, transparent, var(--au-a3), transparent); transform:rotate(-20deg); animation:auOndule3 15s ease-in-out infinite alternate; opacity:.7; }
@keyframes auOndule1{ from{ transform:translate(-8%,0) rotate(-14deg) scaleY(1); } to{ transform:translate(8%,6%) rotate(-6deg) scaleY(1.5); } }
@keyframes auOndule2{ from{ transform:translate(10%,4%) rotate(-8deg) scaleY(1.3); } to{ transform:translate(-10%,-4%) rotate(-16deg) scaleY(.8); } }
@keyframes auOndule3{ from{ transform:translate(0,-4%) rotate(-20deg); } to{ transform:translate(-12%,8%) rotate(-10deg) scaleY(1.6); } }
.au-etoiles{ position:absolute; inset:0; }
.au-etoiles i{ position:absolute; width:2px; height:2px; border-radius:50%; background:#fff; animation:auScintille 3.2s ease-in-out infinite; }
@keyframes auScintille{ 0%,100%{ opacity:.15; } 50%{ opacity:.95; } }
.au-reflet{ position:absolute; inset:0; mix-blend-mode:color-dodge; opacity:.3;
  background:linear-gradient(115deg, transparent 30%, rgba(255,255,255,.55) calc(var(--hx,50%) - 4%), rgba(160,255,230,.35) var(--hx,50%), rgba(200,160,255,.35) calc(var(--hx,50%) + 6%), transparent 70%); }
.au-sceau{ position:absolute; z-index:2; display:inline-flex; align-items:center; gap:4px; color:#fff;
  font-size:.6rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase;
  padding:2px 7px; border-radius:999px; background:rgba(5,10,24,.5); border:1px solid rgba(255,255,255,.45); }
.au-sceau svg{ width:10px; height:10px; color:var(--au-a1); }

/* grande carte (révélation, fiche) : le fond prend toute la carte */
.aurore .carte-cadre{ background:var(--au-t); padding:2px;
  box-shadow:0 14px 28px rgba(0,0,0,.45), 0 0 26px color-mix(in srgb, var(--au-t) 45%, transparent); }
.aurore .carte-int{ position:relative; isolation:isolate; background:#0A1A3D; color:#fff; }
.aurore .carte-art{ background:none; }
/* le dessin reste en place (il donne sa hauteur à l'image de la fiche), invisible */
.aurore .carte-art > svg{ visibility:hidden; }
.aurore .carte-art > .art-photo, .aurore .carte-art > .art-voile{ display:none; }
.aurore .carte-dept{ color:rgba(255,255,255,.18); }
.aurore .carte-num{ color:rgba(255,255,255,.8); text-shadow:0 1px 3px rgba(0,0,0,.6); }
.aurore .carte-rarete{ background:var(--au-t); box-shadow:0 2px 8px rgba(0,0,0,.35); }
.aurore .au-sceau{ top:32px; left:9px; }
.aurore .carte-infos{ margin-top:-22px; padding-top:30px;
  background:linear-gradient(180deg, rgba(5,10,24,0), rgba(5,10,24,.72) 34%, rgba(5,10,24,.9)); }
.aurore .carte-nom{ color:#fff; text-shadow:0 2px 10px rgba(0,0,0,.5); }
.aurore .carte-departement{ color:rgba(255,255,255,.75); }
.aurore .carte-stats{ border-top-color:rgba(255,255,255,.2); }
.aurore .carte-stats span{ color:rgba(255,255,255,.7); }
.aurore .carte-stats b{ color:#fff; }
.au-credit{ margin:-4px 0 5px; font-size:.5rem; line-height:1.2; color:rgba(255,255,255,.55);
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
/* la fiche Front : la carte n'a pas de bloc d'infos, on assombrit le bas */
.fc-carte.aurore .carte-int::after{ content:''; position:absolute; left:0; right:0; bottom:0; height:30%; z-index:-1;
  background:linear-gradient(180deg, transparent, rgba(5,10,24,.6)); pointer-events:none; }

/* mini-carte (collection, bilan) */
.mini.aurore{ background:var(--au-t); padding:2px;
  box-shadow:0 8px 16px rgba(0,0,0,.35), 0 0 14px color-mix(in srgb, var(--au-t) 55%, transparent); }
.mini.aurore .mini-int{ position:relative; isolation:isolate; background:#0A1A3D; color:#fff; }
.mini.aurore .mini-art{ background:none; }
.mini.aurore .mini-art > svg{ visibility:hidden; }
.mini.aurore .mini-art > .art-photo, .mini.aurore .mini-art > .art-voile{ display:none; }
.mini.aurore .mini-dept{ color:rgba(255,255,255,.22); text-shadow:none; }
.mini.aurore .mini-infos{ background:linear-gradient(180deg, rgba(5,10,24,0), rgba(5,10,24,.8) 40%, rgba(5,10,24,.9)); }
.mini.aurore .mini-nom{ color:#fff; }
.mini.aurore .mini-num{ color:rgba(255,255,255,.7); }
.mini.aurore .mini-rarete{ color:#fff; }
.mini .au-voile{ filter:blur(10px); }
.mini .au-sceau{ top:5px; left:5px; padding:3px; border-radius:50%; }
.mini .au-sceau svg{ width:9px; height:9px; }
/* dans une grille, des dizaines de voiles animés coûteraient cher : ils
   restent immobiles ; seule la grande carte bouge */
.mini .au-voile i, .mini .au-etoiles i{ animation:none; }
@media (prefers-reduced-motion: reduce){ .au-voile i, .au-etoiles i{ animation:none !important; } }
"""
ecrire('style.css', css)
print(u'patch111 applique')
