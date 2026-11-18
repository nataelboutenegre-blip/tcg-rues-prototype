// prototype : couronne de laurier autour du blason
function laurierSVG(rang, petit){
  const C = { 1: ['#FFE6A0', '#F0B429', '#9A6A12', '#6B4708'], 2: ['#FFFFFF', '#CFD8E4', '#8D99AB', '#5D6878'], 3: ['#F6C79A', '#C98A4B', '#8A5226', '#5E3515'] }[rang] || null;
  if(!C) return '';
  const id = 'lr' + Math.random().toString(36).slice(2, 8);
  const cx = 50, cy = 64, rx = 64, ry = 70;
  const pt = (t) => [cx - rx * Math.sin(t), cy + ry * Math.cos(t)];
  const n = petit ? 7 : 10, t0 = 0.32, t1 = 2.55;
  let tige = '', feuilles = '';
  const branche = (sens) => {
    const P = [];
    for(let i = 0; i <= 30; i++){ const t = t0 + (t1 - t0) * i / 30; const [x, y] = pt(t); P.push([sens < 0 ? x : 100 - x, y]); }
    tige += `<path d="M${P.map(p => p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' L')}" fill="none" stroke="${C[3]}" stroke-width="${petit ? 3.2 : 2.6}" stroke-linecap="round"/>`;
    for(let i = 0; i < n; i++){
      const t = t0 + 0.12 + (t1 - t0 - 0.12) * i / (n - 1);
      let [x, y] = pt(t); if(sens > 0) x = 100 - x;
      const [x2, y2] = pt(t + 0.01); const dx = (sens > 0 ? 100 - x2 : x2) - x, dy = y2 - y;
      const a = Math.atan2(dy, dx) * 180 / Math.PI;
      const k = (petit ? 1.35 : 1) * (1.15 - 0.45 * i / (n - 1));
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
    feuilles += `<path transform="translate(${xt.toFixed(1)} ${ye.toFixed(1)}) rotate(${sens > 0 ? -60 : -120}) scale(${petit ? 1.1 : .8})" d="M0 0 C5 -5.2 13 -5.2 19 0 C13 4.4 5 4.4 0 0Z" fill="url(#${id})" stroke="${C[3]}" stroke-width=".8"/>`;
  };
  branche(-1); branche(1);
  const noeud = `<g transform="translate(50 ${cy + ry - 1})"><path d="M-3 0 L-12 13 L-7 12 L-5 17 L0 3Z M3 0 L12 13 L7 12 L5 17 L0 3Z" fill="${C[1]}" stroke="${C[3]}" stroke-width="1"/><ellipse rx="5.5" ry="4" fill="${C[1]}" stroke="${C[3]}" stroke-width="1.1"/></g>`;
  return `<svg class="laurier-svg" viewBox="-26 -14 152 162" aria-hidden="true"><defs><linearGradient id="${id}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${C[0]}"/><stop offset=".5" stop-color="${C[1]}"/><stop offset="1" stop-color="${C[2]}"/></linearGradient></defs>${tige}${feuilles}${petit ? '' : noeud}</svg>`;
}
