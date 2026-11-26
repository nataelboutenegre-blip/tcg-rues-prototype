// patch543 : l'éditeur, version 2 (ornements, atelier à calques)
function blDeviseTexte(b, nom, tag){ return b.devise === 'nom' ? (nom || '') : b.devise === 'sigle' ? (tag || '') : ''; }
function blOptsEdition(){ const E = clanEdition; return { orne: true, devise: blDeviseTexte(E.b, E.nom, E.tag) }; }
// une icône de meuble pour les listes (boîte de 40 ou de 100)
function blMeubleIcone(m, couleur){
  if(!m.d) return '<svg viewBox="0 0 40 40" aria-hidden="true"><path d="M10 10L30 30M30 10L10 30" stroke="#5B6E8C" stroke-width="2.5"/></svg>';
  const vb = m.cent ? '0 0 100 100' : '0 0 40 40', c = couleur || '#E6EDF7';
  return `<svg viewBox="${vb}" aria-hidden="true">${m.trait ? `<path d="${m.d}" fill="none" stroke="${c}" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/>` : `<path d="${m.d}" fill-rule="evenodd" fill="${c}"/>`}</svg>`;
}
function blOrnementsHtml(E, B, bt, pastilles){
  const timbre = (k) => `<svg viewBox="-38 -44 176 70" aria-hidden="true">${blOrnements(blasonNet({ ...B, manteau:'aucun', devise:'aucune', timbre:k }), null, 'blt' + k).apres || '<path d="M30 -20L70 10M70 -20L30 10" stroke="#5B6E8C" stroke-width="5"/>'}</svg>`;
  return `<h2>Ornements <small class="bl-petit">(sur les grands blasons)</small></h2>
    <div class="bl-deux"><div><h3 class="bl-h3">Manteau</h3><div class="bl-seg">${bt('manteau', 'aucun', 'Aucun')}${bt('manteau', 'manteau', 'Manteau')}</div>
      ${B.manteau === 'manteau' ? `<div class="bl-emaux bl-marge">${pastilles('cmanteau')}</div>` : ''}</div>
      <div><h3 class="bl-h3">Devise</h3><div class="bl-seg">${bt('devise', 'aucune', 'Aucune')}${bt('devise', 'nom', 'Nom')}${bt('devise', 'sigle', 'Sigle')}</div>
      ${B.devise !== 'aucune' ? `<div class="bl-emaux bl-marge">${pastilles('cdevise')}</div>` : ''}</div></div>
    <h3 class="bl-h3">Au-dessus de l’écu</h3><div class="bl-choix bl-timbres">${Object.entries(BL_TIMBRES).map(([k, t]) =>
      blVerrou(k, t, B.timbre, bt('timbre', k, `${timbre(k)}<span>${t.nom}</span>`))).join('')}</div>
    ${blRares < 2 ? `<p class="clan-note">🔒 La couronne comtale (1<sup>re</sup> semaine d’or) et la couronne royale (2<sup>e</sup>) se gagnent avec l’or de l’objectif de clan.</p>` : ''}`;
}
function blAtelierHtml(E, B, bt){
  const i = Math.min(E.cq || 0, B.calques.length - 1), c = B.calques[i];
  const liste = B.calques.map((q, j) => `<div class="bl-cq${j === i ? ' on' : ''}"><button type="button" class="bl-cq-choisir" data-bl-cq="${j}" aria-pressed="${j === i}">${blMeubleIcone(BL_MEUBLES[q.m], BL_E[q.c])}<b>${BL_MEUBLES[q.m].nom}</b></button>
      <button type="button" class="bl-cq-mini" data-bl-cq-haut="${j}" aria-label="Passer devant"${j === B.calques.length - 1 ? ' disabled' : ''}>⇡</button>
      <button type="button" class="bl-cq-mini" data-bl-cq-suppr="${j}" aria-label="Retirer">✕</button></div>`).join('');
  const champ = (k, nom, min, max, pas, unite) => `<label class="bl-curseur"><span>${nom}</span><input type="range" data-bl-cq-champ="${k}" min="${min}" max="${max}" step="${pas}" value="${c[k]}"><output id="blCqO${k}">${c[k]}${unite}</output></label>`;
  return `<h2>Atelier <small class="bl-petit">${B.calques.length} / ${BL_CALQUES_MAX} meubles</small></h2>
    <div class="bl-atelier"><div class="bl-at-ecu">${blasonSvgTag(B, null, 'id="blApercu" class="bl-glisse"')}<small>Fais glisser le meuble choisi sur l’écu.</small></div>
      <div class="bl-cqs">${liste}</div></div>
    ${champ('s', 'Taille', 25, 220, 5, ' %')}${champ('r', 'Rotation', 0, 355, 5, '°')}${champ('x', 'Position X', 0, 100, 1, '')}${champ('y', 'Position Y', 0, 120, 1, '')}
    <div class="bl-at-actions"><button type="button" class="bq-btn secondaire" data-bl-cq-f aria-pressed="${c.f}">↔ Retourner</button>
      <button type="button" class="bq-btn secondaire" data-bl-cq-dup${B.calques.length >= BL_CALQUES_MAX ? ' disabled' : ''}>Dupliquer</button>
      <button type="button" class="bq-btn secondaire" data-bl-cq-add${B.calques.length >= BL_CALQUES_MAX ? ' disabled' : ''}>+ Ajouter un meuble</button></div>
    <h3 class="bl-h3">Couleur de ce meuble</h3><div class="bl-emaux">${BL_EMAUX.map(([k, nom, col]) => `<button type="button" data-bl-cqc="${k}" aria-pressed="${c.c === k}" aria-label="${nom}" title="${nom}" style="background:${col}"></button>`).join('')}</div>
    <h3 class="bl-h3">Ce meuble</h3><div class="bl-choix bl-meubles">${Object.entries(BL_MEUBLES).filter(([k]) => k !== 'aucun').map(([k, m]) =>
      blVerrou(k, m, B.calques.some(q => q.m === k) ? k : B.meuble, `<button type="button" data-bl-cqm="${k}" aria-pressed="${c.m === k}">${blMeubleIcone(m)}<span>${m.nom}</span></button>`)).join('')}</div>
    <p><button type="button" class="bq-btn secondaire" data-bl-cq-fin>Revenir à un meuble simple</button></p>`;
}
// l'aperçu suit les curseurs et le doigt sans tout redessiner
function blApercuMaj(){
  const B = clanEdition && clanEdition.b;
  if(!B) return;
  const a = document.getElementById('blApercu');
  if(a){ a.setAttribute('viewBox', '0 0 100 120'); a.innerHTML = blasonSVG(B); }
  const g = document.querySelector('.bl-edition .bl-grand');
  if(g){ const o = blOptsEdition(), orne = blAOrnements(blasonNet(B)); g.setAttribute('viewBox', orne ? BL_BOITE_ORNE : '0 0 100 120'); g.innerHTML = blasonSVG(B, orne ? o : null); }
  const c = B.calques[clanEdition.cq || 0];
  if(c) ['s', 'r', 'x', 'y'].forEach(k => { const o = document.getElementById('blCqO' + k), r = document.querySelector(`[data-bl-cq-champ="${k}"]`);
    if(o) o.textContent = c[k] + (k === 's' ? ' %' : k === 'r' ? '°' : ''); if(r && document.activeElement !== r) r.value = c[k]; });
}
function blRerendre(){ const y = window.scrollY; renderClan(); window.scrollTo(0, y); }
// les actions de l'atelier ; renvoie true si le clic est traité
function blAtelierClic(b){
  const E = clanEdition, B = E && E.b;
  if(!B) return false;
  const tout = () => { blRerendre(); return true; };
  if(b.hasAttribute('data-bl-atelier')){
    const M = BL_MEUBLES[B.meuble];
    B.calques = !M || !M.d ? [blCalqueNet({ m:'etoile', c:B.cm, x:50, y:56, s:100 })]
      : B.nombre === 3 ? [[32, 38], [68, 38], [50, 80]].map(([x, y]) => blCalqueNet({ m:B.meuble, c:B.cm, x, y, s:50 }))
      : [blCalqueNet({ m:B.meuble, c:B.cm, x:50, y:B.forme === 'rond' ? 60 : 56, s:100 })];
    E.cq = 0; return tout();
  }
  if(!B.calques.length) return false;
  const i = Math.min(E.cq || 0, B.calques.length - 1), c = B.calques[i];
  if(b.dataset.blCq !== undefined){ E.cq = Number(b.dataset.blCq); return tout(); }
  if(b.dataset.blCqHaut !== undefined){ const j = Number(b.dataset.blCqHaut); if(j < B.calques.length - 1){ [B.calques[j], B.calques[j + 1]] = [B.calques[j + 1], B.calques[j]]; E.cq = j + 1; } return tout(); }
  if(b.dataset.blCqSuppr !== undefined){ B.calques.splice(Number(b.dataset.blCqSuppr), 1); E.cq = Math.max(0, Math.min(E.cq, B.calques.length - 1));
    if(!B.calques.length) B.meuble = 'aucun'; return tout(); }
  if(b.hasAttribute('data-bl-cq-f')){ c.f = !c.f; return tout(); }
  if(b.hasAttribute('data-bl-cq-dup')){ if(B.calques.length < BL_CALQUES_MAX){ B.calques.push(blCalqueNet({ ...c, x: Math.min(100, c.x + 10), y: Math.min(120, c.y + 10) })); E.cq = B.calques.length - 1; } return tout(); }
  if(b.hasAttribute('data-bl-cq-add')){ if(B.calques.length < BL_CALQUES_MAX){ B.calques.push(blCalqueNet({ m:'etoile', c:B.cm, x:50, y:56, s:60 })); E.cq = B.calques.length - 1; } return tout(); }
  if(b.dataset.blCqc){ c.c = b.dataset.blCqc; return tout(); }
  if(b.dataset.blCqm){ c.m = b.dataset.blCqm; return tout(); }
  if(b.hasAttribute('data-bl-cq-fin')){ const p = B.calques[0]; B.meuble = p ? p.m : 'aucun'; B.cm = p ? p.c : B.cm; B.nombre = 1; B.calques = []; return tout(); }
  return false;
}
// curseurs
document.addEventListener('input', (e) => {
  const r = e.target.closest && e.target.closest('[data-bl-cq-champ]');
  if(!r || !clanEdition || !clanEdition.b.calques.length) return;
  const c = clanEdition.b.calques[clanEdition.cq || 0];
  if(!c) return;
  c[r.dataset.blCqChamp] = Number(r.value);
  blApercuMaj();
});
// glisser du doigt sur l'écu de l'atelier
let blGlisse = null;
document.addEventListener('pointerdown', (e) => {
  const svg = e.target.closest && e.target.closest('#blApercu');
  if(!svg || !clanEdition || !clanEdition.b.calques.length) return;
  e.preventDefault();
  blGlisse = { svg, id: e.pointerId };
  try { svg.setPointerCapture(e.pointerId); } catch(_){}
  blGlisser(e);
});
function blGlisser(e){
  if(!blGlisse || e.pointerId !== blGlisse.id) return;
  const m = blGlisse.svg.getScreenCTM();
  if(!m) return;
  const p = new DOMPoint(e.clientX, e.clientY).matrixTransform(m.inverse());
  const c = clanEdition && clanEdition.b.calques[clanEdition.cq || 0];
  if(!c) return;
  c.x = Math.round(Math.min(100, Math.max(0, p.x))); c.y = Math.round(Math.min(120, Math.max(0, p.y)));
  blApercuMaj();
}
document.addEventListener('pointermove', (e) => { if(blGlisse){ e.preventDefault(); blGlisser(e); } }, { passive: false });
['pointerup', 'pointercancel'].forEach(t => document.addEventListener(t, (e) => { if(blGlisse && e.pointerId === blGlisse.id) blGlisse = null; }));
