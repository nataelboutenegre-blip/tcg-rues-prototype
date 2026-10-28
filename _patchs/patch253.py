# patch253 : modifier son clan et créer son blason (avec s2-52)
#  - le moteur de blason (formes, partitions, émaux, meubles) dessiné en SVG
#  - blasonHtml : le blason du clan s'il en a un, sinon l'écu au sigle d'avant
#  - l'éditeur, ouvert par le chef depuis l'écran Clan (« Modifier le clan »)
import pathlib
def rep(s, a, b, n=1):
    assert s.count(a) == n, (a[:90], s.count(a)); return s.replace(a, b)
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')

MOTEUR = r"""
// ---------- patch253 : les blasons de clan ----------
// 12 couleurs de clan sur la carte (les 8 d'avant + 4)
const CLAN_COULEURS_ED = [...CLAN_COULEURS, '#F06EA9', '#7DD3FC', '#A3E635', '#F97316'];
const BL_EMAUX = [
  ['or', 'Or', '#E8B931'], ['argent', 'Argent', '#EEF1F5'], ['gueules', 'Rouge (gueules)', '#C8102E'], ['azur', 'Bleu (azur)', '#1F4FA8'],
  ['sinople', 'Vert (sinople)', '#1E7B45'], ['sable', 'Noir (sable)', '#1B1B1F'], ['pourpre', 'Pourpre', '#6E2C8C'],
  ['orange', 'Orangé', '#E07A2E'], ['ciel', 'Bleu ciel', '#6FB1E0'], ['rose', 'Rose', '#E58BA8'], ['turquoise', 'Turquoise', '#1ABC9C'], ['brun', 'Brun', '#7A4B2A'],
];
const BL_E = Object.fromEntries(BL_EMAUX.map(([k, , c]) => [k, c]));
const BL_FORMES = {
  francais: { nom:'Français', d:'M6 6H94V74C94 96 74 108 50 116C26 108 6 96 6 74Z' },
  ancien:   { nom:'Ancien',   d:'M6 6H94C94 58 80 96 50 116C20 96 6 58 6 6Z' },
  banniere: { nom:'Bannière', d:'M10 6H90V104L50 114L10 104Z' },
  rond:     { nom:'Médaillon', d:'M50 8C76 8 94 30 94 60C94 90 76 112 50 112C24 112 6 90 6 60C6 30 24 8 50 8Z' },
};
const BL_PARTITIONS = {
  plein:     { nom:'Plein', d:'' },
  parti:     { nom:'Parti', d:'M50 0H100V120H50Z' },
  coupe:     { nom:'Coupé', d:'M0 60H100V120H0Z' },
  tranche:   { nom:'Tranché', d:'M100 0V120H0Z' },
  taille:    { nom:'Taillé', d:'M0 0V120H100Z' },
  ecartele:  { nom:'Écartelé', d:'M50 0H100V60H50ZM0 60H50V120H0Z' },
  chef:      { nom:'Chef', d:'M0 0H100V36H0Z' },
  fasce:     { nom:'Fasce', d:'M0 44H100V76H0Z' },
  pal:       { nom:'Pal', d:'M34 0H66V120H34Z' },
  bande:     { nom:'Bande', d:'M-10 6L12 -10L112 104L90 124Z' },
  chevron:   { nom:'Chevron', d:'M50 34L104 92V118L50 62L-4 118V92Z' },
  croix:     { nom:'Croix', d:'M40 0H60V50H100V70H60V120H40V70H0V50H40Z' },
  sautoir:   { nom:'Sautoir', d:'M-6 8L8 -6L50 46L92 -6L106 8L58 60L106 112L92 126L50 74L8 126L-6 112L42 60Z' },
  echiquete: { nom:'Échiqueté', d:[...Array(6)].flatMap((_, l) => [...Array(5)].map((_, c) => (l + c) % 2 ? `M${c*20} ${l*20}h20v20h-20z` : '')).join('') },
  fusele:    { nom:'Losangé', d:[...Array(7)].flatMap((_, l) => [...Array(6)].map((_, c) => `M${c*20 - (l%2)*10 + 10} ${l*20 - 10}l10 10l-10 10l-10 -10z`)).join('') },
  gironne:   { nom:'Gironné', d:[0,2,4,6].map(i => { const a1 = i*Math.PI/4, a2 = (i+1)*Math.PI/4; return `M50 60L${(50+90*Math.cos(a1)).toFixed(1)} ${(60+90*Math.sin(a1)).toFixed(1)}L${(50+90*Math.cos(a2)).toFixed(1)} ${(60+90*Math.sin(a2)).toFixed(1)}Z`; }).join('') },
};
const blEtoile = (n, R, r) => 'M' + [...Array(2*n)].map((_, i) => { const a = -Math.PI/2 + i*Math.PI/n, k = i % 2 ? r : R; return `${(20 + k*Math.cos(a)).toFixed(2)} ${(20 + k*Math.sin(a)).toFixed(2)}`; }).join('L') + 'Z';
const BL_MEUBLES = {
  aucun:    { nom:'Aucun', d:'' },
  lys:      { nom:'Fleur de lys', d:'M20 2C24.5 8 25.5 15 20 24C14.5 15 15.5 8 20 2ZM18 22.5C10 25 3.5 19 6 10.5C8.5 15 13 17.5 18 18.5ZM22 22.5C30 25 36.5 19 34 10.5C31.5 15 27 17.5 22 18.5ZM10.5 22H29.5V26H10.5ZM17 26.5C16.3 31 13.5 34 9.5 35C14 36.6 18.3 34.5 20 30.5C21.7 34.5 26 36.6 30.5 35C26.5 34 23.7 31 23 26.5Z' },
  etoile:   { nom:'Étoile', d:blEtoile(5, 18, 7.4) },
  croissant:{ nom:'Croissant', d:'M27 4.5A16.5 16.5 0 1 0 27 35.5A13 13 0 1 1 27 4.5Z' },
  tour:     { nom:'Tour', d:'M10 37V15H7.5V5H13V9H17V5H23V9H27V5H32.5V15H30V37ZM16.5 37V30A3.5 3.5 0 0 1 23.5 30V37ZM18.6 16H21.4V22H18.6Z' },
  couronne: { nom:'Couronne', d:'M5 29L7 11L14 19L20 6L26 19L33 11L35 29ZM5 31H35V36H5Z' },
  epee:     { nom:'Épée', d:'M18.5 2H21.5L22.5 25H17.5ZM10 25H30V28.5H10ZM18.3 28.5H21.7V34.5H18.3ZM20 34A3 3 0 1 1 20 40A3 3 0 1 1 20 34Z' },
  cle:      { nom:'Clé', d:'M20 1.5A7.5 7.5 0 1 1 20 16.5A7.5 7.5 0 1 1 20 1.5ZM20 5.5A3.5 3.5 0 1 0 20 12.5A3.5 3.5 0 1 0 20 5.5ZM18.3 15H21.7V38H18.3ZM21.7 29H27V32H21.7ZM21.7 34H25.5V37H21.7Z' },
  ancre:    { nom:'Ancre', trait:true, d:'M20 9V36M12.5 15H27.5M6.5 25Q8.5 36.5 20 36.5Q31.5 36.5 33.5 25M20 2.2A3.2 3.2 0 1 1 20 8.6A3.2 3.2 0 1 1 20 2.2Z' },
  arbre:    { nom:'Arbre', d:'M17.5 24H22.5V37H17.5ZM20 3A10 10 0 1 1 20 23A10 10 0 1 1 20 3ZM12 12A7.5 7.5 0 1 1 12 27A7.5 7.5 0 1 1 12 12ZM28 12A7.5 7.5 0 1 1 28 27A7.5 7.5 0 1 1 28 12Z' },
  coeur:    { nom:'Cœur', d:'M20 36C5 25 1.5 15.5 8.5 9C14 4.5 19 8 20 12.5C21 8 26 4.5 31.5 9C38.5 15.5 35 25 20 36Z' },
  coquille: { nom:'Coquille', d:'M20 5C32 5 38 15 34.5 25.5L25 35H15L5.5 25.5C2 15 8 5 20 5ZM13 33H27V37H13Z', nervures:true },
  hermine:  { nom:'Hermine', d:'M20 4.5A2.8 2.8 0 1 1 20 10.1A2.8 2.8 0 1 1 20 4.5ZM14.5 7.5A2.8 2.8 0 1 1 14.5 13.1A2.8 2.8 0 1 1 14.5 7.5ZM25.5 7.5A2.8 2.8 0 1 1 25.5 13.1A2.8 2.8 0 1 1 25.5 7.5ZM20 12.5C17 22 13 30 10.5 36L20 31.5L29.5 36C27 30 23 22 20 12.5Z' },
  aigle:    { nom:'Aigle', d:'M20 5C22.5 5 24 7 23.5 9.5L35 4L32 14L38 12.5L32.5 21H25.5L28.5 31H24.5L22 26L20 37L18 26L15.5 31H11.5L14.5 21H7.5L2 12.5L8 14L5 4L16.5 9.5C16 7 17.5 5 20 5Z' },
  soleil:   { nom:'Soleil', d:'M' + [...Array(32)].map((_, i) => { const a = -Math.PI/2 + i*Math.PI/16, k = i % 2 ? 11 : 17.5; return `${(20 + k*Math.cos(a)).toFixed(2)} ${(20 + k*Math.sin(a)).toFixed(2)}`; }).join('L') + 'Z' },
  epis:     { nom:'Épi de blé', d:'M19 14H21V38H19ZM20 2C22.5 4 22.5 7 20 9C17.5 7 17.5 4 20 2ZM20 8C24.5 7.5 26.5 10 25.5 13.5C22 14 19.5 12 20 8ZM20 8C15.5 7.5 13.5 10 14.5 13.5C18 14 20.5 12 20 8ZM20 14C24.5 13.5 26.5 16 25.5 19.5C22 20 19.5 18 20 14ZM20 14C15.5 13.5 13.5 16 14.5 19.5C18 20 20.5 18 20 14ZM20 20C24.5 19.5 26.5 22 25.5 25.5C22 26 19.5 24 20 20ZM20 20C15.5 19.5 13.5 22 14.5 25.5C18 26 20.5 24 20 20Z' },
};
const BL_DEFAUT = { forme:'francais', partition:'plein', c1:'azur', c2:'or', meuble:'aucun', cm:'or', nombre:1, bordure:'aucune' };
let blCompteur = 0;
// toute valeur inconnue retombe sur le défaut : rien d'autre que nos dessins n'entre dans le SVG
function blasonNet(b){
  const x = Object.assign({}, BL_DEFAUT, b || {});
  return { forme: BL_FORMES[x.forme] ? x.forme : 'francais', partition: BL_PARTITIONS[x.partition] ? x.partition : 'plein',
           c1: BL_E[x.c1] ? x.c1 : 'azur', c2: BL_E[x.c2] ? x.c2 : 'or', meuble: BL_MEUBLES[x.meuble] ? x.meuble : 'aucun',
           cm: BL_E[x.cm] ? x.cm : 'or', nombre: Number(x.nombre) === 3 ? 3 : 1, bordure: BL_E[x.bordure] ? x.bordure : 'aucune' };
}
function blasonSVG(b0){
  const b = blasonNet(b0), id = 'bl' + (++blCompteur);
  const F = BL_FORMES[b.forme], P = BL_PARTITIONS[b.partition], M = BL_MEUBLES[b.meuble], cm = BL_E[b.cm];
  const ombre = b.cm === 'sable' ? 'rgba(255,255,255,.35)' : 'rgba(0,0,0,.38)';
  const meuble = (x, y, k) => {
    if(!M.d) return '';
    const t = `transform="translate(${x - 20*k} ${y - 20*k}) scale(${k})"`;
    if(M.trait) return `<g ${t}><path d="${M.d}" fill="none" stroke="${ombre}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/><path d="${M.d}" fill="none" stroke="${cm}" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/></g>`;
    const nerv = M.nervures ? `<path d="M20 9V33M14 11L16.5 33M26 11L23.5 33M8.5 16L13 31M31.5 16L27 31" stroke="${ombre}" stroke-width="1.3" fill="none"/>` : '';
    return `<g ${t}><path d="${M.d}" fill-rule="evenodd" fill="${cm}" stroke="${ombre}" stroke-width="1.2" stroke-linejoin="round"/>${nerv}</g>`;
  };
  const meubles = b.nombre === 3 ? meuble(32, 38, .62) + meuble(68, 38, .62) + meuble(50, 80, .62) : meuble(50, b.forme === 'rond' ? 60 : 56, 1.25);
  const bord = b.bordure !== 'aucune' ? `<path d="${F.d}" fill="none" stroke="${BL_E[b.bordure]}" stroke-width="14"/>` : '';
  return `<defs><clipPath id="${id}"><path d="${F.d}"/></clipPath>
      <linearGradient id="${id}g" x1="0" y1="0" x2="0.4" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".22"/><stop offset=".55" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".22"/></linearGradient></defs>
    <g clip-path="url(#${id})"><rect x="-10" y="-10" width="120" height="140" fill="${BL_E[b.c1]}"/>${P.d ? `<path d="${P.d}" fill="${BL_E[b.c2]}"/>` : ''}${meubles}${bord}
      <rect x="-10" y="-10" width="120" height="140" fill="url(#${id}g)"/></g>
    <path d="${F.d}" fill="none" stroke="#0B1830" stroke-width="3.2" stroke-linejoin="round"/>
    <path d="${F.d}" fill="none" stroke="rgba(255,255,255,.28)" stroke-width="1" stroke-linejoin="round" transform="translate(50 60) scale(.955) translate(-50 -60)"/>`;
}
let BLASONS = new Map();   // sigle -> { blason, libre }
async function chargerBlasons(){
  try{
    const { data, error } = await sb.rpc('clans_blasons');
    if(error) return;
    BLASONS = new Map((data || []).map(r => [r.tag, { blason: r.blason, libre: r.nom_libre_le ? new Date(r.nom_libre_le) : null }]));
  }catch(e){ /* les écus au sigle restent */ }
}
// l'éditeur (chef) : null quand il est fermé
let clanEdition = null;
function ouvrirEditionClan(c){
  const b = BLASONS.get(c.tag);
  clanEdition = { nom: c.nom, tag: c.tag, carte: CLAN_COULEURS_ED.includes(String(c.couleur).toUpperCase()) ? String(c.couleur).toUpperCase() : CLAN_COULEURS_ED[0],
                  b: blasonNet(b && b.blason ? b.blason : null), libre: b && b.libre && b.libre > new Date() ? b.libre : null };
}
function editionClanHtml(){
  const E = clanEdition, B = E.b;
  const bt = (g, v, html, label, style) => `<button type="button" data-bl-g="${g}" data-bl-v="${v}" aria-pressed="${String(g === 'carte' ? E.carte : B[g]) === String(v)}"${label ? ` aria-label="${label}" title="${label}"` : ''}${style ? ` style="${style}"` : ''}>${html}</button>`;
  const pastilles = (g, aucune) => (aucune ? bt(g, 'aucune', '', 'Aucune').replace('<button', '<button class="aucune"') : '')
    + BL_EMAUX.map(([k, nom, c]) => bt(g, k, '', nom, `background:${c}`)).join('');
  const ecu = (b) => `<svg viewBox="0 0 100 120" aria-hidden="true">${blasonSVG(b)}</svg>`;
  const verrou = E.libre ? `<p class="clan-note">Nom et sigle modifiables à nouveau le ${E.libre.toLocaleDateString('fr-FR', { day:'numeric', month:'long' })} à ${E.libre.toLocaleTimeString('fr-FR', { hour:'2-digit', minute:'2-digit' })}.</p>` : '';
  return `<div class="clan-carte bl-edition">
    <div class="bl-tete"><svg class="bl-grand" viewBox="0 0 100 120" aria-hidden="true">${blasonSVG(B)}</svg>
      <div><div class="clan-nom" id="blVNom">${echapperTexte(E.nom)}</div><span class="bl-tag" style="--clan:${E.carte}" id="blVTag">${echapperTexte(E.tag)}</span>
        <div class="bl-mini">${ecu(B)}<span>Dans le classement</span></div></div></div>
    <h2>Nom et sigle</h2>
    <div class="clan-form"><label>Nom du clan<input id="blNom" maxlength="24" value="${echapperTexte(E.nom)}"${E.libre ? ' disabled' : ''}></label>
      <label class="bl-sigle">Sigle<input id="blTag" maxlength="4" value="${echapperTexte(E.tag)}"${E.libre ? ' disabled' : ''}></label></div>${verrou}
    <h2>Couleur sur la carte</h2><div class="bl-emaux">${CLAN_COULEURS_ED.map(c => bt('carte', c, '', 'Couleur du clan sur la carte', `background:${c}`)).join('')}</div>
    <h2>Forme de l’écu</h2><div class="bl-choix">${Object.entries(BL_FORMES).map(([k, f]) => bt('forme', k, `${ecu({ ...B, forme:k })}<span>${f.nom}</span>`)).join('')}</div>
    <h2>Partition</h2><div class="bl-choix">${Object.entries(BL_PARTITIONS).map(([k, p]) => bt('partition', k, `${ecu({ ...B, partition:k, meuble:'aucun', bordure:'aucune' })}<span>${p.nom}</span>`)).join('')}</div>
    <div class="bl-deux"><div><h2>Couleur 1</h2><div class="bl-emaux">${pastilles('c1')}</div></div>
      <div><h2>Couleur 2</h2>${BL_PARTITIONS[B.partition].d ? `<div class="bl-emaux">${pastilles('c2')}</div>` : '<p class="clan-note">Partition « Plein » : une seule couleur.</p>'}</div></div>
    <h2>Meuble</h2><div class="bl-choix bl-meubles">${Object.entries(BL_MEUBLES).map(([k, m]) => bt('meuble', k,
      `<svg viewBox="0 0 40 40" aria-hidden="true">${m.d ? (m.trait ? `<path d="${m.d}" fill="none" stroke="#E6EDF7" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/>` : `<path d="${m.d}" fill-rule="evenodd" fill="#E6EDF7"/>`) : '<path d="M10 10L30 30M30 10L10 30" stroke="#5B6E8C" stroke-width="2.5"/>'}</svg><span>${m.nom}</span>`)).join('')}</div>
    ${BL_MEUBLES[B.meuble].d ? `<div class="bl-deux"><div><h2>Couleur du meuble</h2><div class="bl-emaux">${pastilles('cm')}</div></div>
      <div><h2>Nombre</h2><div class="bl-seg">${bt('nombre', 1, 'Un seul')}${bt('nombre', 3, 'Trois')}</div></div></div>` : ''}
    <h2>Bordure</h2><div class="bl-emaux">${pastilles('bordure', true)}</div>
    <div class="bl-actions"><button type="button" class="bq-btn secondaire" data-bl-hasard>Au hasard</button>
      <button type="button" class="bq-btn secondaire" data-bl-annuler>Annuler</button><button type="button" class="bq-btn" data-bl-enregistrer>Enregistrer</button></div>
    <p class="clan-note">Le nom et le sigle se changent une fois par semaine ; la couleur et le blason, quand tu veux. Un nom ou un sigle déjà pris est refusé.</p>
  </div>`;
}
"""
s = rep(s, "let clanMembres = new Set();          // ids des autres membres de mon clan (cibles exclues)\n",
           "let clanMembres = new Set();          // ids des autres membres de mon clan (cibles exclues)\n" + MOTEUR)

# blasonHtml : le blason s'il existe
s = rep(s, """function blasonHtml(tag, couleur, petit){
  return `<span class="blason${petit ? ' petit' : ''}" style="--clan:${couleur}">${echapperTexte(tag)}</span>`;""",
"""function blasonHtml(tag, couleur, petit){
  const bl = BLASONS.get(tag);   // patch253
  if(bl && bl.blason) return `<span class="blason blason-svg${petit ? ' petit' : ''}" title="${echapperTexte(tag)}"><svg viewBox="0 0 100 120" aria-hidden="true">${blasonSVG(bl.blason)}</svg></span>`;
  return `<span class="blason${petit ? ' petit' : ''}" style="--clan:${couleur}">${echapperTexte(tag)}</span>`;""")

# les blasons se chargent avec les clans de la carte (au démarrage et après chaque action de clan)
s = rep(s, """    const { data, error } = await sb.rpc('clans_carte');
    if(error) return;""", """    const [{ data, error }] = await Promise.all([sb.rpc('clans_carte'), chargerBlasons()]);   // patch253
    if(error) return;""")

# l'écran Clan : bouton « Modifier » pour le chef, et l'éditeur à la place de la carte du clan
s = rep(s, """      <div class="clan-tete">${blasonHtml(c.tag, c.couleur)}<div><div class="clan-nom">${echapperTexte(c.nom)}</div><small>${n} membre${n > 1 ? 's' : ''} sur 8${n < 3 ? ' · classé à partir de 3' : ''}</small></div></div>""",
"""      <div class="clan-tete">${blasonHtml(c.tag, c.couleur)}<div><div class="clan-nom">${echapperTexte(c.nom)}</div><small>${n} membre${n > 1 ? 's' : ''} sur 8${n < 3 ? ' · classé à partir de 3' : ''}</small></div>${c.chef ? '<button type="button" class="bq-btn secondaire bl-modifier" data-bl-ouvrir>Modifier le clan</button>' : ''}</div>""")
s = rep(s, """  zone.innerHTML = `<div class="clan-grille">${gauche}${blocClassement}</div>`;""",
"""  if(clanEdition && c && c.chef) gauche = editionClanHtml();   // patch253
  else clanEdition = null;
  zone.innerHTML = `<div class="clan-grille">${gauche}${blocClassement}</div>`;""")

# les clics de l'éditeur
s = rep(s, """  if(b.dataset.clanGerer){""",
"""  // patch253 : l'éditeur du clan
  if(b.hasAttribute('data-bl-ouvrir')){ ouvrirEditionClan(clanCache.moi.clan); renderClan(); document.getElementById('clanZone').scrollIntoView({ behavior:'smooth', block:'start' }); return; }
  if(clanEdition){
    if(b.dataset.blG){ const g = b.dataset.blG, v = b.dataset.blV;
      if(g === 'carte') clanEdition.carte = v; else clanEdition.b[g] = g === 'nombre' ? Number(v) : v;
      const y = window.scrollY; renderClan(); window.scrollTo(0, y); return; }
    if(b.hasAttribute('data-bl-annuler')){ clanEdition = null; renderClan(); return; }
    if(b.hasAttribute('data-bl-hasard')){
      const tire = (o) => o[Math.floor(Math.random() * o.length)], cles = BL_EMAUX.map(x => x[0]), B = clanEdition.b;
      B.forme = tire(Object.keys(BL_FORMES)); B.partition = tire(Object.keys(BL_PARTITIONS));
      B.c1 = tire(cles); do { B.c2 = tire(cles); } while(B.c2 === B.c1);
      B.meuble = tire(Object.keys(BL_MEUBLES).slice(1)); do { B.cm = tire(cles); } while(B.cm === B.c1);
      B.nombre = tire([1, 1, 3]); B.bordure = tire(['aucune', 'aucune', 'aucune', ...cles]);
      const y = window.scrollY; renderClan(); window.scrollTo(0, y); return; }
    if(b.hasAttribute('data-bl-enregistrer')){
      b.disabled = true;
      const E = clanEdition;
      return actionClan('clan_modifier', { p_nom: E.nom.trim(), p_tag: E.tag.trim().toUpperCase(), p_couleur: E.carte, p_blason: E.b }, 'Clan modifié')
        .then(ok => { if(ok){ clanEdition = null; renderClan(); } else b.disabled = false; });
    }
  }
  if(b.dataset.clanGerer){""")
f.write_text(s, encoding='utf-8')

# la saisie du nom et du sigle : on garde le focus (pas de nouveau rendu), l'aperçu suit
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
s = rep(s, "document.getElementById('panel-clan').addEventListener('click', (e) => {",
"""document.getElementById('panel-clan').addEventListener('input', (e) => {   // patch253
  if(!clanEdition) return;
  if(e.target.id === 'blNom'){ clanEdition.nom = e.target.value; const v = document.getElementById('blVNom'); if(v) v.textContent = e.target.value; }
  if(e.target.id === 'blTag'){ clanEdition.tag = e.target.value.toUpperCase(); const v = document.getElementById('blVTag'); if(v) v.textContent = clanEdition.tag; }
});
document.getElementById('panel-clan').addEventListener('click', (e) => {""")
f.write_text(s, encoding='utf-8')

f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
s += """
/* ---------- patch253 : blasons et édition du clan ---------- */
.blason.blason-svg{ background:none; clip-path:none; width:62px; height:74px; }
.blason.blason-svg.petit{ width:27px; height:32px; }
.blason.blason-svg svg{ width:100%; height:100%; display:block; filter:drop-shadow(0 2px 4px rgba(0,0,0,.35)); }
.cl-marche.cl-clan .blason.blason-svg{ width:38px; height:46px; }
.clan-tete{ flex-wrap:wrap; }
.clan-tete .bl-modifier{ margin-left:auto; align-self:flex-start; white-space:nowrap; font-size:.9rem; padding:6px 10px; }
.bl-tete{ display:flex; gap:18px; align-items:center; margin-bottom:6px; }
.bl-grand{ width:120px; height:144px; flex:none; filter:drop-shadow(0 8px 18px rgba(0,0,0,.45)); }
.bl-tag{ display:inline-block; margin-top:6px; font-family:var(--titre); font-weight:800; font-size:.9rem; padding:2px 8px; border-radius:6px; background:var(--clan); color:#1a0d02; }
.bl-mini{ display:flex; align-items:center; gap:8px; margin-top:10px; color:var(--brume); font-size:.78rem; }
.bl-mini svg{ width:27px; height:32px; }
.bl-sigle{ max-width:120px; }
.bl-choix{ display:flex; flex-wrap:wrap; gap:7px; }
.bl-choix button{ background:var(--nuit-2); border:1.5px solid rgba(169,188,212,.18); border-radius:10px; padding:5px; cursor:pointer; color:#fff;
  display:flex; flex-direction:column; align-items:center; gap:3px; font:inherit; font-size:.66rem; }
.bl-choix button[aria-pressed="true"]{ border-color:var(--c-legendaire, #F0B429); background:var(--nuit-3); }
.bl-choix svg{ width:36px; height:43px; display:block; }
.bl-choix.bl-meubles svg{ width:32px; height:32px; }
.bl-choix span{ color:var(--brume); max-width:56px; text-align:center; line-height:1.15; }
.bl-emaux{ display:flex; flex-wrap:wrap; gap:7px; }
.bl-emaux button{ width:30px; height:30px; border-radius:50%; border:2px solid rgba(255,255,255,.18); cursor:pointer; padding:0; }
.bl-emaux button[aria-pressed="true"]{ border-color:#fff; box-shadow:0 0 0 2px var(--nuit), 0 0 0 4px #fff; }
.bl-emaux button.aucune{ background:repeating-linear-gradient(45deg, #2a3a55 0 4px, #1a2a45 4px 8px); }
.bl-deux{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:14px; }
@media (max-width:560px){ .bl-deux{ grid-template-columns:1fr; } .bl-grand{ width:96px; height:115px; } }
.bl-seg{ display:inline-flex; background:var(--nuit); padding:3px; border-radius:10px; gap:2px; }
.bl-seg button{ background:none; border:0; color:var(--brume); font:inherit; font-size:.85rem; padding:6px 12px; border-radius:8px; cursor:pointer; }
.bl-seg button[aria-pressed="true"]{ background:var(--nuit-3); color:#fff; }
.bl-actions{ display:flex; gap:8px; flex-wrap:wrap; margin-top:18px; }
.bl-actions [data-bl-enregistrer]{ margin-left:auto; }
.bl-choix button:focus-visible, .bl-emaux button:focus-visible, .bl-seg button:focus-visible{ outline:2px solid var(--c-legendaire, #F0B429); outline-offset:2px; }
"""
f.write_text(s, encoding='utf-8')

# droit « modifier le clan » pour les bras droits (choisi par le chef)
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
s = rep(s, "${bascule('inviter', 'Inviter')}${bascule('exclure', 'Exclure des membres')}",
           "${bascule('inviter', 'Inviter')}${bascule('exclure', 'Exclure des membres')}${bascule('modifier', 'Modifier le clan')}")
s = rep(s, "p_bras_droit: b.dataset.actif === '1', p_inviter: true, p_exclure: false }",
           "p_bras_droit: b.dataset.actif === '1', p_inviter: true, p_exclure: false, p_modifier: false }")
s = rep(s, "const d = Object.assign({ inviter: true, exclure: false }, (m && m.droits) || {});",
           "const d = Object.assign({ inviter: true, exclure: false, modifier: false }, (m && m.droits) || {});")
s = rep(s, "p_bras_droit: true, p_inviter: d.inviter, p_exclure: d.exclure }",
           "p_bras_droit: true, p_inviter: d.inviter, p_exclure: d.exclure, p_modifier: d.modifier }")
s = rep(s, "${c.chef ? '<button type=\"button\" class=\"bq-btn secondaire bl-modifier\" data-bl-ouvrir>Modifier le clan</button>' : ''}",
           "${c.chef || (c.droits || {}).modifier ? '<button type=\"button\" class=\"bq-btn secondaire bl-modifier\" data-bl-ouvrir>Modifier le clan</button>' : ''}")
s = rep(s, "  if(clanEdition && c && c.chef) gauche = editionClanHtml();   // patch253",
           "  if(clanEdition && c && (c.chef || (c.droits || {}).modifier)) gauche = editionClanHtml();   // patch253")
s = rep(s, "Le chef peut nommer 2 bras droits et choisir leurs droits (inviter, exclure).",
           "Le chef peut nommer 2 bras droits et choisir leurs droits (inviter, exclure, modifier le clan).")
s = rep(s, "tu choisis ensuite s'il peut aussi exclure.</p>", "tu choisis ensuite s'il peut aussi exclure ou modifier le clan.</p>")
f.write_text(s, encoding='utf-8')
print('patch253 ok')
