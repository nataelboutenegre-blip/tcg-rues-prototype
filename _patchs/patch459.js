
// ---------- patch459 : les lauriers du podium des clans (s3-29) ----------
// clans_blasons() donne laurier_rang (1, 2, 3), laurier_saison et laurier_masque. Rien tant que le serveur n'en donne pas.
let LAURIER_N = 0;
function laurierSVG(rang, petit){
  const C = { 1: ['#FFE6A0', '#F0B429', '#9A6A12', '#6B4708'], 2: ['#FFFFFF', '#CFD8E4', '#8D99AB', '#5D6878'], 3: ['#F6C79A', '#C98A4B', '#8A5226', '#5E3515'] }[rang] || null;
  if(!C) return '';
  const id = 'lr' + (++LAURIER_N);
  const cx = 50, cy = 64, rx = 64, ry = 70;
  const pt = (t) => [cx - rx * Math.sin(t), cy + ry * Math.cos(t)];
  const n = petit ? 5 : 10, t0 = 0.32, t1 = 2.55;
  let tige = '', feuilles = '';
  const branche = (sens) => {
    const P = [];
    for(let i = 0; i <= 30; i++){ const t = t0 + (t1 - t0) * i / 30; const [x, y] = pt(t); P.push([sens < 0 ? x : 100 - x, y]); }
    tige += `<path d="M${P.map(p => p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' L')}" fill="none" stroke="${C[3]}" stroke-width="${petit ? 4.2 : 2.6}" stroke-linecap="round"/>`;
    for(let i = 0; i < n; i++){
      const t = t0 + 0.12 + (t1 - t0 - 0.12) * i / (n - 1);
      let [x, y] = pt(t); if(sens > 0) x = 100 - x;
      const [x2, y2] = pt(t + 0.01); const dx = (sens > 0 ? 100 - x2 : x2) - x, dy = y2 - y;
      const a = Math.atan2(dy, dx) * 180 / Math.PI;
      const k = (petit ? 1.75 : 1) * (1.15 - 0.45 * i / (n - 1));
      for(const cote of [-1, 1]){
        const ang = a + cote * 38 * (sens > 0 ? -1 : 1);
        feuilles += `<path transform="translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${ang.toFixed(1)}) scale(${k.toFixed(2)})" d="M0 0 C5 -5.2 13 -5.2 19 0 C13 4.4 5 4.4 0 0Z" fill="url(#${id})" stroke="${C[3]}" stroke-width="${petit ? 1.1 : .8}"/>`
          + (petit ? '' : `<path transform="translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${ang.toFixed(1)}) scale(${k.toFixed(2)})" d="M1.5 0 L16 0" stroke="${C[2]}" stroke-width=".7" opacity=".7"/>`);
      }
      // une baie entre les feuilles
      if(!petit && i % 3 === 1){ feuilles += `<circle cx="${(x + (sens > 0 ? 5 : -5)).toFixed(1)}" cy="${(y - 2).toFixed(1)}" r="2.2" fill="${C[1]}" stroke="${C[3]}" stroke-width=".7"/>`; }
    }
    // la pointe
    const [xe, ye] = pt(t1 + 0.08); const xt = sens > 0 ? 100 - xe : xe;
    feuilles += `<path transform="translate(${xt.toFixed(1)} ${ye.toFixed(1)}) rotate(${sens > 0 ? -60 : -120}) scale(${petit ? 1.4 : .8})" d="M0 0 C5 -5.2 13 -5.2 19 0 C13 4.4 5 4.4 0 0Z" fill="url(#${id})" stroke="${C[3]}" stroke-width=".8"/>`;
  };
  branche(-1); branche(1);
  const noeud = `<g transform="translate(50 ${cy + ry - 1})"><path d="M-3 0 L-12 13 L-7 12 L-5 17 L0 3Z M3 0 L12 13 L7 12 L5 17 L0 3Z" fill="${C[1]}" stroke="${C[3]}" stroke-width="1"/><ellipse rx="5.5" ry="4" fill="${C[1]}" stroke="${C[3]}" stroke-width="1.1"/></g>`;
  return `<svg class="laurier-svg" viewBox="-26 -14 152 162" aria-hidden="true"><defs><linearGradient id="${id}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${C[0]}"/><stop offset=".5" stop-color="${C[1]}"/><stop offset="1" stop-color="${C[2]}"/></linearGradient></defs>${tige}${feuilles}${petit ? '' : noeud}</svg>`;
}

function laurierDe(tag){
  const bl = BLASONS.get(tag);
  return bl && bl.laurier && !bl.laurier.masque ? bl.laurier.rang : 0;
}
function laurierAutour(html, tag, petit){
  const r = laurierDe(tag);
  return r ? `<span class="lr${petit ? ' petit' : ''} lr${r}">${laurierSVG(r, petit)}${html}</span>` : html;
}
const LAURIER_NOMS = { 1: 'Laurier d’or', 2: 'Laurier d’argent', 3: 'Laurier de bronze' };
const LAURIER_TXT = { 1: 'Clan champion', 2: '2e clan', 3: '3e clan' };
function laurierEditionHtml(tag){
  const bl = BLASONS.get(tag), L = bl && bl.laurier;
  if(!L) return '';
  const on = !L.masque, s = (nomSaison(L.saison) || '').toLowerCase();
  const ecu = `<span class="blason blason-svg lr-ed-ecu"><svg viewBox="0 0 100 120" aria-hidden="true">${blasonSVG(clanEdition ? clanEdition.b : (bl.blason || null))}</svg></span>`;
  return `<div class="lr-ed lr-ed${L.rang}"><span class="lr petit">${laurierSVG(L.rang, true)}${ecu}</span>
    <div><b>${LAURIER_NOMS[L.rang]} · ${echapperHtml(s)}</b><small>${LAURIER_TXT[L.rang]} de la ${echapperHtml(s)}. ${on ? 'Affiché autour de ton blason partout dans le jeu.' : 'Retiré : personne ne le voit.'}</small></div>
    <button type="button" class="lr-sw${on ? ' on' : ''}" data-bl-laurier="${on ? '0' : '1'}" role="switch" aria-checked="${on}" aria-label="Afficher le laurier"></button></div>`;
}
document.addEventListener('click', async (ev) => {
  const b = ev.target.closest('[data-bl-laurier]');
  if(!b || b.disabled) return;
  b.disabled = true;
  const afficher = b.dataset.blLaurier === '1';
  const { data, error } = await sb.rpc('clan_laurier_afficher', { p_afficher: afficher });
  if(error){ notifier({ type: 'erreur', titre: 'Laurier', texte: messageLisible(error.message) }); b.disabled = false; return; }
  const tag = clanCache && clanCache.moi && clanCache.moi.clan ? clanCache.moi.clan.tag : null;
  const bl = tag ? BLASONS.get(tag) : null;
  if(bl && bl.laurier) bl.laurier.masque = !!(data && data.laurier_masque);
  notifier({ type: 'succes', titre: 'Laurier', texte: afficher ? 'Le laurier entoure de nouveau ton blason.' : 'Laurier retiré. Tu peux le remettre quand tu veux.' });
  const y = window.scrollY; renderClan(); window.scrollTo(0, y);
});
