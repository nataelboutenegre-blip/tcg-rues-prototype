#!/usr/bin/env python3
# patch439 : le pass de saison en vitrine (habillage Topo, même interrupteur que la boutique : interface.vitrine).
# La piste devient verticale et montre les vrais objets. Avec s3-13 : paquets à ouvrir depuis le pass,
# lingots, niveaux bonus, aperçu du modérateur (?pass=test). Le bloc « défis » ne s'affiche que si le
# serveur l'envoie (e.defis) : pas encore codé côté serveur.
import io, sys
A = 'app.js'; S = 'style.css'
a = io.open(A, encoding='utf-8').read()
s = io.open(S, encoding='utf-8').read()
if 'patch439' in a or 'patch439' in s: sys.exit('patch439 déjà appliqué')

def rempl(t, avant, apres, n=1):
    assert t.count(avant) == n, (t.count(avant), avant[:70])
    return t.replace(avant, apres)

JS = r"""// ---------- patch439 : le pass en vitrine ----------
const PSX_TYPE = { tp: 'TerraPoints', energie: 'Énergie', titre: 'Titre de profil', dos: 'Dos de carte', habillage: 'Habillage de paquet', skin: 'Skin de carte', paquet: '5 communes', lingots: 'Lingots' };
const PSX_LINGOT = '<svg viewBox="0 0 56 56" aria-hidden="true"><path d="M17 20h22l9 18H8z" fill="#F0B429" stroke="#7A5410" stroke-width="2.2" stroke-linejoin="round"/><path d="M17 20h22l3 6H14z" fill="#FFE08A"/></svg>';
function psxSachet(id){
  const p = makePackEl('achete');
  const t = p.querySelector('.paquet-titre'), bd = p.querySelector('.paquet-bande');
  const dep = id === 'paquet-departement';
  if(t) t.textContent = dep ? 'Département' : 'Garanti';
  if(bd) bd.textContent = dep ? '5 communes' : '1 rare ou mieux';
  return '<div class="psx-sachet" aria-hidden="true">' + p.outerHTML.replace(/^<button/, '<div').replace(/<\/button>$/, '</div>') + '</div>';
}
function psxVisuel(r){
  const t = r.type;
  if(t === 'dos') return dosApercuHtml(r.valeur);
  if(t === 'skin') return skinVignetteHtml(skinCle(r.valeur));
  if(t === 'habillage') return habVignette(habCle(r.valeur));
  if(t === 'paquet') return psxSachet(r.valeur);
  if(t === 'titre') return `<span class="psx-titre">${echapperTexte(String(r.nom || '').replace(/^Titre\s*/, '').replace(/[«»]/g, '').trim())}</span>`;
  if(t === 'lingots') return `<span class="psx-qte">${PSX_LINGOT}<b>${Number(r.quantite)}</b></span>`;
  return `<span class="psx-qte">${PS_ICO[t] || ''}<b>${t === 'energie' ? '+' : ''}${Number(r.quantite)}</b></span>`;
}
function psxDepSelect(){
  const deps = Object.keys(DEPT_NAMES).filter(d => !estCanton(d)).sort((x, y) => x.localeCompare(y, 'fr', { numeric: true }));
  return `<select class="psx-dep" aria-label="Département"><option value="">Choisis un département</option>${deps.map(d => `<option value="${d}">${d} · ${echapperTexte(DEPT_NAMES[d])}</option>`).join('')}</select>`;
}
// le bouton d'une récompense prête : un paquet s'ouvre, le reste se réclame
const psxBouton = (r, cls) => r.type === 'paquet'
  ? `<button type="button" class="${cls}" data-ps-paquet="${r.niveau}">Ouvrir</button>`
  : `<button type="button" class="${cls}" data-ps-reclamer="${r.niveau}">Réclamer</button>`;
const psxDep = (r) => r.type === 'paquet' && r.valeur === 'paquet-departement' ? psxDepSelect() : '';
const psxNom = (r) => r.type === 'titre' ? String(r.nom || '').replace(/^Titre\s*/, '').replace(/[«»]/g, '').trim() : r.nom;
function renderPassLuxe(el, e){
  const nb = (n) => Number(n || 0).toLocaleString('fr-FR');
  const jours = psJours(e);
  const fini = e.niveau >= e.niveaux;
  const bonusOn = Number(e.bonus_xp) > 0 && Number(e.bonus_tp) > 0;
  const bonusDans = fini && bonusOn ? Math.max(0, Number(e.xp) - e.niveaux * e.xp_niveau) % Number(e.bonus_xp) : 0;
  const bonusDus = bonusOn ? Number(e.bonus_dus || 0) : 0;
  const pct = fini ? (bonusOn ? Math.round(100 * bonusDans / Number(e.bonus_xp)) : 100) : Math.round(100 * e.dans_niveau / e.xp_niveau);
  const jourXp = Number(e.jour_quetes || 0) + Number(e.jour_actions || 0);
  const recs = e.recompenses;
  const prets = recs.filter(r => psEtatRecompense(r, e) === 'pret');
  const directs = prets.filter(r => r.type !== 'paquet').length;   // « Tout réclamer » laisse les paquets : ils s'ouvrent
  const payantes = recs.filter(r => r.payant);
  const atteintesPass = payantes.filter(r => r.niveau <= e.niveau).length;
  // le contenu du pass, en clair : « 2 dos, 2 paquets, 2 skins et 4 titres »
  const mots = { dos: ['dos', 'dos'], habillage: ['habillage de paquet', 'habillages de paquet'], skin: ['skin', 'skins'], titre: ['titre', 'titres'] };
  const parts = Object.keys(mots).map(k => { const n = payantes.filter(r => r.type === k).length; return n ? `${n} ${mots[k][n > 1 ? 1 : 0]}` : ''; }).filter(Boolean);
  const contenu = parts.length > 1 ? parts.slice(0, -1).join(', ') + ' et ' + parts[parts.length - 1] : parts.join('');
  // à la une : ce qui est à réclamer, sinon la prochaine récompense
  const une = prets[0] || recs.find(r => r.niveau === e.niveau + 1) || null;
  let uneHtml = '';
  if(une){
    const aReclamer = prets[0] === une, verrou = une.payant && !e.possede;
    uneHtml = `<div class="bqx-une psx-une${une.payant ? ' pass' : ''} t-${une.type}">
        <div class="psx-une-vis">${psxVisuel(une)}</div>
        <div class="bqx-une-txt">
          <span class="bqx-sur">${aReclamer ? 'À réclamer' : 'Prochaine récompense'} · niveau ${une.niveau}</span>
          <b class="bqx-une-nom">${echapperTexte(psxNom(une))}</b>
          <span class="bqx-une-dept">${PSX_TYPE[une.type] || ''}${une.payant ? ' · avec le pass' : ' · pour tous'}</span>
          ${aReclamer ? psxDep(une) + psxBouton(une, 'psx-cta')
            : `<span class="psx-reste">Encore <b>${nb(e.xp_niveau - e.dans_niveau)} XP</b></span>${verrou ? `<span class="psx-verrou">${PS_CADENAS}Avec le pass</span>` : ''}`}
        </div></div>`;
  }
  const achat = e.possede
    ? `<div class="psx-achat ok"><div><b>Pass débloqué ✓</b><p>Les ${payantes.length} récompenses du pass sont à toi, au fil des niveaux. Merci pour ton soutien !</p></div></div>`
    : e.en_vente && e.actif
      ? `<div class="psx-achat"><div><b>Pass complet</b><p>${contenu}.${atteintesPass ? ` Tu reçois tout de suite ${atteintesPass > 1 ? `les ${atteintesPass} déjà atteintes` : 'celle déjà atteinte'}.` : ''} Achat unique, gardé à vie.</p></div><button type="button" class="psx-cta" data-ps-acheter>${e.prix ? euros(e.prix) : 'Voir'}</button></div>`
      : `<div class="psx-achat"><div><b>Pass complet</b><p>${e.actif ? 'Bientôt en vente.' : 'La saison est terminée.'}</p></div></div>`;
  const defis = Array.isArray(e.defis) && e.defis.length ? `<div class="psx-defis">
      <div class="psx-h2"><h2>Défis de la semaine</h2><span>${e.defis.filter(d => d.fait).length} sur ${e.defis.length}${e.defis_fin ? ' · ' + echapperTexte(e.defis_fin) : ''}</span></div>
      ${e.defis.map(d => `<div class="psx-defi${d.fait ? ' fait' : ''}"><div class="l"><b>${echapperTexte(d.nom)}</b><span>${d.fait ? '✓ ' : ''}+${nb(d.xp)} XP</span></div>
        <div class="psx-jauge"><i style="width:${Math.min(100, Math.round(100 * d.n / d.sur))}%"></i></div><small>${nb(Math.min(d.n, d.sur))} / ${nb(d.sur)}</small></div>`).join('')}</div>` : '';
  const lignes = recs.map(r => {
    const st = psEtatRecompense(r, e), verrou = r.payant && !e.possede;
    const etat = st === 'recu' ? '<span class="psx-ok">✓ Reçu</span>'
      : st === 'pret' ? psxBouton(r, 'psx-recl')
      : verrou ? `<span class="psx-verrou">${PS_CADENAS}Pass</span>`
      : st === 'bientot' ? '<span class="psx-loin">Bientôt</span>' : '';
    return `<li class="psx-l${r.niveau <= e.niveau ? ' atteint' : ''}${r.niveau === e.niveau + 1 ? ' courant' : ''}${r.payant ? ' pass' : ''}${st === 'recu' ? ' recu' : ''}">
        <span class="psx-n">${r.niveau}</span>
        <div class="psx-carte"><div class="psx-vis t-${r.type}">${psxVisuel(r)}</div>
          <div class="psx-txt"><b>${echapperTexte(psxNom(r))}</b><span>${PSX_TYPE[r.type] || ''}</span>${st === 'pret' ? psxDep(r) : ''}</div>
          <div class="psx-etat">${etat}</div></div></li>`;
  }).join('');
  const bonus = bonusOn ? `<li class="psx-l bonus${fini ? ' courant' : ''}"><span class="psx-n">+</span>
        <div class="psx-carte"><div class="psx-vis t-tp"><span class="psx-qte">${PS_ICO.tp}<b>${nb(e.bonus_tp)}</b></span></div>
          <div class="psx-txt"><b>Niveaux bonus</b><span>${fini ? `${nb(bonusDans)} / ${nb(e.bonus_xp)} XP vers les prochains ${nb(e.bonus_tp)} TP`
            : `Après le niveau ${e.niveaux} : ${nb(e.bonus_tp)} TP tous les ${nb(e.bonus_xp)} XP, jusqu’à la fin de la saison`}</span></div>
          <div class="psx-etat">${bonusDus ? `<button type="button" class="psx-recl" data-ps-bonus>+${nb(bonusDus * Number(e.bonus_tp))} TP</button>` : ''}</div></div></li>` : '';
  el.innerHTML = `<div class="psx">
      <div class="psx-tete">
        <span class="bqx-sur">Pass de la saison ${echapperTexte(nomSaison(e.saison).replace('Saison ', ''))} · ${e.apercu ? 'aperçu, toi seul' : e.actif ? `encore ${jours} jour${jours > 1 ? 's' : ''}` : 'saison terminée'}</span>
        <h1 class="psx-h1">${echapperTexte(e.nom)}</h1>
        <div class="psx-niveau"><span class="psx-pastille">${e.niveau}</span>
          <div class="psx-barre"><div class="l"><span><b>Niveau ${e.niveau}</b> sur ${e.niveaux}</span><span>${fini ? (bonusOn ? `Bonus · ${nb(bonusDans)} / ${nb(e.bonus_xp)} XP` : 'Pass terminé') : `${nb(e.dans_niveau)} / ${nb(e.xp_niveau)} XP`}</span></div>
            <div class="psx-jauge"><i style="width:${pct}%"></i></div>
            <div class="psx-jour">${e.apercu ? 'Le pass ouvrira avec la saison 3. Les joueurs ne le voient pas encore.' : e.actif ? `Aujourd’hui : ${nb(jourXp)} XP gagnés` : 'Réclame tes récompenses avant qu’elles disparaissent.'}</div></div></div>
      </div>
      ${uneHtml}
      ${achat}
      ${defis}
      <div class="psx-h2"><h2>Les ${e.niveaux} niveaux</h2>${directs > 1 ? `<button type="button" class="psx-recl" data-ps-tout>Tout réclamer (${directs})</button>` : '<span>Impairs : pour tous · pairs : pass</span>'}</div>
      <ol class="psx-piste">${lignes}${bonus}</ol>
      <div class="psx-infos">
        <div><h3>Gagner de l’XP</h3><ul>
          <li>Chaque quête du jour réclamée <b>+${e.xp_quete} XP</b></li>
          <li>Conquête ou défense réussie <b>+30 XP</b></li>
          <li>Duel classé, Commune du jour <b>+20 XP</b></li>
          <li>Paquet Terra ouvert <b>+10 XP</b></li>
          <li>Plafond des actions <b>${nb(e.plafond_actions)} XP / jour</b></li></ul></div>
        <p>Tout ce que tu gagnes se garde à vie. Le pass payant ne donne que de l’apparence : rien qui fasse gagner au Front. Les titres se choisissent dans ton profil, les objets dans Profil › Personnaliser.</p>
      </div>
    </div>`;
  try{ habGl.demarrer(); }catch(err){}
}
function renderPass(){"""
a = rempl(a, "function renderPass(){", JS)
a = rempl(a, """    el.innerHTML = '<p class="collection-empty">Le pass de saison arrive bientôt : tes quêtes du jour le feront avancer.</p>';
    return;
  }
  const jours = psJours(e);""", """    el.innerHTML = '<p class="collection-empty">Le pass de saison arrive bientôt : tes quêtes du jour le feront avancer.</p>';
    return;
  }
  if(bqLuxe()){ renderPassLuxe(el, e); return; }   // patch439
  const jours = psJours(e);""")


# ---- s3-13 côté jeu : aperçu du modérateur, titres, paquets, bonus
a = rempl(a, "const CANTONS = {", """// patch439 : ?pass=test montre au modérateur le pass avant son ouverture (le serveur ne l'envoie qu'à lui)
const PASS_TEST = (() => {
  try {
    if(/[?&]pass=test\\b/.test(location.search)) sessionStorage.setItem('tf-pass-test', '1');
    return sessionStorage.getItem('tf-pass-test') === '1';
  } catch(e){ return /[?&]pass=test\\b/.test(location.search); }
})();
const CANTONS = {""")
a = rempl(a, """  'pass-s2-brumes': 'Gardien des brumes', 'pass-s2-legende': 'Légende de la saison 2', 'pass-s2-veteran': 'Vétéran de la saison 2' };""",
"""  'pass-s2-brumes': 'Gardien des brumes', 'pass-s2-legende': 'Légende de la saison 2', 'pass-s2-veteran': 'Vétéran de la saison 2',
  // patch439 : le pass de la saison 3
  'pass-s3-mecene': 'Mécène d’automne', 'pass-s3-recrue': 'Recrue d’automne', 'pass-s3-vignes': 'Seigneur des vignes',
  'pass-s3-brumes': 'Gardien des brumes', 'pass-s3-legende': 'Légende de la saison 3', 'pass-s3-veteran': 'Vétéran de la saison 3' };""")
a = rempl(a, """    passEtat = error ? null : data;
  }catch(e){ passEtat = null; }""", """    passEtat = error ? null : data;
    if(passEtat && passEtat.apercu && !PASS_TEST) passEtat = null;   // patch439
  }catch(e){ passEtat = null; }""")
# le paquet gagné dans le pass passe par la table de tirage, comme un paquet de boutique
a = rempl(a, """  if(boutiqueAchat && boutiqueAchat.collection){
    // patch112 : paquet d'une collection thematique""", """  if(boutiqueAchat && boutiqueAchat.pass != null){
    // patch439 : paquet gagné dans le pass de saison
    const achat = boutiqueAchat;
    boutiqueAchat = null;
    const { data, error } = await sb.rpc('pass_ouvrir_paquet', { p_niveau: achat.pass, p_departement: achat.dep });
    terraPaquet = error ? null : (data || []);
    terraPaquetBloque = true;
    boutiqueOuvert = !error;
    viderBilanTerra();
    return error;
  }
  if(boutiqueAchat && boutiqueAchat.collection){
    // patch112 : paquet d'une collection thematique""")
a = rempl(a, """async function passAcheter(){""", """// patch439 : ouvrir un paquet du pass (même chemin qu'un paquet de boutique)
async function passOuvrirPaquet(niveau, sel){
  const e = passEtat, r = e && e.recompenses ? e.recompenses.find(x => x.niveau === Number(niveau)) : null;
  if(!r) return;
  if(paquetEnCours){ notifier({ type: 'erreur', titre: 'Un paquet t\\'attend déjà', texte: 'Ouvre d\\'abord celui qui est sur la table.' }); return; }
  let dep = null;
  if(r.valeur === 'paquet-departement'){
    dep = sel ? sel.value : '';
    if(!dep){ notifier({ type: 'erreur', titre: 'Choisis d\\'abord un département' }); if(sel) sel.focus(); return; }
  }
  boutiqueAchat = { pass: Number(niveau), dep };
  boutiqueOuvert = false;
  const tirage = document.querySelector('.tab[data-tab="tirage"]');
  if(tirage) tirage.click();
  await openPack('achete');
  boutiqueAchat = null;
  chargerPass();
  if(!boutiqueOuvert) return;
  const bande = document.querySelector('#packZone .paquet .paquet-bande');
  if(bande) bande.textContent = dep ? (DEPT_NAMES[dep] || dep) + ' (' + dep + ')' : '1 rare ou mieux';
  const titre = document.querySelector('#packZone .paquet .paquet-titre');
  if(titre) titre.textContent = dep ? 'Département' : 'Garanti';
}
async function passBonus(bouton){
  if(bouton) bouton.disabled = true;
  const { data, error } = await sb.rpc('pass_bonus_reclamer');
  if(error){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible(error.message) }); if(bouton) bouton.disabled = false; return; }
  passEtat = data;
  notifier({ type: 'succes', titre: 'Niveaux bonus', texte: '+' + Number(data.bonus_gain || 0).toLocaleString('fr-FR') + ' TP' });
  renderPassQG(); renderPass();
  if(typeof loadPackStatus === 'function') loadPackStatus();
}
async function passAcheter(){""")
a = rempl(a, """  if(t.closest('[data-ps-acheter]')) passAcheter();""", """  if(t.closest('[data-ps-acheter]')) passAcheter();
  const pq = t.closest('[data-ps-paquet]');   // patch439
  if(pq){ const boite = pq.closest('.psx-une, .psx-l, .ps-niv'); passOuvrirPaquet(pq.dataset.psPaquet, boite ? boite.querySelector('select.psx-dep') : null); return; }
  const bn = t.closest('[data-ps-bonus]');
  if(bn){ passBonus(bn); return; }""")
a = rempl(a, """             texte: r ? r.nom + (r.type === 'titre' ? ' : choisis-le dans ton profil.' : r.type === 'dos' || r.type === 'habillage' || r.type === 'skin' ? ' : dans Profil › Personnaliser.' : '') : '' });""",
"""             texte: (r ? r.nom + (r.type === 'titre' ? ' : choisis-le dans ton profil.' : r.type === 'dos' || r.type === 'habillage' || r.type === 'skin' ? ' : dans Profil › Personnaliser.' : '') : '')
               + (Number(data.tp_repli) > 0 ? ` Réserve de lingots pleine : ${Number(data.tp_repli)} TP à la place.` : '') });   // patch439""")
# l'ancienne piste (interrupteur vitrine éteint) reste utilisable avec les nouvelles récompenses
a = rempl(a, """const PS_TYPE = { tp: 'TerraPoints', energie: 'Énergie', titre: 'Titre', dos: 'Dos de carte', habillage: 'Habillage de paquet', skin: 'Skin de carte' };""",
"""const PS_TYPE = { tp: 'TerraPoints', energie: 'Énergie', titre: 'Titre', dos: 'Dos de carte', habillage: 'Habillage de paquet', skin: 'Skin de carte', paquet: '5 communes', lingots: 'Lingots' };""")
a = rempl(a, """      : st === 'pret' ? `<button type="button" class="ps-etat recl" data-ps-reclamer="${r.niveau}">Réclamer</button>`""",
"""      : st === 'pret' ? psxDep(r) + psxBouton(r, 'ps-etat recl')""")
a = rempl(a, """        <div class="ps-ico">${PS_ICO[r.type] || ''}</div>""", """        <div class="ps-ico">${PS_ICO[r.type] || (r.type === 'lingots' ? PSX_LINGOT : r.type === 'paquet' ? PS_ICO.habillage : '')}</div>""")
a = rempl(a, """${prets > 1 ? `<button type="button" class="qg-btn plein" data-ps-tout>Tout réclamer (${prets})</button>` : '<span>Niveaux impairs : pour tous · niveaux pairs : pass</span>'}</div>""",
"""${prets > 1 ? `<button type="button" class="qg-btn plein" data-ps-tout>Tout réclamer (${prets})</button>` : '<span>Niveaux impairs : pour tous · niveaux pairs : pass</span>'}${Number(e.bonus_dus) > 0 ? `<button type="button" class="qg-btn plein" data-ps-bonus>Niveaux bonus : +${Number(e.bonus_dus) * Number(e.bonus_tp)} TP</button>` : ''}</div>""")

css = io.open('_patchs/patch439.css', encoding='utf-8').read().replace('VV ', 'html.topo:not(.sans-vitrine) ')
s = s.rstrip('\n') + '\n\n' + css
io.open(A, 'w', encoding='utf-8').write(a)
io.open(S, 'w', encoding='utf-8').write(s)
print('patch439 appliqué')
