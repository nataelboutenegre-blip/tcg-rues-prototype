const BL_DEFAUT = { forme:'francais', partition:'plein', c1:'azur', c2:'or', c3:'gueules', meuble:'aucun', cm:'or', nombre:1, bordure:'aucune',
                    manteau:'aucun', cmanteau:'gueules', timbre:'aucun', devise:'aucune', cdevise:'argent', calques:[] };   // patch543 : ornements, calques
let blCompteur = 0;
// toute valeur inconnue retombe sur le défaut : rien d'autre que nos dessins n'entre dans le SVG
function blasonNet(b){
  const x = Object.assign({}, BL_DEFAUT, b || {});
  return { forme: BL_FORMES[x.forme] ? x.forme : 'francais', partition: BL_PARTITIONS[x.partition] ? x.partition : 'plein',
           c1: BL_E[x.c1] ? x.c1 : 'azur', c2: BL_E[x.c2] ? x.c2 : 'or', c3: BL_E[x.c3] ? x.c3 : 'gueules', meuble: BL_MEUBLES[x.meuble] ? x.meuble : 'aucun',
           cm: BL_E[x.cm] ? x.cm : 'or', nombre: Number(x.nombre) === 3 ? 3 : 1, bordure: BL_E[x.bordure] ? x.bordure : 'aucune',
           manteau: x.manteau === 'manteau' ? 'manteau' : 'aucun', cmanteau: BL_E[x.cmanteau] ? x.cmanteau : 'gueules',
           timbre: BL_TIMBRES[x.timbre] ? x.timbre : 'aucun', devise: BL_DEVISES[x.devise] ? x.devise : 'aucune',
           cdevise: BL_E[x.cdevise] ? x.cdevise : 'argent',
           calques: Array.isArray(x.calques) ? x.calques.slice(0, BL_CALQUES_MAX).map(blCalqueNet) : [] };
}
function blasonSVG(b0, o){
  const b = blasonNet(b0), id = 'bl' + (++blCompteur);
  const F = BL_FORMES[b.forme], P = BL_PARTITIONS[b.partition], M = BL_MEUBLES[b.meuble], cm = BL_E[b.cm];
  const ombreDe = (c) => c === 'sable' ? 'rgba(255,255,255,.35)' : 'rgba(0,0,0,.38)';
  const meubles = b.calques.length   // patch543 : l'atelier, des meubles placés librement
    ? b.calques.map(c => blMeuble(BL_MEUBLES[c.m], BL_E[c.c], ombreDe(c.c), c.x, c.y, 1.25 * c.s / 100, c.r, c.f)).join('')
    : b.nombre === 3 ? [[32, 38], [68, 38], [50, 80]].map(([x, y]) => blMeuble(M, cm, ombreDe(b.cm), x, y, .62)).join('')
    : blMeuble(M, cm, ombreDe(b.cm), 50, b.forme === 'rond' ? 60 : 56, 1.25);
  const bord = b.bordure !== 'aucune' ? `<path d="${F.d}" fill="none" stroke="${BL_E[b.bordure]}" stroke-width="14"/>` : '';
  const orn = o ? blOrnements(b, o, id) : { avant: '', apres: '' };
  return `${orn.avant}<defs><clipPath id="${id}"><path d="${F.d}"/></clipPath>
      <linearGradient id="${id}g" x1="0" y1="0" x2="0.4" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".22"/><stop offset=".55" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".22"/></linearGradient></defs>
    <g clip-path="url(#${id})"><rect x="-10" y="-10" width="120" height="140" fill="${BL_E[b.c1]}"/>${P.d ? `<path d="${P.d}" fill="${BL_E[b.c2]}"/>` : ''}${P.d3 ? `<path d="${P.d3}" fill="${BL_E[b.c3]}"/>` : ''}${meubles}${bord}
      <rect x="-10" y="-10" width="120" height="140" fill="url(#${id}g)"/></g>
    <path d="${F.d}" fill="none" stroke="#0B1830" stroke-width="3.2" stroke-linejoin="round"/>
    <path d="${F.d}" fill="none" stroke="rgba(255,255,255,.28)" stroke-width="1" stroke-linejoin="round" transform="translate(50 60) scale(.955) translate(-50 -60)"/>${orn.apres}`;
}
