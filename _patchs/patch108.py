# -*- coding: utf-8 -*-
u"""
patch108 — carte : les limites et numéros des arrondissements de Paris.

Purement visuel : Paris reste UNE commune (75056), une seule carte, un seul
propriétaire. On trace par-dessus, une fois zoomé sur Paris, les limites
entre arrondissements et, de plus près, leurs numéros.

Données : data/arrondissements-paris.json (3,5 Ko), chargé seulement quand
les contours de Paris sont affichés. Limites de la Ville de Paris (ODbL),
recalées sur le contour de Paris utilisé par le jeu pour qu'elles s'arrêtent
pile sur son bord. Aucun SQL.
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

assert os.path.exists(os.path.join(BASE, 'data', 'arrondissements-paris.json')), \
    u'data/arrondissements-paris.json manquant'

js = lire('app.js')
assert 'ARR_PARIS' not in js, u'patch108 deja applique'

js = rempl(js, u"""  const mode = dessinerFondsCanvas(ctx, trait, k, liste, joueurs);
  dessinerFrontieres(ctx, trait, mode === 'contours');""",
u"""  const mode = dessinerFondsCanvas(ctx, trait, k, liste, joueurs);
  if(mode === 'contours') dessinerArrondissementsParis(ctx, trait, k, liste);   // patch108
  dessinerFrontieres(ctx, trait, mode === 'contours');""", 'appel')

js += u"""

// ---------- patch108 : les arrondissements de Paris sur la carte ----------
// Paris reste une seule commune : ce n'est qu'un dessin par-dessus.
let ARR_PARIS = null;   // null = pas demande, 'attente', 'erreur' ou les donnees
const ARR_CODE = '75056';
async function chargerArrondissementsParis(){
  ARR_PARIS = 'attente';
  try{
    const rep = await fetch('data/arrondissements-paris.json', { cache: 'force-cache' });
    if(!rep.ok) throw new Error('introuvable');
    ARR_PARIS = await rep.json();
  } catch(e){
    ARR_PARIS = 'erreur';
  }
  renderMapOverlay();
}
function dessinerArrondissementsParis(ctx, trait, k, liste){
  const contours = CONTOURS.get('75');
  if(!contours || contours === 'erreur' || !contours[ARR_CODE]) return;
  const paris = cheminCommuneCanvas(ARR_CODE, contours[ARR_CODE]);
  // Paris doit etre a l'ecran : sinon rien a dessiner, ni a charger
  const pt = project(48.8566, 2.3522);
  const sx = pt.x * MAP_W * k + mapPanX * CV.dpr, sy = pt.y * MAP_H * k + mapPanY * CV.dpr;
  const marge = 0.15 * MAP_W * k;   // largeur de Paris, a peu pres
  if(sx < -marge || sy < -marge || sx > CV.largeur * CV.dpr + marge || sy > CV.hauteur * CV.dpr + marge) return;
  if(ARR_PARIS === null) chargerArrondissementsParis();
  if(!ARR_PARIS || ARR_PARIS === 'attente' || ARR_PARIS === 'erreur') return;

  // le chemin des limites suit la projection : refait si les communes l'ont ete
  if(CV.arrParisRef !== paris){
    const p = new Path2D();
    for(const l of ARR_PARIS.lignes){
      l.forEach(([lon, lat], i) => {
        const q = project(lat, lon);
        if(i === 0) p.moveTo(q.x * MAP_W, q.y * MAP_H); else p.lineTo(q.x * MAP_W, q.y * MAP_H);
      });
    }
    CV.arrParisChemin = p;
    CV.arrParisRef = paris;
  }
  const possedee = liste.some(c => c.code === ARR_CODE);
  ctx.save();
  ctx.clip(paris);
  ctx.strokeStyle = possedee ? 'rgba(7,17,31,0.5)' : 'rgba(169,188,212,0.32)';
  ctx.lineWidth = trait(0.9);
  ctx.stroke(CV.arrParisChemin);
  ctx.restore();

  // les numeros, seulement quand Paris est assez grand a l'ecran
  const a = project(48.85, 2.25), b = project(48.85, 2.42);
  const largeurParis = (b.x - a.x) * MAP_W * k / CV.dpr;   // en pixels CSS
  if(largeurParis < 140) return;
  const opacite = Math.min(1, (largeurParis - 140) / 60);
  const taille = Math.max(9, Math.min(13, largeurParis / 22));
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.font = '800 ' + Math.round(taille * CV.dpr) + 'px "Big Shoulders Display", Impact, sans-serif';
  ctx.globalAlpha = opacite * (possedee ? 0.7 : 0.55);
  ctx.fillStyle = possedee ? '#07111F' : '#A9BCD4';
  for(const e of ARR_PARIS.etiquettes){
    const q = project(e.lat, e.lon);
    const x = q.x * MAP_W * k + mapPanX * CV.dpr, y = q.y * MAP_H * k + mapPanY * CV.dpr;
    ctx.fillText(e.n === 1 ? '1er' : e.n + 'e', x, y);
  }
  ctx.restore();
}
"""
ecrire('app.js', js)
print(u'patch108 applique')
