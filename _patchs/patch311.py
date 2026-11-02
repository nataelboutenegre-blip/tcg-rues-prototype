# patch311 : les grands chantiers (module Monuments de Terra, s2-78)
# Dans l'onglet Monuments (Terra), au-dessus de l'album :
#  - ton chantier : la scène en pixel art (plan bleu, échafaudage, grue, ouvriers),
#    l'avancement, la fin estimée, « Abandonner » (deux touchers) ;
#  - le choix d'un monument quand aucun chantier n'est en cours (ceux de ta collection) ;
#  - « RESTAURÉ ! » et « Inaugurer » à la fin, avec la plaque du nom gravé ;
#  - les visiteurs (TP à récolter, réserve d'une journée), ton équipe (embaucher, outils) ;
#  - la merveille du moment (envoyer / rappeler son équipe, les mécènes), les merveilles finies ;
#  - dans l'album : les monuments restaurés passent en or, avec le nom gravé.
# Le serveur fait foi (chantiers_etat) ; ici on extrapole entre deux lectures.
# Rien ne s'affiche tant que s2-78 n'est pas lancé, ni pour les comptes non testeurs
# tant que s2-78b n'a pas ouvert le module. Les dessins (chantiers/chantiers.js,
# assemblé par _chantiers/construire.py) ne se chargent qu'à la première ouverture.
import pathlib

def rep(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:100])
    return s.replace(a, b)

# ---------------------------------------------------------------- index.html
f = pathlib.Path('index.html'); s = f.read_text(encoding='utf-8')
assert 'patch311' not in s
s = rep(s, """      <h1>Monuments <span class="mon-compteur" id="monCompteur">—</span></h1>
      <div class="sub">""", """      <h1>Monuments <span class="mon-compteur" id="monCompteur">—</span></h1>
      <div id="chantiersZone" class="ch" hidden></div><!-- patch311 : les grands chantiers -->
      <div class="sub">""")
f.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------- app.js
f = pathlib.Path('app.js'); s = f.read_text(encoding='utf-8')
assert 'patch311' not in s

s = rep(s, """    if(tab.dataset.tab === 'monuments'){ vuesMonuments(); loadMonuments(); }   // patch191""",
           """    if(tab.dataset.tab === 'monuments'){ vuesMonuments(); loadMonuments(); chantiersOuvrir(); }   // patch191   // patch311""")

# l'album : le monument restauré passe en or, avec le nom gravé
s = rep(s, """  const action = SAISON2 ? '' : m.a_moi ? 'fiche' : (m.libre ? '' : 'attaquer');
  return `
    <article class="mon ${etat}\"""", """  const action = SAISON2 ? '' : m.a_moi ? 'fiche' : (m.libre ? '' : 'attaquer');
  const chm = chAlbum(m.commune_code, m.a_moi);   // patch311
  return `
    <article class="mon ${etat}${chm && chm.dore ? ' restaure' : ''}\"""")
s = rep(s, """          <span class="mon-dept">${echapperTexte(dept)}</span>
        </div>""", """          <span class="mon-dept">${echapperTexte(dept)}</span>${chm && chm.dore ? '<span class="mon-restaure">Restauré</span>' : ''}
        </div>""")
s = rep(s, """        <p class="mon-qui">${qui}</p>
      </div>
    </article>`;""", """        ${chm && chm.ligne ? `<p class="mon-grave">${chm.ligne}</p>` : ''}
        <p class="mon-qui">${qui}</p>
      </div>
    </article>`;""")

BLOC = r"""
// ---------- patch311 : les grands chantiers (s2-78) ----------
// Le module Monuments de Terra : restaurer les monuments de sa collection
// (un chantier à la fois, l'équipe travaille même quand on n'est pas là),
// récolter leurs visiteurs (des TP), graver son nom sur ceux qu'on restaure
// en premier, et restaurer à plusieurs la merveille du moment.
// Le serveur fait foi (chantiers_etat) : on ne fait ici qu'extrapoler entre
// deux lectures, pour que tout avance sous les yeux. Rien ne s'affiche tant
// que s2-78 n'est pas lancé, ni pour les comptes non testeurs tant que s2-78b
// n'a pas ouvert le module. Les dessins (chantiers/chantiers.js, 66 Ko) ne se
// chargent qu'à la première ouverture de l'onglet.
var CH = null, chLu = 0, chDecalage = 0, chIndex = null, chSigAlbum = '';
var chMoteurP = null, chBoucle = 0, chDerniere = 0, chSeconde = 0;
var chArme = '', chOccupe = false, chRelecture = false, chScJeu = null, chScMerv = null;
var chCacheVignettes = new Map();
var CH_LENT = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
var CH_TAILLE = { petit: 'petit chantier', moyen: 'chantier moyen', grand: 'grand chantier', merveille: 'merveille' };
var CH_CASQUES = ['#E07A2E', '#4C9BE8', '#C45BD6', '#2BB673', '#E5484D', '#E8C547', '#1ABC9C', '#F28CB1', '#9AD94F'];
function chMaj(x){ x = String(x || ''); return x.charAt(0).toUpperCase() + x.slice(1); }
function chNb(v){ return Math.floor(Number(v) || 0).toLocaleString('fr-FR'); }
function chVirgule(v){ return (Math.round((Number(v) || 0) * 100) / 100).toLocaleString('fr-FR'); }
function chMaintenant(){ return Date.now() + chDecalage; }
function chDuree(h){
  h = Math.max(0, Number(h) || 0);
  if(h < 1) return Math.max(1, Math.round(h * 60)) + ' min';
  const t = Math.round(h), j = Math.floor(t / 24), r = t % 24;
  if(!j) return t + ' h';
  return r ? `${j} j ${r} h` : `${j} jour${j > 1 ? 's' : ''}`;
}

// les dessins : chargés une fois, à la demande
function chMoteur(){
  if(window.TF_CHANTIERS) return Promise.resolve(window.TF_CHANTIERS);
  if(!chMoteurP) chMoteurP = new Promise((ok, ko) => {
    const sc = document.createElement('script');
    sc.src = 'chantiers/chantiers.js?v=' + VERSION_JEU;
    sc.async = true;
    sc.onload = () => window.TF_CHANTIERS ? ok(window.TF_CHANTIERS) : ko(new Error('dessins absents'));
    sc.onerror = () => { chMoteurP = null; ko(new Error('dessins introuvables')); };
    document.head.appendChild(sc);
  });
  return chMoteurP;
}

// l'état du serveur
function chRecevoir(d){
  CH = d && typeof d === 'object' ? d : null;
  chLu = Date.now(); chIndex = null;
  if(CH && CH.maintenant){ const t = new Date(CH.maintenant).getTime(); if(!isNaN(t)) chDecalage = t - chLu; }
  if(CH && CH.solde != null){
    if(packStatusCache) packStatusCache.solde = Number(CH.solde);
    const mb = document.getElementById('mbPoints');
    if(mb) mb.textContent = fmtNombre(Number(CH.solde));
  }
}
async function chantiersCharger(){
  if(!SAISON2 || !enTerra()) return null;
  try{
    const { data, error } = await sb.rpc('chantiers_etat');
    if(error){ CH = null; chIndex = null; return null; }   // s2-78 pas encore lancé : rien ne s'affiche
    chRecevoir(data);
  }catch(e){ /* réseau : on garde ce qu'on avait */ }
  return CH;
}
function chIdx(){
  if(chIndex) return chIndex;
  const mons = new Map(), miens = new Map(), finies = new Map();
  ((CH && CH.monuments) || []).forEach(m => mons.set(m.code, m));
  ((CH && CH.restaurations) || []).forEach(r => miens.set(r.code, r));
  ((CH && CH.merveilles_finies) || []).forEach(x => finies.set(x.code, x));
  chIndex = { mons, miens, finies };
  return chIndex;
}

// ce qui avance entre deux lectures
function chFait(){
  const c = CH && CH.chantier;
  if(!c) return 0;
  const t = Number(c.travail) || 1, f = Number(c.fait) || 0;
  if(c.en_pause) return Math.min(t, f);
  const r = Number(CH.equipe && CH.equipe.rythme) || 0;
  return Math.min(t, f + r * Math.max(0, chMaintenant() - new Date(c.depuis).getTime()) / 3600e3);
}
function chReste(){   // ms avant la fin ; null en pause
  const c = CH && CH.chantier;
  if(!c || c.en_pause || !c.fin_prevue) return null;
  return Math.max(0, new Date(c.fin_prevue).getTime() - chMaintenant());
}
function chAVisiteurs(){
  const v = CH && CH.visiteurs;
  if(!v) return 0;
  const taux = Number(v.par_jour) || 0;
  return Math.min(taux, (Number(v.stock) || 0) + taux * Math.max(0, chMaintenant() - new Date(v.stock_maj).getTime()) / 86400e3);
}
function chMervFait(){
  const m = CH && CH.merveille;
  if(!m) return 0;
  return Math.min(Number(m.total) || 0, (Number(m.fait) || 0) + (Number(m.rythme) || 0) * (Date.now() - chLu) / 3600e3);
}
function chMesHeures(){
  const m = CH && CH.merveille;
  if(!m || !m.moi) return 0;
  return (Number(m.moi.heures) || 0) + (m.moi.actif ? (Number(m.moi.rythme) || 0) * (Date.now() - chLu) / 3600e3 : 0);
}
function chTp(taille){ return Number(((CH && CH.regles && CH.regles.visiteurs) || {})[taille]) || 0; }
function chR(cle, def){ const v = CH && CH.regles ? Number(CH.regles[cle]) : NaN; return isNaN(v) ? def : v; }
// l'album ne se redessine que si ce qu'il montre a changé
function chAlbumAJour(){
  const sig = CH && CH.permis ? JSON.stringify([(CH.restaurations || []).map(x => x.code + (x.premier ? '*' : '')),
    (CH.monuments || []).filter(m => m.graveur).map(m => m.code + m.graveur), (CH.merveilles_finies || []).map(x => x.code + x.mecenes)]) : '';
  if(sig === chSigAlbum) return;
  chSigAlbum = sig;
  if(monuments.length) renderMonuments();
}

// ce que montre la grande scène : une inauguration à faire, sinon le
// chantier en cours, sinon le dernier monument restauré
function chVue(){
  const restos = (CH && CH.restaurations) || [];
  const a = restos.filter(r => !r.inaugure);
  if(a.length) return { type: 'inaug', code: a[a.length - 1].code, r: a[a.length - 1] };
  if(CH && CH.chantier) return { type: 'chantier', code: CH.chantier.code };
  if(restos.length) return { type: 'fini', code: restos[restos.length - 1].code, r: restos[restos.length - 1] };
  return null;
}

// l'album : or et nom gravé
function chAlbum(code, aMoi){
  if(!CH || !CH.permis || !enTerra()) return null;
  const I = chIdx(), m = I.mons.get(code);
  if(!m) return null;
  if(m.taille === 'merveille'){
    const x = I.finies.get(code);
    return x ? { dore: true, ligne: `★ Merveille restaurée par ${chNb(x.mecenes)} mécène${Number(x.mecenes) > 1 ? 's' : ''}` }
             : { dore: false, ligne: 'Merveille collective' };
  }
  const moi = I.miens.get(code);
  if(moi && moi.premier) return { dore: true, ligne: '★ Ton nom est gravé' };
  if(m.graveur) return { dore: !!moi, ligne: '★ Gravé : ' + echapperTexte(m.graveur) };
  return { dore: !!moi, ligne: moi ? '' : (aMoi ? 'Chantier possible' : '') };
}

function chSegs(id){ return `<div class="ch-segs" id="${id}" aria-hidden="true">${'<i></i>'.repeat(24)}</div>`; }
function chSegsMaj(id, p, fini){
  const z = document.getElementById(id);
  if(!z) return;
  const n = Math.floor(Math.max(0, Math.min(1, p)) * 24 + 1e-9);
  Array.prototype.forEach.call(z.children, (x, k) => { x.className = k < n ? (fini ? 'vert' : 'on') : ''; });
}

function chVoileHtml(mon, r){
  const date = new Date(r.le).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
  const autre = !r.premier && mon.graveur ? `${echapperTexte(mon.graveur)} l’avait restauré avant toi : son nom reste gravé. ` : '';
  return `<div class="ch-voile">
    <p class="ch-gros">RESTAURÉ !</p>
    <p>${r.premier ? 'Tu es le premier à le restaurer : ton nom est gravé pour toujours. ' : autre}Il te rapportera <b>${chTp(mon.taille)} TP</b> par jour.</p>
    <p class="ch-plaque">${r.premier ? 'Restauré en premier par toi' : 'Restauré par toi'}<br><small>${echapperTexte(chMaj(mon.embleme))} · ${date}</small></p>
    <button type="button" class="ch-bouton vert" data-ch="inaugurer" data-code="${echapperTexte(mon.code)}">Inaugurer</button>
  </div>`;
}

function renderChantiers(){
  const z = document.getElementById('chantiersZone');
  if(!z) return;
  if(!CH || !CH.permis || !enTerra()){ z.hidden = true; z.innerHTML = ''; chArret(); return; }
  const I = chIdx(), E = CH.equipe || {}, V = CH.visiteurs || {};
  const solde = Number(CH.solde) || 0, plafond = chR('plafond', 300), seuil = chR('mecene', 24);
  const vue = chVue();
  const mon = vue ? I.mons.get(vue.code) : null;
  const c = CH.chantier;
  let h = `<div class="ch-tete"><h2 class="ch-h2">Grands chantiers</h2>
    <p class="ch-intro">Restaure les monuments de ta collection : ton équipe travaille même quand tu n’es pas là. Un monument restauré attire des visiteurs, et le premier à le restaurer y grave son nom.</p>
    ${CH.ouvert ? '' : '<p class="ch-essai">Essai : seuls les comptes testeurs voient les grands chantiers pour l’instant.</p>'}</div>`;

  // la scène
  if(vue && mon){
    const enCours = vue.type === 'chantier';
    h += `<div class="ch-scene">
      <div class="ch-scene-tete"><p class="ch-scene-titre">${echapperTexte(chMaj(mon.embleme))}<small>${echapperTexte(mon.commune)} (${echapperTexte(mon.dept)}) · ${CH_TAILLE[mon.taille] || ''}</small></p>
        <div class="ch-boite"><span>${enCours ? (c.en_pause ? 'EN PAUSE' : 'CHANTIER') : 'VISITEURS'}</span><b id="chBoiteVal">${enCours ? Math.floor(chFait() / (Number(c.travail) || 1) * 100) + ' %' : '+' + chTp(mon.taille) + '/j'}</b></div></div>
      <canvas id="chCanvas" width="192" height="108" role="img" aria-label="${echapperTexte(chMaj(mon.embleme))}"></canvas>
      ${vue.type === 'inaug' ? chVoileHtml(mon, vue.r) : ''}
    </div>`;
    if(enCours){
      h += chSegs('chSegs') + `<div class="ch-lignes"><p id="chLigneFin"></p><p id="chLigneRythme"></p></div>
        <div class="ch-actions"><button type="button" class="ch-lien${chArme === 'abandonner' ? ' arme' : ''}" data-ch="abandonner">${chArme === 'abandonner' ? 'Sûr ? Le travail fait sera perdu. Touche encore pour abandonner' : 'Abandonner ce chantier'}</button></div>`;
    }
  }

  // le choix d'un monument, quand aucun chantier n'est en cours
  if(!c){
    const libres = (CH.monuments || []).filter(m => m.taille !== 'merveille' && m.a_moi && !I.miens.has(m.code));
    const rang = { grand: 0, moyen: 1, petit: 2 };
    libres.sort((a, b) => (rang[a.taille] - rang[b.taille]) || ((Number(b.langues) || 0) - (Number(a.langues) || 0)));
    h += `<h3 class="ch-h3">${vue ? 'Ton prochain chantier' : 'Choisis ton premier chantier'}</h3>`;
    if(libres.length){
      const r = Number(E.rythme) || 3, T = (CH.regles && CH.regles.travail) || {};
      h += `<p class="ch-note">Les monuments de ta collection Terra qui attendent leur chantier. Touches-en un pour lancer ton équipe.</p>
        <div class="ch-choix">${libres.map(m => `<button type="button" class="ch-mon" data-ch="commencer" data-code="${echapperTexte(m.code)}">
          <canvas width="192" height="108" data-dessin="${echapperTexte(m.dessin)}" aria-hidden="true"></canvas>
          <b>${echapperTexte(chMaj(m.embleme))}</b>
          <small>${echapperTexte(m.commune)} (${echapperTexte(m.dept)}) · ${CH_TAILLE[m.taille]}</small>
          <span class="ch-mon-info">${chDuree((Number(T[m.taille]) || 0) / r)} avec ton équipe · +${chTp(m.taille)} TP/jour</span>
          <span class="ch-mon-grave">${m.graveur ? '★ Gravé : ' + echapperTexte(m.graveur) : 'Personne ne l’a encore restauré'}</span>
        </button>`).join('')}</div>`;
    } else {
      const total = (CH.monuments || []).filter(m => m.taille !== 'merveille').length;
      h += `<p class="ch-note">${I.miens.size ? 'Tu as restauré tous les monuments de ta collection.' : 'Aucun monument de ta collection n’a encore de chantier.'} Les ${total} monuments à restaurer arrivent avec leurs communes, dans les paquets Terra : l’album plus bas montre ceux qu’il te reste à trouver. En attendant, ton équipe peut aider la merveille du moment.</p>`;
    }
  }

  // les visiteurs et l'équipe
  const restos = CH.restaurations || [];
  const mecene = (CH.merveilles_finies || []).filter(x => Number(x.mes_heures) >= seuil);
  const brut = Number(V.brut) || 0, parJour = Number(V.par_jour) || 0;
  h += `<div class="ch-grille">
    <div class="ch-carte ch-vis">
      <div class="ch-haut"><h3>Les visiteurs</h3><span class="ch-val" id="chVisVal">+0</span></div>
      ${restos.length || mecene.length ? `
        <p>Tes monuments rapportent <b>${chNb(parJour)} TP</b> par jour${brut > plafond ? ` (le plafond de ${plafond} est atteint)` : ` (${plafond} au plus)`}. Les visiteurs s’accumulent jusqu’à une journée de recette : passe les récolter chaque jour.</p>
        <div class="ch-liste-v">${restos.map(r => { const m = I.mons.get(r.code); return m ? `<div><span>${echapperTexte(chMaj(m.embleme))}${r.premier ? ' <i title="Ton nom est gravé">★</i>' : ''}</span><b>+${chTp(m.taille)} / jour</b></div>` : ''; }).join('')}${mecene.map(x => { const m = I.mons.get(x.code); return `<div><span>${echapperTexte(m ? chMaj(m.embleme) : 'Merveille')} (mécène)</span><b>+${chR('mecene_tp', 20)} / jour</b></div>`; }).join('')}</div>
        <div class="ch-jauge" aria-hidden="true"><i id="chVisJauge"></i></div>
        <button type="button" class="ch-bouton vert" data-ch="recolter" id="chRecolter">Récolter</button>`
      : `<p>Chaque monument restauré attire des visiteurs : <b>${chTp('petit')} TP</b> par jour pour un petit chantier, <b>${chTp('moyen')}</b> pour un moyen, <b>${chTp('grand')}</b> pour un grand. Au plus <b>${plafond}</b> par jour.</p>`}
    </div>
    <div class="ch-carte">
      <div class="ch-haut"><h3>Ton équipe</h3><span class="ch-val">${chNb(E.ouvriers)} ouvriers</span></div>
      <p>Outils niveau ${chNb(E.outils)} : ton équipe fait <b>${chVirgule(E.rythme)} heures</b> de travail par heure, sur ton chantier comme sur la merveille.</p>
      <button type="button" class="ch-bouton" data-ch="embaucher"${E.cout_ouvrier == null || solde < E.cout_ouvrier ? ' disabled' : ''}>${E.cout_ouvrier == null ? 'Équipe complète' : `Embaucher un ouvrier · ${chNb(E.cout_ouvrier)} TP`}</button>
      <button type="button" class="ch-bouton sec" data-ch="outils"${E.cout_outils == null || solde < E.cout_outils ? ' disabled' : ''}>${E.cout_outils == null ? 'Meilleurs outils' : `Outils niveau ${(Number(E.outils) || 1) + 1} (+15 %) · ${chNb(E.cout_outils)} TP`}</button>
      <p class="ch-petit">Tu as <b>${chNb(solde)} TP</b>.</p>
    </div>
  </div>`;

  // la merveille du moment
  const M = CH.merveille;
  if(M){
    const mm = I.mons.get(M.code), moi = M.moi || null, actif = !!(moi && moi.actif), graves = chR('graves', 10);
    h += `<h3 class="ch-h3 merv">La merveille du moment</h3>
      <p class="ch-note">Une seule à la fois, pour tout le jeu. Envoie ton équipe : ton propre chantier s’arrête pendant ce temps. Avec au moins ${seuil} h de travail données, tu deviens mécène : +${chR('mecene_tp', 20)} TP par jour, pour toujours. Les ${graves} plus gros contributeurs sont gravés.</p>
      <div class="ch-scene merv"><div class="ch-scene-tete"><p class="ch-scene-titre">${echapperTexte(mm ? chMaj(mm.embleme) : 'Merveille')}<small id="chMervSous"></small></p><div class="ch-boite merv"><span>MERVEILLE</span><b id="chMervPct">0 %</b></div></div>
        <canvas id="chCanvasMerv" width="192" height="108" role="img" aria-label="Le chantier de la merveille"></canvas></div>
      ${chSegs('chMervSegs')}
      <div class="ch-grille">
        <div class="ch-carte merv"><div class="ch-haut"><h3>Ton équipe</h3><span class="ch-val" id="chMesHeures">0 h</span></div>
          <p id="chMervTexte"></p>
          <button type="button" class="ch-bouton violet" data-ch="${actif ? 'rappeler' : 'envoyer'}">${actif ? 'Reprendre mon chantier' : 'Envoyer mon équipe'}</button></div>
        <div class="ch-carte merv"><div class="ch-haut"><h3>Les mécènes</h3><span class="ch-petit">${chNb(M.mecenes)} mécène${Number(M.mecenes) > 1 ? 's' : ''}</span></div>
          <div class="ch-mecenes">${(M.top || []).length ? M.top.map(x => `<div class="${x.moi ? 'moi' : ''}"><span>${chNb(x.rang)}</span><span>${x.moi ? 'Toi' : echapperTexte(x.pseudo)}${Number(x.heures) >= seuil ? ' ✦' : ''}</span><span>${chNb(x.heures)} h</span></div>`).join('')
            + (moi && Number(moi.rang) > graves ? `<div class="moi"><span>${chNb(moi.rang)}</span><span>Toi</span><span>${chNb(moi.heures)} h</span></div>` : '')
            : '<p class="ch-petit">Personne pour l’instant : sois le premier.</p>'}</div>
          <p class="ch-petit">✦ mécène (au moins ${seuil} h). Les ${graves} premiers sont gravés pour toujours.</p></div>
      </div>`;
  } else if((CH.merveilles_finies || []).length){
    h += `<h3 class="ch-h3 merv">Les merveilles</h3><p class="ch-note">Toutes les merveilles sont restaurées. Bravo aux mécènes !</p>`;
  }
  const finies = CH.merveilles_finies || [];
  if(finies.length){
    h += `<div class="ch-finies">${finies.slice().reverse().map(x => {
      const m = I.mons.get(x.code), moiMec = Number(x.mes_heures) >= seuil;
      return `<div class="ch-finie"><canvas width="192" height="108" data-dessin="${echapperTexte(m ? m.dessin : '')}" aria-hidden="true"></canvas>
        <div><b>${echapperTexte(m ? chMaj(m.embleme) : 'Merveille')}</b><small>Restaurée ${dateCourte(x.finie_le)} · ${chNb(x.mecenes)} mécène${Number(x.mecenes) > 1 ? 's' : ''}${moiMec ? ' · tu en fais partie' : ''}</small>
        <span class="ch-plaque petite">${(x.graves || []).map(p => echapperTexte(p)).join(', ')}</span></div></div>`;
    }).join('')}</div>`;
  }
  h += '<h2 class="ch-h2 ch-album-titre">L’album</h2>';

  z.innerHTML = h;
  z.hidden = false;
  chVignettes(z);
  chMajTextes();
  chDessiner(performance.now(), true);
  chAnimer();
}

// les textes qui bougent (chaque seconde)
function chMajTextes(){
  if(!CH || !CH.permis) return;
  const $ = (id) => document.getElementById(id);
  const c = CH.chantier, vue = chVue();
  if(c && vue && vue.type === 'chantier'){
    const t = Number(c.travail) || 1, f = chFait(), p = f / t, reste = chReste();
    const v = $('chBoiteVal'); if(v) v.textContent = Math.floor(p * 100) + ' %';
    chSegsMaj('chSegs', p, false);
    const fin = $('chLigneFin');
    if(fin) fin.textContent = c.en_pause ? 'En pause : ton équipe est sur la merveille' : (reste > 0 ? 'Fin dans ' + formatDuree(reste) : 'Terminé ! Inauguration…');
    const ry = $('chLigneRythme');
    if(ry) ry.textContent = `Travail : ${chNb(Math.min(f, t))} / ${chNb(t)} h · ${chVirgule(CH.equipe && CH.equipe.rythme)} h par heure`;
    if(reste === 0) chRelire();
  }
  const a = chAVisiteurs(), n = Math.floor(a), taux = Number(CH.visiteurs && CH.visiteurs.par_jour) || 0;
  const vv = $('chVisVal'); if(vv) vv.textContent = '+' + n;
  const j = $('chVisJauge'); if(j) j.style.width = (taux ? Math.min(100, a / taux * 100) : 0) + '%';
  const b = $('chRecolter');
  if(b){ b.disabled = n < 1 || chOccupe; b.textContent = n >= 1 ? `Récolter ${chNb(n)} TP` : 'Rien à récolter pour l’instant'; }
  const M = CH.merveille;
  if(M){
    const total = Number(M.total) || 1, fm = chMervFait(), pm = fm / total;
    const pc = $('chMervPct'); if(pc) pc.textContent = Math.floor(pm * 100) + ' %';
    const so = $('chMervSous'); if(so) so.textContent = `${chNb(fm)} h sur ${chNb(total)} h · ${chNb(M.equipes)} équipe${Number(M.equipes) > 1 ? 's' : ''}`;
    chSegsMaj('chMervSegs', pm, false);
    const mh = chMesHeures(), seuil = chR('mecene', 24), actif = !!(M.moi && M.moi.actif);
    const hh = $('chMesHeures'); if(hh) hh.textContent = chNb(mh) + ' h';
    const tx = $('chMervTexte');
    if(tx) tx.innerHTML = actif
      ? `Ton équipe (${chNb(CH.equipe.ouvriers)} ouvriers, casques blancs) travaille sur la merveille.${c ? ' <b>Ton chantier est en pause.</b>' : ''} ${mh < seuil ? `Encore ${Math.ceil(seuil - mh)} h pour devenir mécène.` : 'Tu es mécène.'}`
      : (mh >= seuil ? `Tu es mécène (${chNb(mh)} h). Continue pour monter parmi les ${chR('graves', 10)} premiers.`
                     : `Envoie ton équipe aider.${c ? ' Ton chantier s’arrête pendant ce temps : tu le reprends quand tu veux.' : ' Tu n’as pas de chantier en cours : elle ne perd rien.'}`);
    if(pm >= 1) chRelire();
  }
}

// relire le serveur (une fin de chantier, la minute qui passe) sans s'emballer
function chRelire(){
  if(chRelecture || Date.now() - chLu < 5000) return;
  chRelecture = true;
  chantiersCharger().then(() => {
    chRelecture = false;
    renderChantiers();
    chAlbumAJour();
  });
}

// le dessin
function chVisible(cv){
  const r = cv.getBoundingClientRect();
  return r.width > 0 && r.bottom > 0 && r.top < (window.innerHeight || 800);
}
function chDessiner(t, force){
  const T = window.TF_CHANTIERS;
  if(!T || !CH) return;
  if(!chScJeu){ chScJeu = T.creerScene(); chScMerv = T.creerScene(); }
  const I = chIdx(), vue = chVue(), ouv = Math.min(8, Number(CH.equipe && CH.equipe.ouvriers) || 3);
  const cv = document.getElementById('chCanvas');
  if(cv && vue && (force || chVisible(cv))){
    const m = I.mons.get(vue.code), d = m && T.DESSINS[m.dessin];
    if(d){
      const ctx = cv.getContext('2d'); ctx.imageSmoothingEnabled = false;
      if(vue.type === 'chantier'){
        const c = CH.chantier, p = chFait() / (Number(c.travail) || 1);
        chScJeu(ctx, d, { pct: p, fini: p >= 1, ouvriers: c.en_pause ? 0 : ouv, visiteurs: 0 }, t);
      } else chScJeu(ctx, d, { pct: 1, fini: true, ouvriers: vue.type === 'inaug' ? ouv : 0, visiteurs: 6 }, t);
    }
  }
  const cm = document.getElementById('chCanvasMerv'), M = CH.merveille;
  if(cm && M && (force || chVisible(cm))){
    const m = I.mons.get(M.code), d = m && T.DESSINS[m.dessin];
    if(d){
      const ctx = cm.getContext('2d'); ctx.imageSmoothingEnabled = false;
      const actif = !!(M.moi && M.moi.actif);
      const casques = CH_CASQUES.slice(0, Math.min(CH_CASQUES.length, Math.max(0, (Number(M.actives) || 0) - (actif ? 1 : 0))));
      if(actif) for(let k = 0; k < ouv; k++) casques.push('#FFFFFF');
      chScMerv(ctx, d, { pct: chMervFait() / (Number(M.total) || 1), fini: false, ouvriers: casques.length, casques, visiteurs: 0 }, t);
    }
  }
}
// les vignettes : chaque dessin est peint une fois, puis recopié
function chVignettes(z){
  const T = window.TF_CHANTIERS;
  if(!T) return;
  z.querySelectorAll('canvas[data-dessin]').forEach(cv => {
    const nom = cv.dataset.dessin, d = T.DESSINS[nom];
    if(!d) return;
    let src = chCacheVignettes.get(nom);
    if(!src){
      src = document.createElement('canvas'); src.width = T.PW; src.height = T.PH;
      const x = src.getContext('2d'); x.imageSmoothingEnabled = false;
      T.creerScene()(x, d, { pct: 1, fini: true, ouvriers: 0, visiteurs: 0 }, 1300);
      chCacheVignettes.set(nom, src);
    }
    const ctx = cv.getContext('2d'); ctx.imageSmoothingEnabled = false;
    ctx.drawImage(src, 0, 0);
  });
}
// l'animation : 12 images par seconde, seulement onglet ouvert et écran allumé
function chAnimer(){
  if(chBoucle) return;
  const pas = (t) => {
    const p = document.getElementById('panel-monuments');
    if(!CH || !CH.permis || !p || !p.classList.contains('active') || document.hidden){ chBoucle = 0; return; }
    chBoucle = requestAnimationFrame(pas);
    if(t - chDerniere < (CH_LENT ? 1000 : 83)) return;
    chDerniere = t;
    chDessiner(t, false);
    if(t - chSeconde >= 1000){ chSeconde = t; chMajTextes(); }
    if(Date.now() - chLu > 60000) chRelire();
  };
  chBoucle = requestAnimationFrame(pas);
}
function chArret(){ if(chBoucle){ cancelAnimationFrame(chBoucle); chBoucle = 0; } }
document.addEventListener('visibilitychange', () => {
  if(document.hidden || !CH || !CH.permis) return;
  const p = document.getElementById('panel-monuments');
  if(p && p.classList.contains('active')){ chRelire(); chAnimer(); }
});

// l'onglet s'ouvre
async function chantiersOuvrir(){
  const z = document.getElementById('chantiersZone');
  if(!z) return;
  if(!SAISON2 || !enTerra()){ z.hidden = true; chArret(); return; }
  if(CH && CH.permis) renderChantiers();   // ce qu'on sait déjà, tout de suite
  const r = await Promise.all([chantiersCharger(), chMoteur().catch(() => null)]);
  renderChantiers();
  chAlbumAJour();
}

// les boutons
async function chAction(rpc, args, apres){
  if(chOccupe) return;
  chOccupe = true;
  try{
    const { data, error } = await sb.rpc(rpc, args || {});
    if(error){
      notifier({ type: 'erreur', titre: 'Grands chantiers', texte: messageLisible(error.message) });
      await chantiersCharger();
    } else {
      chRecevoir(data);
      if(apres) try{ apres(data); }catch(e){}
    }
  }catch(e){
    notifier({ type: 'erreur', titre: 'Grands chantiers', texte: messageLisible(e && e.message) });
  }finally{
    chOccupe = false;
    renderChantiers();
    chAlbumAJour();
  }
}
document.getElementById('chantiersZone').addEventListener('click', (e) => {
  const b = e.target.closest('[data-ch]');
  if(!b || b.disabled) return;
  const quoi = b.dataset.ch, code = b.dataset.code || '';
  if(quoi !== 'abandonner' && chArme){ chArme = ''; }
  if(quoi === 'commencer'){
    chAction('chantier_commencer', { p_code: code }, () => {
      const m = chIdx().mons.get(code);
      notifier({ type: 'succes', titre: 'Chantier lancé', texte: m ? chMaj(m.embleme) + ' : ton équipe est au travail.' : 'Ton équipe est au travail.' });
      const z = document.getElementById('chantiersZone');
      if(z) z.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  } else if(quoi === 'abandonner'){
    if(chArme !== 'abandonner'){
      chArme = 'abandonner'; renderChantiers();
      setTimeout(() => { if(chArme === 'abandonner'){ chArme = ''; renderChantiers(); } }, 6000);
      return;
    }
    chArme = '';
    chAction('chantier_abandonner', {}, () => notifier({ type: 'info', titre: 'Chantier abandonné', texte: 'Tu peux en choisir un autre.' }));
  } else if(quoi === 'inaugurer'){
    chAction('chantier_inaugurer', { p_code: code });
  } else if(quoi === 'recolter'){
    chAction('chantiers_recolter', {}, (d) => notifier({ type: 'succes', titre: 'Visiteurs récoltés', texte: `+${chNb(d && d.gain)} TP` }));
  } else if(quoi === 'embaucher'){
    chAction('chantiers_embaucher', {}, () => notifier({ type: 'succes', titre: 'Un ouvrier de plus', texte: `Ton équipe compte ${chNb(CH.equipe.ouvriers)} ouvriers.` }));
  } else if(quoi === 'outils'){
    chAction('chantiers_outils', {}, () => notifier({ type: 'succes', titre: 'Nouveaux outils', texte: `Niveau ${chNb(CH.equipe.outils)} : ${chVirgule(CH.equipe.rythme)} h de travail par heure.` }));
  } else if(quoi === 'envoyer'){
    chAction('merveille_equipe', { p_envoyer: true }, () => notifier({ type: 'succes', titre: 'Équipe envoyée', texte: 'Elle travaille sur la merveille.' + (CH.chantier ? ' Ton chantier est en pause.' : '') }));
  } else if(quoi === 'rappeler'){
    chAction('merveille_equipe', { p_envoyer: false }, () => notifier({ type: 'info', titre: 'Équipe revenue', texte: CH.chantier ? 'Ton chantier reprend.' : 'Elle attend ton prochain chantier.' }));
  }
});
"""

s = rep(s, """document.getElementById('monGrille').addEventListener('keydown', (e) => {
  if(e.key !== 'Enter' && e.key !== ' ') return;
  const c = e.target.closest('[data-mon]');
  if(!c) return;
  e.preventDefault();
  c.click();
});
""", """document.getElementById('monGrille').addEventListener('keydown', (e) => {
  if(e.key !== 'Enter' && e.key !== ' ') return;
  const c = e.target.closest('[data-mon]');
  if(!c) return;
  e.preventDefault();
  c.click();
});
""" + BLOC)
f.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------- style.css
f = pathlib.Path('style.css'); s = f.read_text(encoding='utf-8')
assert 'patch311' not in s
s = s.rstrip('\n') + """

/* patch311 : les grands chantiers (onglet Monuments, Terra) */
.ch{ width:100%; min-width:0; display:flex; flex-direction:column; gap:12px; margin:4px 0 6px; color:#EAF1F8; }
.ch[hidden]{ display:none; }
.ch p{ margin:0; }
.ch-tete{ display:flex; flex-direction:column; gap:6px; }
.ch-h2{ margin:6px 0 0; font-family: var(--titre); font-weight:800; font-size:clamp(1.7rem, 6vw, 2.3rem); line-height:1; color:#fff; }
.ch-h3{ margin:10px 0 0; font-family: var(--titre); font-weight:800; font-size:1.45rem; line-height:1.05; color:#FFD56B; }
.ch-h3.merv{ color:#D3B8FF; }
.ch-intro{ color: var(--brume); font-size:0.92rem; max-width:62ch; }
.ch-note{ color: var(--brume); font-size:0.86rem; max-width:70ch; }
.ch-essai{ align-self:flex-start; padding:5px 10px; border-radius:8px; font-size:0.8rem; font-weight:600;
  color:#13233B; background:#FFD56B; }
.ch-scene{ position:relative; border-radius:16px; overflow:hidden; border:1px solid rgba(169,188,212,0.18);
  background-color:#0B1A33;
  background-image: linear-gradient(rgba(90,169,255,0.12) 1px, transparent 1px), linear-gradient(90deg, rgba(90,169,255,0.12) 1px, transparent 1px);
  background-size: 3.125% 5.555%; }
.ch-scene canvas{ display:block; width:100%; height:auto; image-rendering:pixelated; image-rendering:crisp-edges; }
.ch-scene-tete{ display:flex; justify-content:space-between; align-items:flex-start; gap:10px; padding:9px 11px 2px; }
.ch-scene-titre{ min-width:0; font-family: var(--titre); font-weight:700; font-size:clamp(1.15rem, 4.6vw, 1.8rem); line-height:0.95;
  text-transform:uppercase; color:#fff; text-shadow:0 2px 0 #0B1A33, 0 0 8px rgba(11,26,51,0.9); }
.ch-scene-titre small{ display:block; margin-top:4px; font-family: var(--texte); font-size:0.74rem; font-weight:600; text-transform:none; color: var(--brume); text-shadow:0 1px 2px #0B1A33; }
.ch-boite{ flex:none; padding:3px 9px 5px; border:2px solid var(--c-legendaire); border-radius:10px; background:rgba(11,26,51,0.88); text-align:center; }
.ch-boite span{ display:block; font-family: var(--titre); font-size:0.66rem; letter-spacing:0.18em; color:#FFD56B; }
.ch-boite b{ display:block; font-family: var(--titre); font-weight:700; font-size:clamp(1.15rem, 4.4vw, 1.7rem); line-height:1; color:#fff; }
.ch-boite.merv{ border-color:#B794F4; }
.ch-boite.merv span{ color:#D3B8FF; }
.ch-voile{ position:absolute; left:50%; top:52%; z-index:2; transform:translate(-50%, -50%); width:min(90%, 430px);
  display:flex; flex-direction:column; align-items:center; gap:7px; padding:12px 14px;
  background:rgba(11,26,51,0.94); border:2px solid #7EE2B0; border-radius:16px; text-align:center; font-size:0.86rem; color:#C9D6E6; }
.ch-gros{ font-family: var(--titre); font-weight:700; font-size:clamp(1.6rem, 6vw, 2.3rem); line-height:1; color:#7EE2B0; }
.ch-plaque{ display:inline-block; padding:5px 12px; border-radius:6px; background:linear-gradient(180deg, #F7D774, #C9962A);
  color:#3A2A08; font-family: var(--titre); font-weight:700; font-size:0.95rem; line-height:1.15;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.45), 0 2px 0 #7A5106; }
.ch-plaque small{ font-family: var(--texte); font-weight:600; font-size:0.72rem; color:#5A4108; }
.ch-plaque.petite{ align-self:flex-start; padding:3px 8px; font-family: var(--texte); font-size:0.72rem; font-weight:700; }
.ch-segs{ display:flex; gap:3px; }
.ch-segs i{ flex:1; height:9px; border-radius:3px; background:#1F3A60; }
.ch-segs i.on{ background: var(--c-legendaire); }
.ch-segs i.vert{ background:#7EE2B0; }
.ch-lignes{ display:flex; flex-wrap:wrap; justify-content:space-between; gap:3px 16px; font-size:0.84rem; color:#C9D6E6; }
.ch-actions{ display:flex; justify-content:flex-end; }
.ch-lien{ background:none; border:0; padding:4px 0; font:inherit; font-size:0.82rem; color: var(--brume); text-decoration:underline; text-underline-offset:3px; cursor:pointer; }
.ch-lien.arme{ color:#FF8F92; font-weight:700; }
.ch-choix{ display:grid; grid-template-columns:repeat(auto-fill, minmax(168px, 1fr)); gap:10px; }
.ch-mon{ display:flex; flex-direction:column; gap:3px; padding:6px 6px 8px; border-radius:12px; border:1px solid rgba(169,188,212,0.18);
  background:#162C4B; color:#EAF1F8; font:inherit; text-align:left; cursor:pointer; }
.ch-mon:hover{ border-color: var(--c-legendaire); }
.ch-mon canvas{ width:100%; height:auto; image-rendering:pixelated; border-radius:7px; background:#0B1A33; margin-bottom:3px; }
.ch-mon b{ font-size:0.86rem; line-height:1.2; }
.ch-mon small{ font-size:0.74rem; color: var(--brume); }
.ch-mon-info{ font-size:0.74rem; color:#7EE2B0; font-weight:600; }
.ch-mon-grave{ font-size:0.72rem; color:#FFD56B; }
.ch-grille{ display:grid; grid-template-columns:repeat(auto-fit, minmax(250px, 1fr)); gap:10px; }
.ch-carte{ display:flex; flex-direction:column; gap:8px; padding:12px 14px; border-radius:14px; background:#162C4B; border:1px solid rgba(169,188,212,0.14); }
.ch-carte h3{ margin:0; font-family: var(--titre); font-weight:800; font-size:1.3rem; line-height:1.05; color:#fff; }
.ch-carte p{ font-size:0.86rem; color:#C9D6E6; }
.ch-carte p b{ color:#fff; }
.ch-haut{ display:flex; justify-content:space-between; align-items:baseline; gap:10px; }
.ch-val{ font-family: var(--titre); font-weight:800; font-size:1.35rem; line-height:1; color:#FFD56B; white-space:nowrap; }
.ch-carte.ch-vis{ background:#13314A; border-color:rgba(126,226,176,0.45); }
.ch-carte.ch-vis .ch-val{ color:#7EE2B0; }
.ch-carte.merv{ background:#1A1F45; border-color:#6B4FB0; }
.ch-carte.merv h3{ color:#D3B8FF; }
.ch-carte.merv .ch-val{ color:#D3B8FF; }
.ch-petit{ font-size:0.78rem !important; color: var(--brume) !important; }
.ch-bouton{ min-height:44px; padding:0 16px; border:0; border-radius:12px; background: var(--c-legendaire); color:#13233B;
  font-family: var(--titre); font-weight:800; font-size:1.12rem; cursor:pointer; }
.ch-bouton.vert{ background:#7EE2B0; }
.ch-bouton.violet{ background:#B794F4; color:#1A1240; }
.ch-bouton.sec{ background:transparent; color:#FFD56B; box-shadow: inset 0 0 0 2px rgba(240,180,41,0.55); }
.ch-bouton:disabled{ background:#2A3E5C; color: var(--brume); box-shadow:none; cursor:default; }
.ch-liste-v{ display:flex; flex-direction:column; gap:4px; font-size:0.84rem; }
.ch-liste-v div{ display:flex; justify-content:space-between; gap:10px; color:#C9D6E6; }
.ch-liste-v div i{ font-style:normal; color:#FFD56B; }
.ch-liste-v div b{ color:#7EE2B0; font-weight:600; white-space:nowrap; }
.ch-jauge{ height:8px; border-radius:4px; background:#1F3A60; overflow:hidden; }
.ch-jauge i{ display:block; height:100%; width:0; background:#7EE2B0; }
.ch-mecenes{ display:flex; flex-direction:column; gap:2px; font-size:0.84rem; }
.ch-mecenes > div{ display:grid; grid-template-columns:2.4ch 1fr auto; gap:8px; padding:2px 6px; border-radius:6px; color:#C9D6E6; }
.ch-mecenes > div span:nth-child(2){ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.ch-mecenes > div span:last-child{ color:#D3B8FF; white-space:nowrap; }
.ch-mecenes > div.moi{ background:rgba(255,255,255,0.08); color:#fff; font-weight:600; }
.ch-finies{ display:flex; flex-direction:column; gap:8px; }
.ch-finie{ display:grid; grid-template-columns:96px 1fr; gap:10px; align-items:center; padding:8px; border-radius:12px;
  background:linear-gradient(160deg, #3A2E10, #1B2B45 60%); border:2px solid #E3B53F; }
.ch-finie canvas{ width:96px; height:auto; image-rendering:pixelated; border-radius:6px; }
.ch-finie div{ display:flex; flex-direction:column; gap:3px; min-width:0; }
.ch-finie b{ font-size:0.9rem; }
.ch-finie small{ font-size:0.74rem; color: var(--brume); }
.ch-album-titre{ margin-top:14px; }
/* l'album : un monument restauré passe en or */
.mon.restaure{ background: linear-gradient(135deg, #FFF6D0, #F0B429 30%, #FFE7A0 52%, #B7791F 78%, #FCE38A);
  box-shadow: 0 0 0 1px rgba(255,214,107,0.6), 0 8px 22px rgba(240,180,41,0.35); }
.mon-restaure{ position:absolute; left:5px; top:5px; padding:1px 6px 2px; border-radius:5px; background:rgba(11,26,51,0.85);
  color:#FFD56B; font-family: var(--titre); font-weight:800; font-size:0.7rem; letter-spacing:0.06em; text-transform:uppercase; }
.mon-grave{ margin:0; padding:0 8px; font-size:0.7rem; font-weight:700; color:#8A6410;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.mon.libre .mon-grave, .mon.pris .mon-grave{ color:#6B5A2A; }
@media (max-width: 560px){
  .ch-choix{ grid-template-columns:repeat(2, minmax(0, 1fr)); gap:8px; }
  .ch-mon b{ font-size:0.8rem; }
  .ch-boite{ padding:2px 7px 4px; }
  .ch-voile{ top:56%; padding:10px 12px; gap:5px; font-size:0.8rem; }
}
"""
f.write_text(s, encoding='utf-8')
print('patch311 appliqué')
