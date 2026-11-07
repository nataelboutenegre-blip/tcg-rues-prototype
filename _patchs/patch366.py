# patch366 (7/11/2026) : les bâtiments en pixel art (s2-112, aperçu validé « c'est parfait »).
#
#   - Mon front : une case « Mes bâtiments » (vignettes en pixel art, nombre,
#     constructions en cours, lingots ; « Nouveau » jusqu'à la première visite) ;
#   - l'écran Bâtiments, plein écran :
#       « Les miens » : chaque bâtiment, son style, sa commune, son état ;
#       « Les autres » : recherche (joueur ou commune), région, tri, type,
#       30 par page ; jamais une Banque, un Centre seulement une fois dévoilé
#       (le serveur décide : batiments_autres) ;
#   - la fiche d'un bâtiment : le pixel art en grand, le style, le joueur, le
#     lieu, l'effet ; « Voir sur la carte » et « Attaquer » ;
#   - la construction : on choisit d'abord son style (2 ou 3, gratuits,
#     purement décoratifs), puis « Construire » (batiment_construire_style).
# Les dessins sont dans batiments/<type>-<style>.svg (_outils/batiments-pixel.py).
# Sans s2-112 (pas de liste de styles), la construction reste comme avant.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch366' not in s, 'patch366 déjà appliqué'

BLOC = r"""// ---------- patch366 : les bâtiments en pixel art (s2-112) ----------
// Une case dans Mon front, un écran Bâtiments (les miens / ceux des autres),
// la fiche d'un bâtiment et le choix du style à la construction. Les Banques
// n'apparaissent jamais chez les autres ; un Centre seulement une fois dévoilé.
var BT_STYLES_DEFAUT = { fonderie: ['brique', 'acier'], forteresse: ['chateau', 'bastion', 'tour'], banque: ['classique', 'coffre'], centre: ['labo', 'bunker'] };
var BT_STYLE_NOMS = { brique: 'Brique', acier: 'Acier', chateau: 'Château fort', bastion: 'Bastion', tour: 'Tour de guet', classique: 'Classique', coffre: 'Coffre-fort', labo: 'Laboratoire', bunker: 'Bunker' };
var BTE = { vue: 'miens', type: '', region: '', tri: 'recents', q: '', lignes: [], total: null, totalSansFiltre: null, decalage: 0, charge: false, erreur: '', req: 0, minuteur: 0 };
var BTS = { code: null, type: null, style: null };
function btStyles(type){
  const S = BATIMENTS && BATIMENTS.styles;
  return (S && Array.isArray(S[type]) && S[type].length ? S[type] : BT_STYLES_DEFAUT[type]) || [];
}
function btStyleDe(type, style){ const l = btStyles(type); return style && l.includes(style) ? style : (l[0] || ''); }
function btStyleNom(s){ return BT_STYLE_NOMS[s] || (s ? s[0].toUpperCase() + s.slice(1) : ''); }
function btImg(type, style, taille, cls){
  return `<img class="bt-px${cls ? ' ' + cls : ''}" src="batiments/${type}-${btStyleDe(type, style)}.svg" width="${taille}" height="${taille}" alt="" decoding="async">`;
}
const btFem = (type) => type !== 'centre';   // la Fonderie, la Forteresse, la Banque ; le Centre
function btMiens(){
  if(!BATIMENTS) return [];
  const l = [];
  mesFonderies().forEach(b => l.push(Object.assign({}, b, { type: 'fonderie' })));
  mesForteresses().forEach(b => l.push(Object.assign({}, b, { type: 'forteresse' })));
  if(BATIMENTS.banque) l.push(Object.assign({}, BATIMENTS.banque, { type: 'banque' }));
  if(BATIMENTS.centre) l.push(Object.assign({}, BATIMENTS.centre, { type: 'centre' }));
  return l;
}
function btEffetTexte(type, moi){
  if(type === 'fonderie') return `${(BATIMENTS && BATIMENTS.production) || 10} lingots par jour pour ${moi ? 'toi' : 'son propriétaire'}`;
  if(type === 'forteresse') return `−${btReglage('forteresse_defense', 15)} % aux chances de ceux qui l’attaquent, +${btReglage('forteresse_appui', 5)} % aux attaques autour`;
  if(type === 'banque') return `Une épargne : jusqu’à ${bqReglage('reserve', 60)} lingots, +${bqReglage('interet', 10)} % par nuit. Secrète`;
  return 'Il prépare une bombe. Le prendre fait perdre la bombe à son propriétaire';
}
function btEtatMien(b){
  if(btPretDans(b) > 0) return { t: `${btFem(b.type) ? 'Prête' : 'Prêt'} dans ${formatDuree(btPretDans(b))}`, c: 'cours' };
  if(b.type === 'fonderie') return { t: `+${(BATIMENTS && BATIMENTS.production) || 10} lingots par jour`, c: 'ok' };
  if(b.type === 'forteresse') return { t: `−${btReglage('forteresse_defense', 15)} % aux attaquants`, c: 'ok' };
  if(b.type === 'banque') return { t: `Secrète · ${Math.floor(Number(b.contenu) || 0)} lingots`, c: 'or' };
  return b.devoile ? { t: 'Dévoilé : bombe en préparation', c: 'rouge' } : { t: 'Secret', c: 'or' };
}
const CADENAS = '<svg class="bte-cad" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>';
// la case de Mon front
function mfoBatimentsHtml(){
  if(!BATIMENTS || !BATIMENTS.ouverts) return '';
  const l = btMiens(), enCours = l.filter(b => btPretDans(b) > 0).length;
  let neuf = false;
  try{ neuf = !localStorage.getItem('tf-bt-vu'); }catch(e){}
  const vign = l.slice(0, 6).map(b => `<span class="mfo-btv${btPretDans(b) > 0 ? ' cours' : ''}" title="${echapperTexte(btNom(b.type) + ', ' + (b.nom || ''))}">${btImg(b.type, b.style, 44)}</span>`).join('')
    + (l.length > 6 ? `<span class="mfo-btv plus">+${l.length - 6}</span>` : '');
  return `<div class="mfo-t mfo-clic mfo-bt${neuf ? ' neuf' : ''}" data-mfo="batiments" role="button" tabindex="0" aria-label="Voir mes bâtiments">
    <div class="mfo-h"><span>Mes bâtiments${neuf ? ' <em class="mfo-neuf">Nouveau</em>' : ''}</span><span class="mfo-lien">Tout voir ›</span></div>
    ${l.length ? `<div class="mfo-btl">${vign}</div><p class="mfo-p"><b>${l.length}</b> bâtiment${l.length > 1 ? 's' : ''}${enCours ? ` · ${enCours} en construction` : ''} · <b>${Math.floor(lingotsActuels() || 0)}</b> lingots</p>`
      : '<p class="mfo-p">Aucun bâtiment pour l’instant : ta première Fonderie est gratuite. Touche une de tes communes sur la carte pour la construire.</p>'}</div>`;
}
// l'écran Bâtiments
function btEcranEl(){
  let e = document.getElementById('btEcran');
  if(e) return e;
  e = document.createElement('div');
  e.id = 'btEcran'; e.className = 'bte'; e.hidden = true;
  e.setAttribute('role', 'dialog'); e.setAttribute('aria-modal', 'true'); e.setAttribute('aria-label', 'Bâtiments');
  e.innerHTML = `<div class="bte-boite">
    <div class="bte-haut"><button type="button" class="bte-retour" data-bte="fermer" aria-label="Retour">←</button><h2 class="bte-titre">Bâtiments</h2><span class="bte-lingots">${ICONE_LINGOT}<b data-bte-lingots></b></span></div>
    <div class="bte-seg" role="tablist" aria-label="Bâtiments"><button type="button" role="tab" data-bte-vue="miens"></button><button type="button" role="tab" data-bte-vue="autres"></button></div>
    <div class="bte-corps" data-bte-corps></div></div>`;
  document.body.appendChild(e);
  e.addEventListener('click', btEcranClic);
  e.addEventListener('input', btEcranSaisie);
  e.addEventListener('change', btEcranChoix);
  return e;
}
function btEcranOuvrir(vue){
  const e = btEcranEl();
  if(vue) BTE.vue = vue;
  try{ localStorage.setItem('tf-bt-vu', '1'); }catch(err){}
  e.hidden = false;
  document.documentElement.classList.add('bte-ouvert');
  requestAnimationFrame(() => e.classList.add('visible'));
  btEcranRendre();
  if(BTE.total == null && !BTE.charge) btAutresCharger(true);   // le compteur « Les autres »
}
function btEcranFermer(){
  const e = document.getElementById('btEcran');
  if(!e || e.hidden) return;
  e.classList.remove('visible'); e.hidden = true;
  document.documentElement.classList.remove('bte-ouvert');
  if(typeof mfoRendre === 'function') mfoRendre();
}
function btEcranOuvert(){ const e = document.getElementById('btEcran'); return !!(e && !e.hidden); }
function btEcranMajSeg(){
  const e = document.getElementById('btEcran');
  if(!e) return;
  const n = btMiens().length;
  const lg = e.querySelector('[data-bte-lingots]'); if(lg) lg.textContent = String(Math.floor(lingotsActuels() || 0));
  e.querySelectorAll('[data-bte-vue]').forEach(b => {
    const on = b.dataset.bteVue === BTE.vue;
    b.classList.toggle('on', on); b.setAttribute('aria-selected', String(on));
    b.textContent = b.dataset.bteVue === 'miens' ? `Les miens · ${n}` : `Les autres${BTE.totalSansFiltre != null ? ' · ' + BTE.totalSansFiltre : ''}`;
  });
}
function btEcranRendre(){
  const e = btEcranEl();
  btEcranMajSeg();
  const corps = e.querySelector('[data-bte-corps]');
  corps.innerHTML = BTE.vue === 'miens' ? btMiensHtml() : btAutresHtml();
  if(BTE.vue === 'autres') btAutresListeRendre();
}
function btMiensHtml(){
  const l = btMiens();
  if(!l.length) return '<p class="bte-vide">Aucun bâtiment pour l’instant. Ta première Fonderie est gratuite : touche une de tes communes sur la carte, puis « Construire la Fonderie ici ».</p>';
  return `<div class="bte-grille">${l.map((b, i) => {
    const e = btEtatMien(b);
    return `<button type="button" class="bte-tuile${btPretDans(b) > 0 ? ' cours' : ''}" data-bte-mien="${i}">
      <span class="bte-socle">${btImg(b.type, b.style, 72)}</span>
      <b>${btNom(b.type)}${b.type === 'banque' ? CADENAS : ''}</b>
      <small>${echapperHtml(btStyleNom(btStyleDe(b.type, b.style)))} · ${echapperHtml(b.nom || b.code)}${b.dept ? ' (' + echapperHtml(b.dept) + ')' : ''}</small>
      <small class="bte-e ${e.c}">${e.t}</small></button>`;
  }).join('')}</div>
  <p class="bte-note">Le style se choisit à la construction : 2 ou 3 au choix, gratuits. Changer de style : bientôt.</p>`;
}
function btAutresHtml(){
  const regions = [...new Set(Object.values(DEP_REGION))].sort((a, b) => a.localeCompare(b, 'fr'));
  const types = [['', 'Tous'], ['fonderie', 'Fonderies'], ['forteresse', 'Forteresses'], ['centre', 'Centres']];
  return `<div class="bte-outils">
    <div class="bte-recherche"><label class="bte-sr" for="bteRecherche">Rechercher un joueur ou une commune</label>
      <svg class="bte-loupe" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>
      <input id="bteRecherche" type="search" placeholder="Joueur ou commune" autocomplete="off" value="${echapperTexte(BTE.q)}"></div>
    <div class="bte-selects">
      <label class="bte-sel"><span>Région</span><select data-bte-region><option value="">Toutes</option>${regions.map(r => `<option value="${echapperTexte(r)}"${r === BTE.region ? ' selected' : ''}>${echapperHtml(r)}</option>`).join('')}</select></label>
      <label class="bte-sel"><span>Trier</span><select data-bte-tri>${[['recents', 'Les plus récents'], ['nom', 'Commune (A → Z)'], ['joueur', 'Joueur (A → Z)']].map(([k, n]) => `<option value="${k}"${k === BTE.tri ? ' selected' : ''}>${n}</option>`).join('')}</select></label>
    </div>
    <div class="bte-types" role="group" aria-label="Type de bâtiment">${types.map(([k, n]) => `<button type="button" class="bte-chip${BTE.type === k ? ' on' : ''}" aria-pressed="${BTE.type === k}" data-bte-type="${k}">${n}</button>`).join('')}</div>
    <p class="bte-secret">${CADENAS}<span>Les Banques sont secrètes : elles n’apparaissent jamais ici. Un Centre n’y apparaît qu’une fois dévoilé.</span></p>
  </div>
  <div class="bte-liste" data-bte-liste aria-live="polite"></div>`;
}
function btAutresListeRendre(){
  const el = document.querySelector('#btEcran [data-bte-liste]');
  if(!el) return;
  if(BTE.erreur){ el.innerHTML = `<p class="bte-vide">Impossible de charger la liste : ${echapperHtml(BTE.erreur)}</p>`; return; }
  if(!BTE.lignes.length){ el.innerHTML = `<p class="bte-vide">${BTE.charge ? 'Chargement…' : 'Aucun bâtiment ne correspond.'}</p>`; return; }
  const reste = Math.max(0, (Number(BTE.total) || 0) - BTE.lignes.length);
  el.innerHTML = `<div class="bte-l-boite">${BTE.lignes.map((x, i) => `<button type="button" class="bte-l" data-bte-fiche="${i}">
      <span class="bte-v${x.type === 'centre' ? ' rouge' : ''}">${btImg(x.type, x.style, 48)}</span>
      <span class="bte-t"><b>${x.type === 'centre' ? 'Centre dévoilé' : btNom(x.type)} · ${echapperHtml(btStyleNom(btStyleDe(x.type, x.style)))}</b>
        <small>${echapperHtml(x.pseudo || 'un joueur')} · ${echapperHtml(x.nom || x.code)}${x.dept ? ' (' + echapperHtml(x.dept) + ')' : ''}${x.type === 'centre' ? ` · <span class="bte-rouge">${x.centre === 'preparation' ? 'bombe en préparation' : 'a lancé sa bombe'}</span>` : ''}${x.pret === false ? ' · en construction' : ''}</small></span>
      <span class="bte-chev" aria-hidden="true">›</span></button>`).join('')}</div>
    ${reste ? `<button type="button" class="bte-plus" data-bte="plus"${BTE.charge ? ' disabled' : ''}>${BTE.charge ? 'Chargement…' : `Voir plus (${reste})`}</button>` : ''}`;
}
async function btAutresCharger(depuisDebut){
  const req = ++BTE.req;
  if(depuisDebut){ BTE.decalage = 0; BTE.lignes = []; }
  BTE.charge = true; BTE.erreur = '';
  btAutresListeRendre();
  const depts = BTE.region ? Object.keys(DEP_REGION).filter(d => DEP_REGION[d] === BTE.region) : null;
  let data = null, error = null;
  try{
    ({ data, error } = await sb.rpc('batiments_autres', { p_type: BTE.type || null, p_depts: depts, p_recherche: BTE.q || null,
      p_tri: BTE.tri, p_limite: 30, p_decalage: BTE.decalage }));
  }catch(e){ error = e; }
  if(req !== BTE.req) return;   // une recherche plus récente est partie
  BTE.charge = false;
  if(error || !data){ BTE.erreur = messageLisible((error && error.message) || 'réessaie dans un instant'); btAutresListeRendre(); return; }
  BTE.total = Number(data.total) || 0;
  if(!BTE.type && !BTE.region && !BTE.q) BTE.totalSansFiltre = BTE.total;
  BTE.lignes = BTE.lignes.concat(Array.isArray(data.lignes) ? data.lignes : []);
  BTE.decalage = BTE.lignes.length;
  btAutresListeRendre();
  btEcranMajSeg();
}
function btEcranClic(ev){
  const t = ev.target;
  if(t.closest('[data-bte="fermer"]')) return btEcranFermer();
  const v = t.closest('[data-bte-vue]');
  if(v){
    BTE.vue = v.dataset.bteVue; btEcranRendre();
    if(BTE.vue === 'autres' && !BTE.lignes.length && !BTE.charge) btAutresCharger(true);
    return;
  }
  const ty = t.closest('[data-bte-type]');
  if(ty){
    BTE.type = ty.dataset.bteType;
    document.querySelectorAll('#btEcran [data-bte-type]').forEach(b => { const on = b.dataset.bteType === BTE.type; b.classList.toggle('on', on); b.setAttribute('aria-pressed', String(on)); });
    btAutresCharger(true);
    return;
  }
  if(t.closest('[data-bte="plus"]')) return btAutresCharger(false);
  const m = t.closest('[data-bte-mien]');
  if(m){ const b = btMiens()[Number(m.dataset.bteMien)]; if(b) btFicheOuvrir(Object.assign({}, b, { moi: true })); return; }
  const f = t.closest('[data-bte-fiche]');
  if(f){ const x = BTE.lignes[Number(f.dataset.bteFiche)]; if(x) btFicheOuvrir(x); }
}
function btEcranSaisie(ev){
  if(ev.target.id !== 'bteRecherche') return;
  clearTimeout(BTE.minuteur);
  BTE.minuteur = setTimeout(() => { BTE.q = ev.target.value.trim(); btAutresCharger(true); }, 350);
}
function btEcranChoix(ev){
  if(ev.target.matches('[data-bte-region]')){ BTE.region = ev.target.value; btAutresCharger(true); }
  else if(ev.target.matches('[data-bte-tri]')){ BTE.tri = ev.target.value; btAutresCharger(true); }
}
document.addEventListener('keydown', (e) => {
  if(e.key !== 'Escape' || !btEcranOuvert()) return;
  const v = document.getElementById('pcVoile');
  if(v && !v.hidden) return;   // la fiche se ferme d'abord
  btEcranFermer();
});
// la fiche d'un bâtiment
function btFicheOuvrir(x){
  const moi = !!x.moi, type = x.type, style = btStyleDe(type, x.style);
  const commune = othersMap.get(x.code) || collectionMap.get(x.code);
  const peutAttaquer = !moi && othersMap.has(x.code) && !(commune && commune.joueurId && clanMembres.has(commune.joueurId));
  const date = x.cree_le ? new Date(x.cree_le).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' }) : '';
  const etat = moi ? btEtatMien(x) : null;
  pcOuvrir(`<div class="pc-poignee"></div>
    <div class="btf-socle">${btImg(type, style, 192, 'grand')}</div>
    <div class="btf-titre"><h3>${type === 'centre' && !moi ? 'Centre dévoilé' : btNom(type)}</h3><span class="btf-chip">Style ${echapperHtml(btStyleNom(style))}</span></div>
    <p class="btf-de">${moi ? 'à toi' : 'de <b>' + echapperHtml(x.pseudo || 'un joueur') + '</b>'}</p>
    <div class="btf-l"><span>Où</span><b>${echapperHtml(x.nom || x.code)}${x.dept ? ' (' + echapperHtml(x.dept) + ')' : ''}</b></div>
    <div class="btf-l"><span>Effet</span><span>${btEffetTexte(type, moi)}</span></div>
    ${etat ? `<div class="btf-l"><span>État</span><span class="bte-e ${etat.c}">${etat.t}</span></div>` : ''}
    ${!moi && x.pret === false ? '<div class="btf-l"><span>État</span><span>En construction</span></div>' : ''}
    ${date ? `<div class="btf-l"><span>${btFem(type) ? 'Construite' : 'Construit'}</span><span>le ${date}</span></div>` : ''}
    <div class="btf-act"><button type="button" class="pc-go" data-btf="carte" data-code="${echapperTexte(x.code)}">Voir sur la carte</button>${peutAttaquer ? `<button type="button" class="btf-att" data-btf="attaquer" data-code="${echapperTexte(x.code)}">Attaquer</button>` : ''}</div>
    <div class="pc-sec"><span></span><button type="button" data-pc-act="fermer">Fermer</button></div>`);
}
document.addEventListener('click', (e) => {
  const b = e.target.closest('[data-btf]');
  if(!b) return;
  const code = b.dataset.code, c = othersMap.get(code) || collectionMap.get(code);
  pcFermer(); btEcranFermer();
  if(!c) return;
  if(b.dataset.btf === 'carte'){ ncAller('front', 'territoire', () => voirCommuneSurCarte(c)); return; }
  if(b.dataset.btf === 'attaquer') ncAller('front', 'territoire', () => { voirCommuneSurCarte(c); setTimeout(() => { try{ ouvrirAttaque(code); }catch(err){} }, 450); });
});
// construire : le style d'abord
function btPrixTexte(type){
  const p = type === 'fonderie' ? (mesFonderies().length ? btReglage('fonderie2_prix', 30) : 0)
          : type === 'forteresse' ? btReglage('forteresse_prix', 20)
          : type === 'centre' ? btReglage('centre_prix', 40) : bqReglage('prix', 20);
  return Number(p) > 0 ? `${p} lingots` : 'gratuit';
}
function btStyleOuvrir(code, type){
  BTS.code = code; BTS.type = type; BTS.style = btStyles(type)[0];
  pcOuvrir(btStyleHtml());
}
function btStyleHtml(){
  const code = BTS.code, type = BTS.type, c = collectionMap.get(code) || {};
  const opts = btStyles(type).map(st => `<button type="button" class="bts-o${st === BTS.style ? ' on' : ''}" aria-pressed="${st === BTS.style}" data-bts="${echapperTexte(st)}">
      <span class="bts-v">${btImg(type, st, 72)}</span><b>${echapperHtml(btStyleNom(st))}</b><small>gratuit</small></button>`).join('');
  return `<div class="pc-poignee"></div>
    <div class="pc-kicker">${echapperHtml(c.nom || code)}${c.dept ? ' (' + echapperHtml(c.dept) + ')' : ''}</div>
    <div class="pc-titre">Construire ${btFem(type) ? 'une' : 'un'} ${btNom(type)}</div>
    <p class="bts-lab">Choisis son style</p>
    <div class="bts-g" role="group" aria-label="Style">${opts}</div>
    <div class="btf-l"><span>${btFem(type) ? 'Prête' : 'Prêt'} dans</span><b>${btReglage('construction_h', 6)} h</b></div>
    <div class="btf-l"><span>Effet</span><span>${btEffetTexte(type, true)}</span></div>
    <p class="bts-note">Le style ne change rien en jeu. D’autres styles arriveront plus tard, certains payants.</p>
    <button type="button" class="pc-go" data-bts-go>Construire · ${btPrixTexte(type)}</button>
    <div class="pc-sec"><span></span><button type="button" data-pc-act="fermer">Annuler</button></div>`;
}
document.addEventListener('click', (e) => {
  const o = e.target.closest('[data-bts]');
  if(o){ BTS.style = o.dataset.bts; const bx = document.getElementById('pcBoite'); if(bx) bx.innerHTML = btStyleHtml(); return; }
  const g = e.target.closest('[data-bts-go]');
  if(g && !g.disabled){ g.disabled = true; pcFermer(); batimentConstruire(BTS.code, BTS.type, BTS.style); }
});

// ---------- patch288 : « Mon front », le premier volet de Combat ----------"""

s = rep(s, "// ---------- patch288 : « Mon front », le premier volet de Combat ----------", BLOC)

# Mon front : la case, et le lien vers l'écran
s = rep(s, "  z.innerHTML = blocDanger + blocEnergie + blocAtt + blocCom + blocQ;",
           "  z.innerHTML = blocDanger + blocEnergie + blocAtt + mfoBatimentsHtml() + blocCom + blocQ;   // patch366")
s = rep(s, """function mfoVers(quoi, tier){
  const tab = (id) => { const t = document.querySelector(`.tab[data-tab="${id}"]`); if(t) t.click(); };""",
"""function mfoVers(quoi, tier){
  const tab = (id) => { const t = document.querySelector(`.tab[data-tab="${id}"]`); if(t) t.click(); };
  if(quoi === 'batiments') return btEcranOuvrir('miens');   // patch366""")

# les bâtiments rechargés : Mon front et l'écran suivent
s = rep(s, """    BATIMENTS_CARTE = carte;
    renderBatimentsBloc();""", """    BATIMENTS_CARTE = carte;
    renderBatimentsBloc();
    if(typeof mfoRendre === 'function') mfoRendre();   // patch366
    if(btEcranOuvert() && BTE.vue === 'miens') btEcranRendre();""")

# construire : le choix du style, puis la construction avec style
s = rep(s, """  if(quoi === 'bt-construire'){   // patch243 : deux temps, comme le retrait de garnison
    const t = b.dataset.bt;""", """  if(quoi === 'bt-construire'){   // patch243 : deux temps, comme le retrait de garnison
    const t = b.dataset.bt;
    if(BATIMENTS && BATIMENTS.styles && btStyles(t).length > 1){ btArme = null; btStyleOuvrir(code, t); return; }   // patch366 : le style d'abord""")
s = rep(s, """async function batimentConstruire(code, type){
  const nom = btNom(type);   // patch260, patch354
  const { error } = await sb.rpc('batiment_construire', { p_code: code, p_type: type });""",
"""async function batimentConstruire(code, type, style){
  const nom = btNom(type);   // patch260, patch354
  const { error } = style   // patch366 : avec son style (s2-112)
    ? await sb.rpc('batiment_construire_style', { p_code: code, p_type: type, p_style: style })
    : await sb.rpc('batiment_construire', { p_code: code, p_type: type });""")

F.write_text(s, encoding='utf-8')

# --- styles
C = pathlib.Path('style.css'); css = C.read_text(encoding='utf-8')
assert 'patch366' not in css
css += """
/* patch366 : les bâtiments en pixel art */
.bt-px{ display:block; image-rendering:pixelated; flex:none; }
.mfo-bt.neuf{ border-color:rgba(240,180,41,.6); }
.mfo-neuf{ font-style:normal; font-size:.66rem; font-weight:800; color:#1A1404; background:#F0B429; padding:2px 7px; border-radius:20px; margin-left:6px; vertical-align:2px; }
.mfo-btl{ display:flex; gap:6px; flex-wrap:wrap; }
.mfo-btv{ width:48px; height:48px; border-radius:10px; background:#1F3860; display:flex; align-items:center; justify-content:center; box-sizing:border-box; }
.mfo-btv.cours{ border:1px dashed #A9BCD4; }
.mfo-btv.cours .bt-px{ opacity:.45; }
.mfo-btv.plus{ font-weight:800; font-size:.85rem; color:#C9D3E3; }
html.bte-ouvert, html.bte-ouvert body{ overflow:hidden; }
.bte{ position:fixed; inset:0; z-index:48; display:flex; justify-content:center; background:rgba(4,9,18,.72); opacity:0; transition:opacity .18s ease; }
.bte[hidden]{ display:none; }
.bte.visible{ opacity:1; }
.bte-boite{ width:100%; max-width:760px; height:100%; overflow:auto; background:var(--nuit, #0F1F38); color:#EAF1F8; box-sizing:border-box;
  padding:calc(12px + env(safe-area-inset-top)) 16px calc(24px + env(safe-area-inset-bottom)); }
@media (min-width:721px){ .bte{ align-items:center; } .bte-boite{ height:auto; max-height:88vh; border-radius:18px; border:1px solid rgba(169,188,212,.2); padding:16px 20px 22px; } }
.bte-haut{ display:flex; align-items:center; gap:12px; margin-bottom:12px; }
.bte-retour{ width:44px; height:44px; flex:none; border-radius:12px; border:1px solid rgba(169,188,212,.25); background:#13284A; color:#EAF1F8; font-size:20px; cursor:pointer; }
.bte-titre{ flex:1; margin:0; font-family:'Big Shoulders Display', Impact, sans-serif; font-weight:800; font-size:30px; line-height:1; }
.bte-lingots{ display:inline-flex; align-items:center; gap:6px; padding:8px 12px; border-radius:12px; background:#13284A; border:1px solid rgba(169,188,212,.25); font-weight:700; }
.bte-seg{ display:grid; grid-template-columns:1fr 1fr; gap:2px; padding:3px; border-radius:12px; background:#13284A; border:1px solid rgba(169,188,212,.25); margin-bottom:12px; }
.bte-seg button{ min-height:40px; border:0; border-radius:9px; background:transparent; color:#A9BCD4; font:inherit; font-size:.92rem; font-weight:600; cursor:pointer; }
.bte-seg button.on{ background:#F0B429; color:#1A1404; font-weight:800; }
.bte-grille{ display:grid; grid-template-columns:repeat(auto-fill, minmax(150px, 1fr)); gap:10px; }
.bte-tuile{ display:flex; flex-direction:column; gap:3px; padding:10px; border-radius:16px; border:1px solid rgba(169,188,212,.18); background:rgba(169,188,212,.06); color:#EAF1F8; font:inherit; text-align:left; cursor:pointer; }
.bte-tuile.cours{ border-style:dashed; }
.bte-tuile.cours .bt-px{ opacity:.45; }
.bte-tuile b{ font-size:.95rem; display:flex; align-items:center; gap:6px; margin-top:5px; }
.bte-tuile small{ font-size:.8rem; color:#A9BCD4; line-height:1.3; }
.bte-socle{ height:88px; border-radius:12px; background:#1F3860; display:flex; align-items:center; justify-content:center; }
.bte-e{ font-weight:700; }
.bte-e.ok{ color:#7FE3B4 !important; } .bte-e.or{ color:#F0B429 !important; } .bte-e.rouge{ color:#FF9A94 !important; } .bte-e.cours{ color:#A9BCD4 !important; }
.bte-cad{ width:14px; height:14px; color:#F0B429; flex:none; }
.bte-note, .bte-vide{ font-size:.82rem; color:#A9BCD4; line-height:1.4; margin:12px 2px 0; }
.bte-outils{ display:flex; flex-direction:column; gap:8px; margin-bottom:10px; }
.bte-sr{ position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; }
.bte-recherche{ position:relative; }
.bte-recherche input{ width:100%; box-sizing:border-box; min-height:44px; border-radius:12px; border:1px solid rgba(169,188,212,.3); background:#13284A; color:#EAF1F8; font:inherit; font-size:16px; padding:0 12px 0 40px; }
.bte-recherche input::placeholder{ color:#8DA2BD; }
.bte-loupe{ position:absolute; left:13px; top:50%; transform:translateY(-50%); color:#A9BCD4; pointer-events:none; }
.bte-selects{ display:grid; grid-template-columns:1fr 1fr; gap:8px; }
.bte-sel{ display:flex; flex-direction:column; gap:3px; font-size:.72rem; color:#A9BCD4; min-width:0; }
.bte-sel select{ width:100%; min-width:0; min-height:44px; border-radius:12px; border:1px solid rgba(169,188,212,.3); background:#13284A; color:#EAF1F8; font:inherit; font-size:15px; padding:0 10px; }
.bte-types{ display:flex; gap:6px; overflow-x:auto; scrollbar-width:none; }
.bte-chip{ min-height:38px; padding:0 13px; border-radius:19px; border:1px solid rgba(169,188,212,.25); background:#13284A; color:#EAF1F8; font:inherit; font-size:.82rem; font-weight:600; cursor:pointer; white-space:nowrap; }
.bte-chip.on{ background:#F0B429; border-color:#F0B429; color:#1A1404; font-weight:800; }
.bte-secret{ display:flex; align-items:center; gap:8px; margin:2px 0 0; font-size:.78rem; color:#A9BCD4; line-height:1.35; }
.bte-l-boite{ border-radius:16px; border:1px solid rgba(169,188,212,.18); background:rgba(169,188,212,.05); padding:2px 12px; }
.bte-l{ width:100%; display:flex; align-items:center; gap:12px; padding:9px 0; border:0; border-bottom:1px solid rgba(169,188,212,.14); background:transparent; color:#EAF1F8; font:inherit; text-align:left; cursor:pointer; }
.bte-l:last-child{ border-bottom:0; }
.bte-v{ width:52px; height:52px; flex:none; border-radius:10px; background:#1F3860; display:flex; align-items:center; justify-content:center; box-sizing:border-box; }
.bte-v.rouge{ border:1px solid rgba(229,72,77,.7); }
.bte-t{ flex:1; min-width:0; display:flex; flex-direction:column; gap:2px; }
.bte-t b{ font-size:.92rem; }
.bte-t small{ font-size:.8rem; color:#A9BCD4; }
.bte-rouge{ color:#FF9A94; font-weight:600; }
.bte-chev{ color:#A9BCD4; font-size:1.2rem; }
.bte-plus{ display:block; width:100%; margin-top:10px; min-height:44px; border-radius:12px; border:1px solid rgba(240,180,41,.6); background:transparent; color:#FFD36B; font:inherit; font-weight:700; cursor:pointer; }
.btf-socle{ height:208px; border-radius:16px; background:#1F3860; display:flex; align-items:center; justify-content:center; margin:6px 0 12px; }
.btf-titre{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.btf-titre h3{ margin:0; font:900 1.9rem/1 var(--titre); }
.btf-chip{ font-size:.78rem; font-weight:700; padding:3px 10px; border-radius:20px; background:#1F3860; border:1px solid #4A6A96; }
.btf-de{ margin:4px 0 8px; color:#A9BCD4; font-size:.92rem; }
.btf-de b{ color:#fff; }
.btf-l{ display:flex; justify-content:space-between; gap:12px; padding:9px 0; border-bottom:1px solid rgba(169,188,212,.14); font-size:.86rem; }
.btf-l > span:first-child{ color:#A9BCD4; flex:none; }
.btf-l > span:last-child, .btf-l > b{ text-align:right; }
.btf-act{ display:grid; grid-template-columns:1.4fr 1fr; gap:8px; margin-top:14px; }
.btf-act .pc-go{ font-size:1.05rem; }
.btf-act .pc-go:only-child{ grid-column:1 / -1; }
.btf-att{ border-radius:13px; border:1px solid #E5484D; background:transparent; color:#FF9A94; font:inherit; font-weight:800; cursor:pointer; min-height:48px; }
.bts-lab{ margin:12px 0 8px; font-size:.88rem; font-weight:700; }
.bts-g{ display:grid; grid-template-columns:repeat(auto-fit, minmax(96px, 1fr)); gap:8px; }
.bts-o{ position:relative; display:flex; flex-direction:column; gap:3px; padding:6px; border-radius:14px; border:1px solid rgba(169,188,212,.25); background:#1A3255; color:#EAF1F8; font:inherit; text-align:left; cursor:pointer; }
.bts-o.on{ border:2px solid #F0B429; padding:5px; }
.bts-o b{ font-size:.85rem; } .bts-o small{ font-size:.74rem; color:#A9BCD4; }
.bts-v{ height:88px; border-radius:10px; background:#1F3860; display:flex; align-items:center; justify-content:center; }
.bts-note{ margin:10px 0 12px; font-size:.8rem; color:#A9BCD4; line-height:1.4; }
"""
C.write_text(css, encoding='utf-8')
print('patch366 appliqué')
