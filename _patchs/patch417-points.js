
// ---------- patch417 : « Mes points », le détail de mon score du Front (idée d'Oshannir ; s2-137 mon_score_detail) ----------
// Toucher sa propre ligne du classement du Front (ou « Mes points » sous la légende) ouvre la fiche.
// Seulement pour soi : la fonction du serveur ne renvoie que le score du joueur connecté.
const MP_TIER = { legendaire: 'légendaire', epique: 'épique', rare: 'rare', peucommun: 'peu commune', commun: 'commune' };
const MP_BAT = { fonderie: 'Fonderie', forteresse: 'Forteresse', centre: 'Centre de recherche', banque: 'Banque', radar: 'Radar' };
const MP_DEPS_VUS = 6;
let mpFermer = null;
async function ouvrirMesPoints(monId){
  const moi = classementDonnees.find(l => l.est_moi);
  const { data, error } = await sb.rpc('mon_score_detail');
  if(error || !data){
    notifier({ type: 'info', titre: 'Détail indisponible', texte: 'Le détail de tes points n’est pas disponible pour le moment.' });
    return;
  }
  mpFermer = ouvrirFenetre(mpHtml(data, moi), () => { mpFermer = null; });
  const f = document.querySelector('.fenetre.mes-points');
  if(f) f.addEventListener('click', (e) => {
    const b = e.target.closest('[data-mp]');
    if(!b) return;
    if(b.dataset.mp === 'fermer'){ if(mpFermer) mpFermer(null); return; }
    if(b.dataset.mp === 'autres'){
      f.querySelectorAll('.mp-l.cache').forEach(x => x.classList.remove('cache'));
      b.remove();
      return;
    }
    if(b.dataset.mp === 'profil'){ if(mpFermer) mpFermer(null); setTimeout(() => ouvrirProfil(monId || (moi && moi.joueur_id)), 200); }
  });
}
function mpHtml(d, moi){
  const nb = (n) => Number(n || 0).toLocaleString('fr-FR');
  const plus = (n) => Number(n) > 0 ? '+' + nb(n) : '0';
  const e = echapperTexte;
  const ligne = (gauche, droite, sous, cache) =>
    `<div class="mp-l${cache ? ' cache' : ''}"><span class="mp-g">${gauche}${sous ? `<small>${sous}</small>` : ''}</span><b class="mp-d">${droite}</b></div>`;
  const bloc = (cl, titre, total, corps) =>
    `<section class="mp-bloc"><h3><i class="sc-pt ${cl}"></i>${titre}<b>${nb(total)} pts</b></h3>${corps}</section>`;

  // cartes
  const cartes = (d.cartes.lignes || []).map(l => ligne(
    `${nb(l.n)} ${MP_TIER[l.tier] || l.tier}${l.n > 1 ? 's' : ''} <span class="mp-x">× ${nb(l.pu)}</span>`, plus(l.pts))).join('')
    || '<p class="mp-vide">Aucune commune pour le moment.</p>';

  // combats
  const c = d.combats;
  const combats = ligne(`${nb(c.victoires)} victoire${c.victoires > 1 ? 's' : ''} <span class="mp-x">× ${nb(c.pu)}</span>`, plus(c.pts),
    'Conquête, défense ou garnison qui repousse · 10 par jour au plus, 2 par jour contre un même joueur');

  // territoires
  const t = d.territoires;
  const deps = (t.deps || []).map((x, i) => ligne(
    `${e(DEPT_NAMES[x.dep] || x.dep)} <span class="mp-code">${e(x.dep)}</span>`, plus(x.pts),
    `${String(x.part).replace('.', ',')} % (${nb(x.n)} / ${nb(x.taille)})${x.seul ? ' · seul en tête' : ''} · palier ${x.palier} %`,
    i >= MP_DEPS_VUS)).join('');
  const autres = (t.deps || []).length > MP_DEPS_VUS
    ? `<button type="button" class="mp-autres" data-mp="autres">Voir les ${(t.deps.length - MP_DEPS_VUS)} autres départements</button>` : '';
  const regions = (t.regions || []).filter(r => r.gagnee).map(r => ligne(
    `Région ${e(r.region)}`, plus(r.pts), `${r.n} départements sur ${r.total} à 10 % ou plus`)).join('');
  const presque = (t.regions || []).filter(r => !r.gagnee).sort((a, b) => (b.n / b.total) - (a.n / a.total))[0];
  const presqueHtml = presque ? `<p class="mp-note">Région la plus proche : <b>${e(presque.region)}</b>, ${presque.n} département${presque.n > 1 ? 's' : ''} sur ${presque.total} à 10 % ou plus ; il en faut ${Math.floor(presque.total / 2) + 1} pour +${nb(t.region_pts)}.</p>` : '';
  const sans = t.sans > 0 ? `<p class="mp-note">Et ${nb(t.sans)} département${t.sans > 1 ? 's' : ''} où tu as des communes sans bonus (en dessous de 50 %, il faut être seul en tête).</p>` : '';
  const territoires = (deps || '<p class="mp-vide">Aucun département avec un bonus pour le moment.</p>') + autres + regions + presqueHtml + sans;

  // bâtiments, bombes, rébellions
  const b = d.batiments;
  const bats = (b.lignes || []).map(x => ligne(
    `${MP_BAT[x.type] || x.type}${x.comptes > 1 ? ` <span class="mp-x">× ${x.comptes}</span>` : ''}`, plus(x.pts),
    x.n > x.comptes ? `${x.n} construites, ${x.comptes} comptent au plus` : '')).join('');
  const bombes = (b.bombes || []).map(x => ligne(
    `Bombe de niveau ${x.niveau}`, plus(x.pts),
    `${x.nom ? e(x.nom) + ' · ' : ''}${new Date(x.le).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })}`)).join('');
  const reb = b.rebellions_lingots > 0 ? ligne('Rébellions', plus(b.rebellions_pts),
    `${nb(b.rebellions_lingots)} lingots, financées ou étouffées · 2 points par lingot, 60 par jour au plus`) : '';
  const batiments = (bats + bombes + reb) || '<p class="mp-vide">Aucun bâtiment terminé, aucune bombe lancée.</p>';

  const inactif = d.actif ? '' : '<p class="mp-note">Les combats, les territoires et les bâtiments ne comptent pas encore : pour l’instant, seules tes cartes font ton score.</p>';
  return `
    <div class="fenetre profil mes-points" role="dialog" aria-modal="true" aria-labelledby="mpTitre" style="--joueur:${COULEUR_MOI}">
      <div class="pr-tete">
        <button class="pr-fermer" data-mp="fermer" aria-label="Fermer">✕</button>
        <h2 id="mpTitre">Mes points</h2>
        <p class="mp-total">${nb(d.total)}<small>pts</small></p>
        ${moi && moi.rang ? `<p class="pr-sous"><span class="pr-rang">${moi.rang}${moi.rang === 1 ? 'er' : 'e'}</span> du classement du Front</p>` : ''}
        <div class="mp-barre">${['c', 'co', 't', 'b'].map((k, i) => {
          const v = [d.cartes.pts, c.pts, t.pts, b.pts][i];
          return Number(v) > 0 ? `<i class="${k}" style="flex:${Number(v)}"></i>` : '';
        }).join('')}</div>
      </div>
      <div class="pr-corps">
        ${inactif}
        ${bloc('c', 'Cartes', d.cartes.pts, cartes)}
        ${bloc('co', 'Combats', c.pts, combats)}
        ${bloc('t', 'Territoires', t.pts, territoires)}
        ${bloc('b', 'Bâtiments, bombes, rébellions', b.pts, batiments)}
        <p class="mp-pied">Le classement se met à jour chaque minute : juste après une prise, ta ligne peut avoir un petit retard sur cette fiche.</p>
        <button type="button" class="pr-btn" data-mp="profil">Voir mon profil</button>
      </div>
    </div>`;
}
document.addEventListener('click', (e) => {
  if(!e.target.closest('[data-mp-ouvrir]')) return;
  const moi = classementDonnees.find(l => l.est_moi);
  ouvrirMesPoints(moi && moi.joueur_id);
});
