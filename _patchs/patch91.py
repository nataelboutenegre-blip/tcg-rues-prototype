# -*- coding: utf-8 -*-
u"""
patch91 — Le Front de la saison 2 côté jeu (CACHÉ tant que SAISON2 = false).
Aperçus « navigation.png » et « garnison-apercu.png » validés le 9 octobre.

Avec SAISON2 = true :
- Tirage du Front : plus de bouton d'achat, plus de puces « achetés » et
  « solde » (paquets gratuits seulement) ;
- Combat : jauge d'énergie en tête (énergie, prochaine recharge, plein dans) ;
  les intensités et les assauts affichent leur coût en énergie ; plus de
  puce « Solde » ;
- assaut : coût en énergie ; « la garnison a annulé ta victoire » quand le
  serveur renvoie une victoire annulée ; à la conquête, les points Terra
  réellement gagnés (lus sur le solde : plafond et dégressif compris) ;
- garnison : bloc sur la fiche de ses communes (jauge, +1, +5, retirer en
  deux temps), « Mettre en garnison » sinon ; volet Défendre « Mes
  garnisons » avec recharge et récit des 24 h ; encadré « Commune en
  garnison » dans le panneau d'attaque ;
- plus de boucliers, d'échange ni de vente depuis la fiche d'une commune du
  Front ; section Boucliers cachée.
Serveur : s2-6-front.sql et s2-7-garnison.sql (fermés tant que la saison 2
n'est pas ouverte).
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
assert 'garnisonsMoi' not in js, u'patch91 deja applique'

# --- etat du Front ---------------------------------------------------------------------
js = rempl(js, u"let terraDernier = null;           // le dernier paquet ouvert, pour le bilan\n",
           u"""let terraDernier = null;           // le dernier paquet ouvert, pour le bilan
// patch91 : Front
const ENERGIE_INTENSITE = { prudente: 1, normale: 2, offensive: 3 };
let garnisonsMoi = new Map();      // code -> { energie, nom, tier, attaquants, repousses, subis }
let energieEtat = null;            // { energie, prochaine_dans, lu }
let gnRetraitArme = null;          // code de la garnison dont le retrait attend confirmation
const coutTexte = (n) => SAISON2 ? `${n} énergie` : `${Number(n).toLocaleString('fr-FR')} pts`;
const coutIntensiteTexte = (i) => SAISON2 ? `${ENERGIE_INTENSITE[i.id]} énergie`
  : (i.facteur === 1 ? 'prix normal' : (i.facteur < 1 ? 'un tiers du prix' : 'prix doublé'));
""", 'etat Front')

# --- energie : jauge + bascule ------------------------------------------------------------
js = rempl(js, u"""  const { data, error } = await sb.rpc('front_energie');
  if(error || !data || !data[0]) return;
  const el = document.getElementById('mbEnergie');
  if(el) el.textContent = data[0].energie;
}""",
           u"""  const { data, error } = await sb.rpc('front_energie');
  if(error || !data || !data[0]) return;
  const el = document.getElementById('mbEnergie');
  if(el) el.textContent = data[0].energie;
  energieEtat = { energie: Number(data[0].energie), prochaine_dans: data[0].prochaine_dans, lu: Date.now() };
  renderJaugeEnergie();
}

function renderJaugeEnergie(){
  const el = document.getElementById('jaugeEnergie');
  if(!el || !energieEtat) return;
  const e = energieEtat.energie, max = 40;
  const manque = Math.max(0, max - e);
  const prochaineMin = energieEtat.prochaine_dans != null ? Math.max(1, Math.ceil(energieEtat.prochaine_dans / 60)) : null;
  const pleinMin = manque > 0 && prochaineMin != null ? prochaineMin + (manque - 1) * 10 : 0;
  const duree = (m) => m >= 60 ? Math.floor(m / 60) + ' h ' + String(m % 60).padStart(2, '0') : m + ' min';
  el.innerHTML = `<div class="je-titre">${ICONE_ENERGIE} Énergie</div>
    <div class="je-haut"><b>${e} <small>/ ${max}</small></b><span>${e >= max ? 'Réserve pleine' : `+1 dans ${prochaineMin} min · pleine dans ${duree(pleinMin)}`}</span></div>
    <div class="je-barre">${Array.from({ length: max }, (_, i) => `<i class="${i < e ? 'p' : ''}"></i>`).join('')}</div>
    <p class="je-note">L'énergie se recharge seule : +1 toutes les 10 minutes.</p>`;
}""", 'majEnergie')

# --- initModes : jauge, garnisons, textes du Front ---------------------------------------
js = rempl(js, u"""  appliquerMode();
  majEnergie();
  if(!energieTimer) energieTimer = setInterval(majEnergie, 60000);
}""",
           u"""  appliquerMode();
  majEnergie();
  if(!energieTimer) energieTimer = setInterval(majEnergie, 60000);
  // patch91 : la jauge d'energie en tete de Combat, les garnisons dans Defendre
  const combat = document.getElementById('panel-combat');
  if(combat && !document.getElementById('jaugeEnergie')){
    const j = document.createElement('div');
    j.id = 'jaugeEnergie';
    j.className = 'jauge-energie';
    combat.querySelector('.volets').insertAdjacentElement('afterend', j);
  }
  const defense = document.getElementById('panel-defense');
  if(defense && !document.getElementById('garnisonsBloc')){
    const sub = defense.querySelector('.sub');
    if(sub) sub.textContent = 'Quand un joueur gagne un round contre toi, tente une défense (1 énergie). Tes garnisons, elles, se défendent toutes seules.';
    const g = document.createElement('div');
    g.id = 'garnisonsBloc';
    g.className = 'garnisons-bloc';
    const sect = defense.querySelector('.bourse-section');
    if(sect) sect.insertAdjacentElement('beforebegin', g); else defense.appendChild(g);
    g.addEventListener('click', (e) => {
      const b = e.target.closest('[data-gn-recharger]');
      if(b) garnisonAction(b.dataset.gnRecharger, 5);
    });
  }
  chargerGarnisons();
}

// ---------- patch91 : garnisons ----------
async function chargerGarnisons(){
  if(!SAISON2) return;
  const { data, error } = await sb.rpc('mes_garnisons');
  if(error){ console.error(error); return; }
  garnisonsMoi = new Map((data || []).map(g => [g.commune_code, {
    energie: Number(g.energie) || 0, nom: g.nom, tier: g.tier, attaquants: g.attaquants,
    repousses: g.repousses_24h, subis: g.subis_24h }]));
  renderGarnisons();
}

function renderGarnisons(){
  const el = document.getElementById('garnisonsBloc');
  if(!el) return;
  const liste = [...garnisonsMoi.entries()];
  const barre = (n) => `<span class="gl-barre">${Array.from({ length: 10 }, (_, i) => `<i class="${i < n ? 'p' : ''}"></i>`).join('')}</span>`;
  const recits = liste.filter(([, g]) => g.subis > 0).map(([, g]) =>
    `<div class="gn-badge">${ICONES_PC.bouclier}<span>Ta garnison ${deCommune(g.nom).startsWith("d'") ? 'd’' : 'de '}<b>${echapperTexte(g.nom)}</b> a repoussé <b>${g.repousses} assaut${g.repousses > 1 ? 's' : ''} sur ${g.subis}</b> en 24 h (−${g.subis} énergie).</span></div>`).join('');
  el.innerHTML = `<h2>Mes garnisons · ${liste.length} / 3</h2>
    ${liste.map(([code, g]) => {
      const tier = TIERS.find(t => t.id === g.tier) || TIERS[TIERS.length - 1];
      return `<div class="gl"><i class="gl-c ${tier.id}"></i><div class="gl-t"><b>${echapperTexte(g.nom)}</b>
        <span>${tier.label} · ${g.attaquants > 0 ? 'attaquée' : 'calme'} · ${g.energie} / 10</span>${barre(g.energie)}</div>
        <button class="gl-r" data-gn-recharger="${code}" ${g.energie >= 10 ? 'disabled' : ''}>Recharger</button></div>`;
    }).join('')}
    ${liste.length < 3 ? `<p class="gl-vide">${3 - liste.length} place${liste.length < 2 ? 's' : ''} libre${liste.length < 2 ? 's' : ''} : ouvre une de tes communes sur la carte et choisis « Mettre en garnison ».</p>` : ''}
    ${recits}`;
}

async function garnisonAction(code, n){
  const rpc = n === 'retirer' ? sb.rpc('garnison_retirer', { p_code: code }) : sb.rpc('garnison_poser', { p_code: code, p_n: n });
  const { data, error } = await rpc;
  if(error){ notifier({ type: 'erreur', titre: 'Garnison', texte: messageLisible(error.message) }); return; }
  const r = data && data[0];
  if(n === 'retirer') notifier({ type: 'info', titre: 'Garnison retirée', texte: `${r ? r.rendue : 0} énergie te revient.` });
  await Promise.all([chargerGarnisons(), majEnergie()]);
  if(panneauCommune === code && collectionMap.get(code)){
    const a = panneauAncre;
    ouvrirPanneau(code, a ? a.x : 40, a ? a.y : 40);
  }
}

function blocGarnisonFiche(code){
  const g = garnisonsMoi.get(code);
  if(!g) return '';
  const armee = gnRetraitArme === code;
  return `<div class="gn">
    <div class="gn-haut">${ICONES_PC.bouclier} Garnison <b>${ICONE_ENERGIE} ${g.energie} / 10</b></div>
    <div class="gn-barre">${Array.from({ length: 10 }, (_, i) => `<i class="${i < g.energie ? 'p' : ''}"></i>`).join('')}</div>
    <p class="gn-txt">Quand un attaquant gagne un round ici, ta garnison tente de l'annuler (1 chance sur 2) et dépense 1 énergie.</p>
    <div class="gn-btns">
      <button data-pc="gn-plus" data-n="1" ${g.energie >= 10 ? 'disabled' : ''}>+1 ${ICONE_ENERGIE}</button>
      <button data-pc="gn-plus" data-n="5" ${g.energie >= 10 ? 'disabled' : ''}>+5 ${ICONE_ENERGIE}</button>
      <button class="sec ${armee ? 'arme' : ''}" data-pc="gn-retirer">${armee ? `Confirmer (+${Math.floor(g.energie / 2)})` : 'Retirer'}</button>
    </div></div>`;
}""", 'initModes + garnisons')

# --- fiche d'une commune : garnison, plus de bouclier / echange / vente en S2 ----------------------
js = rempl(js, u"""  if(mienne && enVente == null) actions.push(['', 'vente', 'Mettre en vente', 'Vendre ' + c.nom]);
""",
           u"""  if(mienne && enVente == null) actions.push(['', 'vente', 'Mettre en vente', 'Vendre ' + c.nom]);
  // patch91 : en saison 2, le Front n'a ni bouclier, ni echange, ni vente ; il a la garnison
  let gnBloc = '';
  if(SAISON2){
    for(let i = actions.length - 1; i >= 0; i--)
      if(['bouclier', 'echange', 'voir-echange', 'vente'].includes(actions[i][1])) actions.splice(i, 1);
    for(let i = lignes.length - 1; i >= 0; i--)
      if(lignes[i][0] === 'Bouclier' || lignes[i][0] === 'En vente') lignes.splice(i, 1);
    if(mienne){
      gnBloc = blocGarnisonFiche(code);
      if(!gnBloc) actions.push(['', 'gn-poser', `Mettre en garnison <span class="pc-gn-nb">${garnisonsMoi.size} / 3</span>`, 'Défense automatique sur ' + c.nom]);
    }
  }
""", 'fiche actions')
js = rempl(js, u"    ${alerte}\n", u"    ${alerte}\n    ${gnBloc}\n", 'fiche gnBloc')
js = rempl(js, u"ICONES_PC['voir-echange'] = ICONES_PC.echange;\n",
           u"ICONES_PC['voir-echange'] = ICONES_PC.echange;\nICONES_PC['gn-poser'] = ICONES_PC.bouclier;\n", 'icone garnison')
js = rempl(js, u"  if(quoi === 'assaut'){ lancerAssaut(code); return; }\n",
           u"""  if(quoi === 'assaut'){ lancerAssaut(code); return; }
  if(quoi === 'gn-plus'){ gnRetraitArme = null; garnisonAction(code, Number(b.dataset.n) || 1); return; }
  if(quoi === 'gn-poser'){
    const dispo = energieEtat ? Math.floor(energieEtat.energie) : 5;
    garnisonAction(code, Math.max(1, Math.min(5, dispo)));
    return;
  }
  if(quoi === 'gn-retirer'){
    if(gnRetraitArme !== code){ gnRetraitArme = code; const a = panneauAncre; ouvrirPanneau(code, a ? a.x : 40, a ? a.y : 40); return; }
    gnRetraitArme = null;
    garnisonAction(code, 'retirer');
    return;
  }
""", 'clics garnison')

# --- panneau d'attaque : garnison visible, cout en energie -----------------------------------------
js = rempl(js, u"""  const [apercu, siege] = await Promise.all([
    sb.rpc('apercu_attaque', { p_commune_code: code, p_intensite: intensiteChoisie }),
    sb.from('sieges').select('victoires_consecutives, dernier_round')
      .eq('attacker_id', uid).eq('commune_code', code).maybeSingle(),
  ]);""",
           u"""  const [apercu, siege, gnv] = await Promise.all([
    sb.rpc('apercu_attaque', { p_commune_code: code, p_intensite: intensiteChoisie }),
    sb.from('sieges').select('victoires_consecutives, dernier_round')
      .eq('attacker_id', uid).eq('commune_code', code).maybeSingle(),
    SAISON2 ? sb.rpc('garnisons_visibles', { p_codes: [code] }) : Promise.resolve({ data: [] }),
  ]);
  attaqueEnGarnison = !!(gnv && Array.isArray(gnv.data) && gnv.data.length);""", 'attaque garnison visible')
js = rempl(js, u"let attaqueEnCours = false;\n",
           u"let attaqueEnCours = false;\nlet attaqueEnGarnison = false;   // patch91 : la cible ouverte est-elle en garnison\n", 'etat attaque')
js = rempl(js, u"""      <span>${i.label}</span><small>${i.facteur === 1 ? 'prix normal' : (i.facteur < 1 ? '⅓ du prix' : 'prix doublé')}</small>""",
           u"""      <span>${i.label}</span><small>${SAISON2 ? coutIntensiteTexte(i) : (i.facteur === 1 ? 'prix normal' : (i.facteur < 1 ? '⅓ du prix' : 'prix doublé'))}</small>""",
           'pc-int')
js = rempl(js, u"""    <div class="pc-prox ${a.a_distance ? 'loin' : ''}">""",
           u"""    ${attaqueEnGarnison ? `<div class="gn-badge">${ICONES_PC.bouclier}<span><b>Commune en garnison.</b> Chaque victoire peut être annulée par une défense automatique (1 chance sur 2).</span></div>` : ''}
    <div class="pc-prox ${a.a_distance ? 'loin' : ''}">""", 'badge attaquant')
js = rempl(js, u"`Lancer l’assaut — ${a.cout} pts`", u"`Lancer l’assaut — ${coutTexte(a.cout)}`", 'cout assaut panneau')

# --- grille de Combat et intensites --------------------------------------------------------------------
js = rempl(js, u"function coutIntensite(tierId, id){\n",
           u"function coutIntensite(tierId, id){\n  if(SAISON2) return ENERGIE_INTENSITE[intensite(id).id] || 2;\n", 'coutIntensite')
js = rempl(js, u"    if(prix) prix.textContent = v.cout + ' pts';", u"    if(prix) prix.textContent = coutTexte(v.cout);", 'appliquerChances')
js = rempl(js, u"Attaquer <b>${cout} pts</b>", u"Attaquer <b>${coutTexte(cout)}</b>", 'bouton cible')
js = rempl(js, u"""      <span class="int-cout">${i.facteur === 1 ? 'prix normal' : (i.facteur < 1 ? 'un tiers du prix' : 'prix doublé')}</span>""",
           u"""      <span class="int-cout">${coutIntensiteTexte(i)}</span>""", 'renderIntensite')
js = rempl(js, u"""      <span class="int-chances">${ecartIntensite(i)}</span>""",
           u"""      <span class="int-chances">${SAISON2 ? i.chances + ' %' : ecartIntensite(i)}</span>""", 'chances en clair')

# --- la mise en scene de l'assaut ---------------------------------------------------------------------------
js = rempl(js, u"""  const res = r.conquise ? 'conq' : (r.gagne ? 'ok' : 'ko');""",
           u"""  const res = r.conquise ? 'conq' : (r.gagne ? 'ok' : 'ko');
  // patch91 : une victoire annulee par la garnison revient perdue mais avec une serie intacte
  const parGarnison = SAISON2 && !r.gagne && !r.conquise && Number(r.victoires_consecutives) > 0;
  const soldeAvant = packStatusCache ? Number(packStatusCache.solde) : null;
  if(SAISON2) setTimeout(majEnergie, 300);""", 'scene etat')
js = rempl(js, u"""<span>Coût : <b class="blanc">${Number(r.cout).toLocaleString('fr-FR')} pts</b></span>""",
           u"""<span>Coût : <b class="blanc">${coutTexte(r.cout)}</b></span>""", 'scene cout')
js = rempl(js, u"""      v.className = 'as-verdict ko'; v.textContent = 'Repoussé';
      bl.forEach(b => b.className = 'perdu');""",
           u"""      v.className = 'as-verdict ko'; v.textContent = parGarnison ? 'Annulé par la garnison' : 'Repoussé';
      bl.forEach((b, i) => b.className = parGarnison ? (i < Number(r.victoires_consecutives) ? 'gagne' : '') : 'perdu');""", 'scene garnison 1')
js = rempl(js, u"""      d.innerHTML = `${nomCible} tient bon : ta série repart à zéro.`;""",
           u"""      d.innerHTML = parGarnison
        ? `La garnison ${deCommune(nomCible)} a annulé ta victoire : ta série reste à ${Number(r.victoires_consecutives)} sur 3.`
        : `${nomCible} tient bon : ta série repart à zéro.`;""", 'scene garnison 2')
js = rempl(js, u"""      d.innerHTML = `+${bonus.toLocaleString('fr-FR')} pts de bonus · protégée 3 h · revente au jeu dans 12 h`
        + (mon ? `<span class="as-mon">${ICONE_MONUMENT}Monument conquis : <b>${echapperTexte(mon.nom)}</b></span>` : '');""",
           u"""      d.innerHTML = (SAISON2 ? `<span class="as-gain">Points Terra : calcul…</span> · protégée 3 h`
                             : `+${bonus.toLocaleString('fr-FR')} pts de bonus · protégée 3 h · revente au jeu dans 12 h`)
        + (mon ? `<span class="as-mon">${ICONE_MONUMENT}Monument conquis : <b>${echapperTexte(mon.nom)}</b></span>` : '');
      if(SAISON2 && soldeAvant != null){
        // le gain reel (plafond du jour, reprise, degressif) se lit sur le solde
        sb.rpc('statut_paquets').then(({ data }) => {
          const g = fen.querySelector('.as-gain');
          if(!g || !data || !data[0]) return;
          const gain = Number(data[0].solde) - soldeAvant;
          g.textContent = gain > 0 ? `+${gain.toLocaleString('fr-FR')} points Terra` : 'Aucun point Terra (plafond du jour ou reprise)';
        });
      }""", 'scene conquete')

# --- defense : cout en energie ----------------------------------------------------------------------------------
js = rempl(js, u"""texte: `L'attaquant garde ses victoires (−${r ? r.cout : ''} pts).` });""",
           u"""texte: `L'attaquant garde ses victoires (−${r ? coutTexte(r.cout) : ''}).` });""", 'defense cout')
js = rempl(js, u"""    await loadMenaces();
    loadPackStatus();
    if(packStatusCache){
      ['soldeValueCombat', 'soldeValueDefense'].forEach(id => {""",
           u"""    await loadMenaces();
    loadPackStatus();
    if(SAISON2) majEnergie();
    if(packStatusCache){
      ['soldeValueCombat', 'soldeValueDefense'].forEach(id => {""", 'defense energie')

# --- en changeant de mode, le statut des paquets se recharge toujours (meme si le premier chargement a echoue)
js = rempl(js, u"  if(packStatusCache) loadPackStatus();\n  viderBilanTerra();",
           u"  loadPackStatus();\n  viderBilanTerra();", 'statut a chaque changement de mode')

# --- Tirage du Front : paquets gratuits seulement ---------------------------------------------------------------
js = rempl(js, u"""  puces.push(`<span class="puce">Achetés aujourd'hui <b>${achetesJour} sur 5</b></span>`);
  puces.push(`<span class="puce solde">Solde <b>${Number(packStatusCache.solde).toLocaleString('fr-FR')}</b></span>`);""",
           u"""  if(!SAISON2 || enTerra()){
    puces.push(`<span class="puce">Achetés aujourd'hui <b>${achetesJour} sur 5</b></span>`);
    puces.push(`<span class="puce solde">Solde <b>${Number(packStatusCache.solde).toLocaleString('fr-FR')}</b></span>`);
  }""", 'puces Front')

# --- en ouvrant Defendre : les garnisons a jour -------------------------------------------------------------------
js = rempl(js, u"    if(tab.dataset.tab === 'defense'){ loadMenaces().then(loadReveil); loadCombat(); renderIntensite('defense'); }\n",
           u"    if(tab.dataset.tab === 'defense'){ loadMenaces().then(loadReveil); loadCombat(); renderIntensite('defense'); if(SAISON2) chargerGarnisons(); }\n    if(tab.dataset.tab === 'combat' && SAISON2) majEnergie();\n",
           'onglet defense')

ecrire('app.js', js)

# =============================================================================
css = lire('style.css')
assert 'jauge-energie' not in css, u'patch91 deja applique (css)'
css += u'''
/* =====================================================================
   patch91 — Front de la saison 2 : energie, garnison (n'existe qu'avec SAISON2)
   ===================================================================== */
body.mode-front #openBuyBtn{ display:none !important; }
body.mode-front #panel-combat .puce.solde, body.mode-front #panel-defense .puce.solde{ display:none !important; }
body.mode-front #panel-defense .bourse-section{ display:none !important; }
.jauge-energie{ width:100%; max-width:560px; min-width:0; background:rgba(169,188,212,.07); border:1px solid rgba(169,188,212,.16);
  border-radius:14px; padding:14px; margin:0 0 14px; }
.jauge-energie:empty{ display:none; }
.je-titre{ display:flex; align-items:center; gap:6px; color:#FF8A8E; font-weight:600; font-size:.8rem; text-transform:uppercase; letter-spacing:.06em; margin-bottom:6px; }
.je-titre svg{ width:14px; height:14px; }
.je-haut{ display:flex; align-items:baseline; justify-content:space-between; gap:10px; color:#fff; }
.je-haut b{ font-family:var(--titre); font-weight:900; font-size:2rem; line-height:1; }
.je-haut b small{ font-size:1rem; color:var(--brume); font-weight:700; }
.je-haut span{ color:var(--brume); font-size:.8rem; text-align:right; }
.je-barre{ display:grid; grid-template-columns:repeat(40,1fr); gap:2px; margin-top:10px; }
.je-barre i{ height:10px; border-radius:2px; background:rgba(169,188,212,.16); }
.je-barre i.p{ background:linear-gradient(180deg,#FF9A7A,#E5484D); }
.je-note{ margin:8px 0 0; font-size:.74rem; color:var(--brume); }
.gn{ margin-top:11px; padding:10px 11px; border-radius:11px; background:linear-gradient(160deg,rgba(229,72,77,.14),rgba(229,72,77,.05)); border:1px solid rgba(229,72,77,.35); }
.gn-haut{ display:flex; align-items:center; gap:7px; color:#FFB3B5; font-weight:700; font-size:.8rem; text-transform:uppercase; letter-spacing:.06em; }
.gn-haut svg{ width:16px; height:16px; }
.gn-haut b{ margin-left:auto; color:#fff; font-size:.95rem; letter-spacing:0; display:flex; align-items:center; gap:3px; }
.gn-haut b svg{ width:13px; height:13px; color:#FF8A8E; }
.gn-barre{ display:grid; grid-template-columns:repeat(10,1fr); gap:3px; margin:8px 0 6px; }
.gn-barre i{ height:8px; border-radius:2px; background:rgba(169,188,212,.16); }
.gn-barre i.p{ background:linear-gradient(180deg,#FF9A7A,#E5484D); }
.gn-txt{ font-size:.72rem; color:#C9B4B6; line-height:1.4; margin:0; }
.gn-btns{ display:flex; gap:6px; margin-top:9px; }
.gn-btns button{ flex:1; border-radius:9px; border:1px solid rgba(229,72,77,.45); background:rgba(229,72,77,.14); color:#fff; font:inherit;
  font-size:.8rem; font-weight:600; padding:8px 4px; display:flex; align-items:center; justify-content:center; gap:4px; cursor:pointer; }
.gn-btns button:disabled{ opacity:.45; cursor:default; }
.gn-btns button svg{ width:12px; height:12px; color:#FF8A8E; }
.gn-btns button.sec{ background:none; border-color:rgba(169,188,212,.25); color:var(--brume); font-weight:500; }
.gn-btns button.sec.arme{ border-color:#E5484D; color:#fff; background:rgba(229,72,77,.25); }
.gn-badge{ display:flex; align-items:flex-start; gap:8px; margin-top:10px; padding:9px 10px; border-radius:10px; background:rgba(229,72,77,.1);
  border:1px solid rgba(229,72,77,.3); font-size:.76rem; color:#F3D6D7; line-height:1.4; }
.gn-badge svg{ width:18px; height:18px; flex:none; color:#FF8A8E; }
.gn-badge b{ color:#fff; }
.pc-gn-nb{ margin-left:auto; color:var(--brume); font-size:.76rem; }
.garnisons-bloc{ width:100%; max-width:620px; min-width:0; margin:0 0 18px; }
.garnisons-bloc h2{ margin:4px 0 6px; }
.gl{ display:flex; align-items:center; gap:10px; padding:9px 0; border-bottom:1px solid rgba(169,188,212,.1); }
.gl-c{ width:30px; height:30px; border-radius:7px; flex:none; background:var(--c-commun); }
.gl-c.peucommun{ background:var(--c-peucommun); } .gl-c.rare{ background:var(--c-rare); } .gl-c.epique{ background:var(--c-epique); } .gl-c.legendaire{ background:var(--c-legendaire); }
.gl-t{ flex:1; min-width:0; }
.gl-t b{ display:block; color:#fff; font-size:.86rem; }
.gl-t span{ font-size:.7rem; color:var(--brume); }
.gl-barre{ display:grid !important; grid-template-columns:repeat(10,1fr); gap:2px; margin-top:4px; width:120px; }
.gl-barre i{ height:5px; border-radius:1px; background:rgba(169,188,212,.16); }
.gl-barre i.p{ background:#E5484D; }
.gl-r{ flex:none; border:1px solid rgba(229,72,77,.45); background:rgba(229,72,77,.14); color:#fff; border-radius:999px; padding:7px 12px;
  font:inherit; font-size:.76rem; font-weight:600; cursor:pointer; white-space:nowrap; }
.gl-r:disabled{ opacity:.45; cursor:default; }
.gl-vide{ color:var(--brume); font-size:.78rem; padding:10px 0 2px; margin:0; }
'''
ecrire('style.css', css)
print(u'patch91 : OK')
