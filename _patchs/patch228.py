# -*- coding: utf-8 -*-
u"""
patch228 — l'Aurore du Front suit le tirage (s2-40) et se voit (27/10).

- Le Front ne montre plus en Aurore toute commune de la liste : seulement
  celles marquées Aurore côté serveur (tirées en Aurore 1 fois sur 3, ou
  tenues le 27/10). Sans s2-40, on garde l'ancienne règle (la liste).
- Carte du Front : une étoile Aurore (4 branches, couleurs d'aurore, halo)
  sur chaque commune Aurore tenue, à la place du point ou de l'étoile.
- Combat : la carte de la cible porte « ✦ Aurore », sa photo Aurore et un
  liseré d'aurore. Panneau de la carte : ligne « Aurore ».
- Après un paquet Front, la liste est relue : une Aurore tirée s'affiche
  tout de suite comme telle.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rep(s, a, b, n=1):
    c = s.count(a); assert c == n, ('MATCH', a[:70], 'trouve', c, 'attendu', n); return s.replace(a, b)

s = lire('app.js')
assert 'patch228' not in s
# 1. la règle : la marque du serveur, sinon la liste
s = rep(s, "const auroreFront = (code) => SAISON2 && !enTerra() && !!(AURORE && AURORE[code]);",
"""// patch228 : en Front, l'Aurore suit la marque du serveur (s2-40) ; sans elle, la liste
let FRONT_AURORES = null;   // Set des codes Aurore du Front, null = s2-40 absent
let auroresFrontLu = 0;
async function chargerAuroresFront(){
  if(!SAISON2) return;
  try{
    const { data, error } = await sb.rpc('front_aurores');
    if(error) return;
    FRONT_AURORES = new Set((data || []).map(r => String(r.commune_code)));
    auroresFrontLu = Date.now();
    if(typeof demanderDessin === 'function' && canvasActif()){ CV.donneesSignature = null; demanderDessin(); }
  }catch(e){}
}
const auroreFront = (code) => SAISON2 && !enTerra() && (FRONT_AURORES ? FRONT_AURORES.has(String(code)) : !!(AURORE && AURORE[code]));""")
# chargée avec les territoires des autres joueurs
s = rep(s, "  dmEtape(88, 'Tes paquets…');\n", "  chargerAuroresFront();   // patch228\n  dmEtape(88, 'Tes paquets…');\n")
# relue après un paquet Front
s = rep(s, "      aurore: auroreFront(row.code)\n    });\n  }\n  return draws;\n}",
           "      aurore: auroreFront(row.code)\n    });\n  }\n  // patch228 : une Aurore vient peut-être de sortir (1 fois sur 3) : on relit la liste\n"
           "  if(draws.length){ await chargerAuroresFront(); for(const d of draws) d.aurore = auroreFront(d.code); }\n  return draws;\n}")

# 2. la carte : l'étoile Aurore
s = rep(s, """    if(c.tier !== 'legendaire' && (legendairesSeules || (c.tier !== 'rare' && c.tier !== 'epique'))) continue;
    const x = c.x, y = c.y;
    if(x < vue[0] || x > vue[2] || y < vue[1] || y > vue[3]) continue;
    const j = joueurs.get(c.joueur);
    if(!j) continue;
    ctx.globalAlpha = opaciteJoueur(c.joueur, 1);
""", """    const au = auroreFront(c.code);   // patch228
    if(!au && c.tier !== 'legendaire' && (legendairesSeules || (c.tier !== 'rare' && c.tier !== 'epique'))) continue;
    const x = c.x, y = c.y;
    if(x < vue[0] || x > vue[2] || y < vue[1] || y > vue[3]) continue;
    const j = joueurs.get(c.joueur);
    if(!j) continue;
    ctx.globalAlpha = opaciteJoueur(c.joueur, 1);
    if(au){ dessinerEtoileAurore(ctx, x, y, (j.moi ? 11 : 10) * e); ctx.globalAlpha = 1; continue; }
""")
s = rep(s, "function dessinerMarqueursCanvas(ctx, liste, joueurs, k, legendairesSeules){",
"""// patch228 : une commune Aurore sur la carte du Front : étoile à 4 branches aux couleurs d'aurore
function dessinerEtoileAurore(ctx, x, y, r){
  const h = ctx.createRadialGradient(x, y, 0, x, y, r * 2.3);
  h.addColorStop(0, 'rgba(61,242,192,0.7)'); h.addColorStop(0.5, 'rgba(91,140,255,0.3)'); h.addColorStop(1, 'rgba(176,108,255,0)');
  ctx.fillStyle = h; ctx.beginPath(); ctx.arc(x, y, r * 2.3, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath();
  for(let i = 0; i < 8; i++){
    const a = -Math.PI / 2 + i * Math.PI / 4, rr = i % 2 ? r * 0.3 : r;
    ctx.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr);
  }
  ctx.closePath();
  const g = ctx.createLinearGradient(x - r, y - r, x + r, y + r);
  g.addColorStop(0, '#FFFFFF'); g.addColorStop(0.35, '#9FFFE2'); g.addColorStop(0.7, '#7FA8FF'); g.addColorStop(1, '#C08CFF');
  ctx.fillStyle = g; ctx.fill();
  ctx.strokeStyle = '#0B1830'; ctx.lineWidth = r * 0.17; ctx.stroke();
}
function dessinerMarqueursCanvas(ctx, liste, joueurs, k, legendairesSeules){""")

# 3. le Combat : la cible Aurore
s = rep(s, """    return `
      <article class="cible ${commune.tier}">
        <div class="cible-int">
          <div class="cible-haut">
            <span class="cible-rarete">${tier.label}</span>""", """    const au = auroreFront(c.commune_code);   // patch228
    return `
      <article class="cible ${commune.tier}${au ? ' cible-aurore' : ''}">
        <div class="cible-int">
          <div class="cible-haut">
            <span class="cible-rarete">${tier.label}${au ? '<span class="cible-au">✦ Aurore</span>' : ''}</span>""")
s = rep(s, """          <div class="cible-art">${miniArtSvg(c.commune_code, commune.tier)}<span class="cible-dept">""",
           """          <div class="cible-art">${miniArtSvg(c.commune_code, commune.tier)}${au && auroreImage(c.commune_code) ? `<img class="art-photo" src="${auroreImage(c.commune_code)}" alt="" loading="lazy" decoding="async" data-onfail="next"><span class="cible-au-voile"></span>` : ''}<span class="cible-dept">""")

# 3 bis. la légende de la carte
s = rep(s, '<polygon points="${etoileSvg(13, 13, 6)}" fill="#FFF6D6" stroke="#0B1830"/></svg>Légend.</div>\n',
           '<polygon points="${etoileSvg(13, 13, 6)}" fill="#FFF6D6" stroke="#0B1830"/></svg>Légend.</div>\n'
           '        <div><svg width="26" height="26"><defs><linearGradient id="legAu" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff"/><stop offset=".4" stop-color="#9FFFE2"/><stop offset="1" stop-color="#C08CFF"/></linearGradient></defs>'
           '<circle cx="13" cy="13" r="11" fill="rgba(61,242,192,.25)"/><path d="M13 3 L15.4 10.6 L23 13 L15.4 15.4 L13 23 L10.6 15.4 L3 13 L10.6 10.6 Z" fill="url(#legAu)" stroke="#0B1830"/></svg>Aurore</div>\n')

# 4. le panneau de la carte
s = rep(s, "  if(c.pop != null) lignes.push(['Population', nbFr(c.pop)]);\n",
           "  if(SAISON2 && auroreFront(code)) lignes.push(['Carte', '<b class=\"pc-aurore\">✦ Aurore</b>']);   // patch228\n  if(c.pop != null) lignes.push(['Population', nbFr(c.pop)]);\n")
ecrire('app.js', s)

c = lire('style.css')
c = c.rstrip('\n') + u'''

/* ---------- patch228 : l'Aurore se voit dans le Front ---------- */
.cible-au{ display:inline-flex; align-items:center; margin-left:6px; padding:1px 7px; border-radius:999px; font-size:.62rem; font-weight:800; letter-spacing:.04em;
  color:#06231A; background:linear-gradient(90deg, #7FF2D0, #5B8CFF 60%, #B06CFF); vertical-align:1px; }
.cible.cible-aurore{ box-shadow:0 0 0 1.5px rgba(61,242,192,.75), 0 0 18px rgba(91,140,255,.35), 0 10px 22px rgba(0,0,0,.4); }
.cible-aurore .cible-art{ position:relative; overflow:hidden; }
.cible-au-voile{ position:absolute; inset:0; z-index:2; pointer-events:none; mix-blend-mode:screen;
  background:linear-gradient(160deg, rgba(61,242,192,.35), rgba(91,140,255,.12) 45%, rgba(176,108,255,.35)); }
.cible-aurore .cible-dept{ z-index:3; }
.pc-aurore{ background:linear-gradient(90deg, #7FF2D0, #8FB4FF 55%, #C9A6FF); -webkit-background-clip:text; background-clip:text; color:transparent; }
'''
ecrire('style.css', c)
print('patch228 ok')
