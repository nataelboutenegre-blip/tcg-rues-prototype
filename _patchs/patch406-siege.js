
// ---------- patch406 : le siège sur la fiche de la carte, la vague animée, « Comment c'est calculé » ----------
// Ma commune : les sièges contre elle (sgMenaces), avec Renforcer sur place.
function sgFicheMienne(code){
  const l = sgMenaces.filter(m => m.commune === code);
  if(!l.length) return '';
  return '<div class="sg-fiche">' + l.map(m => {
    const res = Number(m.resistance) || 0, deg = Number(m.degats) || 0, p = res ? Math.round(100 * deg / res) : 0;
    return `<div class="sg-fiche-l${p >= 66 ? ' chaud' : ''}">
      <div class="sg-fiche-h"><span>Assiégée par <b>${echapperTexte(m.attaquant_pseudo || 'un joueur')}</b></span><span>${p} % · ${m.long ? 'long' : 'éclair'}</span></div>
      ${sgBarre(deg, res, true)}
      <div class="sg-fiche-a"><span>Renforcer</span>${[2, 5, 10].map(x => `<button type="button" class="sg-renf" data-sg-renf="${x}" data-code="${echapperTexte(m.commune)}" data-att="${echapperTexte(m.attaquant)}">${x} ⚡</button>`).join('')}</div>
    </div>`;
  }).join('') + '</div>';
}
// La commune d'un autre : qui l'assiège (sieges_commune), chargé après l'ouverture.
async function sgFicheAutres(code){
  const { data, error } = await sb.rpc('sieges_commune', { p_code: code });
  if(error || panneauCommune !== code) return;
  const el = document.getElementById('sgFicheAutres');
  if(!el) return;
  const l = Array.isArray(data) ? data : [];
  if(!l.length){ el.hidden = true; el.innerHTML = ''; return; }
  const moi = window.__monId;
  const mien = l.find(x => x.attaquant === moi);
  const autres = l.filter(x => x.attaquant !== moi);
  let h = '';
  if(mien) h += `<div class="sg-fiche-l moi"><div class="sg-fiche-h"><span><b>Ton siège</b></span><span>${Number(mien.pct) || 0} % · ${mien.long ? 'long' : 'éclair'}</span></div>${sgBarre(Number(mien.pct) || 0, 100, true)}</div>`;
  if(autres.length){
    const noms = autres.slice(0, 3).map(x => `<b>${echapperTexte(x.pseudo || 'un joueur')}</b> (${Number(x.pct) || 0} %)`);
    h += `<p class="sg-fiche-course">⚔️ ${mien ? 'Aussi assiégée' : 'Assiégée'} par ${noms.join(', ')}${autres.length > 3 ? ` et ${autres.length - 3} autre${autres.length - 3 > 1 ? 's' : ''}` : ''}${mien ? ' : le premier qui remplit sa jauge la prend.' : '.'}</p>`;
  }
  el.innerHTML = h;
  el.hidden = false;
}
function sgMonSiege(code){ return sgMes.some(s => s.commune === code); }
// La fiche de la carte suit les renforts et les nouvelles vagues.
function sgRafraichirFiche(){
  if(!panneauCommune || !collectionMap.has(panneauCommune)) return;
  const el = document.getElementById('mapPanneau');
  if(!el || el.hidden) return;
  const a = panneauAncre;
  ouvrirPanneau(panneauCommune, a ? a.x : 40, a ? a.y : 40);
}
// La vague : la jauge part de l'ancienne valeur, tremble et brille.
function sgAnimerVague(b){
  const an = SG.anim; SG.anim = null;
  if(!an || !b) return;
  const j = b.querySelector('.sg-jauge');
  const r = b.querySelector('.sg-jauge .sg-rempli');
  if(!j) return;
  if(r){
    const fin = r.style.width;
    r.style.transition = 'none';
    r.style.width = Math.max(0, Math.min(100, an.de)).toFixed(1) + '%';
    void r.offsetWidth;
    r.style.transition = '';
    r.style.width = fin;
  }
  j.classList.add(an.bcl ? 'sg-choc-bcl' : 'sg-choc');
  setTimeout(() => j.classList.remove('sg-choc', 'sg-choc-bcl'), 900);
}
// « Comment c'est calculé » (les chiffres viennent de config_jeu 'siege', s3-7)
function sgCalcHtml(a){
  const mult = Number(a.mult) || 1;
  const multTxt = Math.abs(mult - 1) < 0.005 ? 'normaux' : '× ' + mult.toFixed(2).replace('.', ',');
  return `<details class="sg-calc"${SG.calc ? ' open' : ''}><summary data-sg="calc">Comment c'est calculé ?</summary>
    <ul>
      <li><b>Chaque énergie</b> fait 10 points sur la jauge, au hasard entre 8 et 12.</li>
      <li><b>Tes dégâts</b> dépendent de tes communes à moins de 20 km (aucune : −20 %, une : normal, deux ou plus : +10 %). Zone bombardée +15 %, ta Forteresse à côté +10 %, débutant +50 % sur les communes jusqu'à rare sans garnison. Ici : <b>${multTxt}</b>.</li>
      <li><b>Résistance</b> : commune et peu commune 55, rare 65, épique 125, légendaire 250. Forteresse sur place × 1,5. Une rébellion que tu finances la baisse.</li>
      <li><b>Garnison</b> : chaque énergie en garnison fait un bouclier de 10 points, à casser avant la jauge.</li>
      <li><b>Siège long</b> (garnison, bâtiment, renfort, ou légendaire) : 10 % de la résistance peut partir tout de suite, le reste suit le temps (commune 1 h, peu commune 1 h 30, rare 2 h, épique 6 h, légendaire 15 h). L'énergie en trop attend et part toute seule toutes les 5 minutes.</li>
      <li><b>Épique en éclair</b> : au moins 1 h, même sans défense.</li>
      <li><b>Renfort</b> : chaque énergie du propriétaire fait reculer ta jauge de 12 points en moyenne, et rend le siège long.</li>
      <li><b>24 h sans vague</b> : le siège tombe. L'énergie déjà envoyée est perdue, celle en attente te revient.</li>
    </ul></details>`;
}
