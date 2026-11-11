
// ---------- patch419 : les récompenses de fin de saison 2 (annonce) ----------
// Un bandeau sous le titre du classement, jusqu'à la clôture (dimanche 22/11, 10 h à Paris), et la fiche qui
// détaille les récompenses. L'attribution se fait à la clôture (script à part) ; ici, rien que l'annonce.
const RS2_FIN = Date.UTC(2026, 10, 22, 9, 1);
const RS2_DIST = [
  ['🗺️', 'Le Conquérant', 'le plus de conquêtes'],
  ['🛡️', 'Le Rempart', 'le plus de défenses réussies'],
  ['🏰', 'Le Gardien', 'le plus d’attaques repoussées par ses garnisons'],
  ['🧱', 'Le Bâtisseur', 'le plus de bâtiments terminés'],
  ['💣', 'L’Artificier', 'le plus de bombes lancées'],
  ['✊', 'Le Rebelle', 'le plus de lingots mis dans des rébellions'],
  ['🤝', 'Le Diplomate', 'le plus d’échanges conclus'],
  ['🎯', 'La Cible', 'le plus attaqué'],
  ['🃏', 'Le Collectionneur', 'la plus grande collection Terra'],
  ['📍', 'Le Géographe', 'le plus de Communes du jour trouvées'],
  ['📡', 'Le Navigateur', 'le meilleur classement au Radar'],
  ['⚡', 'L’Éclair', 'le meilleur classement à Rafale'],
  ['🔮', 'Le Flair', 'le meilleur classement à Plus ou moins'],
];
function rs2Actif(){ return typeof SAISON2 !== 'undefined' && SAISON2 && Date.now() < RS2_FIN; }
function rs2Bandeau(){
  const cl = document.getElementById('classement');
  if(!cl) return;
  let b = document.getElementById('rs2Bandeau');
  if(!rs2Actif()){ if(b) b.remove(); return; }
  if(!b){
    b = document.createElement('button');
    b.type = 'button'; b.id = 'rs2Bandeau'; b.className = 'rs2-bandeau';
    b.setAttribute('data-rs2', '');
    const tete = cl.querySelector('.cl-tete');
    (tete || cl.firstChild).after(b);
  }
  const j = Math.ceil((RS2_FIN - Date.now()) / 86400000);
  b.innerHTML = `<span class="rs2-ico">🏆</span><span class="rs2-txt"><b>Fin de la saison 2</b> dimanche 22/11 à 10 h${j <= 7 ? ` · J−${j}` : ''}</span><span class="rs2-voir">Les récompenses ›</span>`;
}
function rs2Html(){
  const moi = (typeof classementDonnees !== 'undefined' && classementMode === 'general') ? classementDonnees.find(l => l.est_moi) : null;
  const rang = moi && moi.rang ? `<p class="rs2-moi">Aujourd’hui, tu es <b>${moi.rang}${moi.rang === 1 ? 'er' : 'e'}</b> du Front.</p>` : '';
  const dist = RS2_DIST.map(([i, n, t]) => `<div class="rs2-d"><span>${i}</span><b>${n}</b><small>${t}</small></div>`).join('');
  return `
    <div class="fenetre profil rs2" role="dialog" aria-modal="true" aria-labelledby="rs2Titre" style="--joueur:#F0B429">
      <div class="pr-tete">
        <button class="pr-fermer" data-rs2-fermer aria-label="Fermer">✕</button>
        <div class="rs2-coupe">🏆</div>
        <h2 id="rs2Titre">Récompenses de la saison 2</h2>
        <p class="pr-sous">Le classement du Front est figé <b>dimanche 22 novembre à 10 h</b> (heure de Paris).</p>
        ${rang}
      </div>
      <div class="pr-corps">
        <h3>Le podium et le top 10</h3>
        <div class="rs2-podium">
          <div class="rs2-m or"><span>🥇</span><b>Champion de la saison 2</b><small>titre, médaille d’or, dos de carte exclusif</small></div>
          <div class="rs2-m argent"><span>🥈</span><b>Vice-champion de la saison 2</b><small>titre, médaille d’argent, dos de carte exclusif</small></div>
          <div class="rs2-m bronze"><span>🥉</span><b>3e de la saison 2</b><small>titre, médaille de bronze, dos de carte exclusif</small></div>
          <div class="rs2-m"><span>🎖️</span><b>Top 10 de la saison 2</b><small>du 4e au 10e : le titre</small></div>
        </div>
        <p class="rs2-note">Le dos de carte du podium ne s’obtiendra pas autrement.</p>

        <h3>Le clan champion</h3>
        <p class="rs2-p">Le 1er du classement des clans à la clôture. Chaque membre reçoit le badge <b>Clan champion · S2</b> (s’il est dans le clan depuis au moins 7 jours), le clan garde un trophée sur sa fiche, et un rôle <b>🏆 Champions S2</b> sur le Discord.</p>

        <h3>Les distinctions</h3>
        <p class="rs2-p">Une par joueur : si tu en gagnes deux, tu gardes la plus nette et l’autre passe au suivant.</p>
        <div class="rs2-dist">${dist}</div>

        <h3>Seigneurs de territoire</h3>
        <p class="rs2-p">Un titre pour chaque département que tu tiens à <b>50 % ou plus</b> à la clôture (<b>Seigneur de la Charente · S2</b>), et pour chaque région où tu as le bonus de région (<b>Maître de la Bretagne · S2</b>). Tu choisis ton titre dans ton profil.</p>

        <h3>Pour tous</h3>
        <p class="rs2-p">Tous ceux qui ont tenu une commune du Front cette saison reçoivent le badge <b>Pionnier du Front</b> et <b>1 paquet Terra</b> offert au début de la saison 3.</p>
        <p class="rs2-note">Les récompenses sont du prestige : aucune ne donne d’avantage au Front de la saison 3. Tes 5 communes marquées d’une ★ restent à toi, comme à chaque saison.</p>
      </div>
    </div>`;
}
let rs2Fermer = null;
document.addEventListener('click', (e) => {
  if(e.target.closest('[data-rs2-fermer]')){ if(rs2Fermer) rs2Fermer(null); return; }
  if(!e.target.closest('[data-rs2]')) return;
  rs2Fermer = ouvrirFenetre(rs2Html(), () => { rs2Fermer = null; });
});
