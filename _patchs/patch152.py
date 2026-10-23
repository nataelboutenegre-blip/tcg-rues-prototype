# -*- coding: utf-8 -*-
u"""
patch152 — parrainage et titre choisi (23 octobre).
Serveur : _sql/parrainage-1.sql (à lancer AVANT de pousser ; sans lui, rien
ne s'affiche et rien ne casse : les appels échouent en silence).

- ?ref=<pseudo> dans l'adresse : mémorisé dans le navigateur (7 jours), même
  si l'inscription passe par la confirmation par e-mail.
- À l'ouverture du jeu : declarer_parrain (une fois), puis parrainage_jour
  (note le jour ; valide l'ami au 3e jour), puis mon_parrainage pour les
  récompenses pas encore montrées (notifications).
- Mot d'accueil : « <parrain> t'a invité » et les deux cadeaux.
- Profil : bloc « Inviter des amis » (lien, Copier / Partager, amis, badges
  à venir) ; le titre peut être choisi (titre de région ou « Le Parrain »).
- Fiche d'un autre joueur : son titre choisi.
- Badges recruteur / parrain / ambassadeur.
- Paquets Terra : une réserve au-dessus de 3 (cadeau) s'affiche telle quelle.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)

# ---------------------------------------------------------------- index.html
h = lire('index.html')
assert 'accueilInvite' not in h, u'patch152 deja applique'
h = rempl(h, u'''    <p class="acc-marque" id="accueilTitre">Terra<span>Front</span></p>''', u'''    <p class="acc-marque" id="accueilTitre">Terra<span>Front</span></p>
    <p class="acc-invite" id="accueilInvite" hidden></p>''', 'accueil invite')
h = rempl(h, u'''    <div class="acc-cadeau">
      <svg''', u'''    <div class="acc-invite-cadeaux" id="accueilInviteCadeaux" hidden>
      <div class="acc-ic"><b>+1</b><span>paquet Terra</span><small>en plus des 3 gratuits</small></div>
      <div class="acc-ic"><b>+10</b><span>énergie en Front</span><small>pour tes premiers assauts</small></div>
    </div>
    <p class="acc-invite-note" id="accueilInviteNote" hidden></p>
    <div class="acc-cadeau">
      <svg''', 'accueil cadeaux')
ecrire('index.html', h)

# ---------------------------------------------------------------- style.css
css = lire('style.css')
css = rempl(css, u"  /* ---------- Mot de passe oublié ---------- */", u"""  /* ---------- patch152 : parrainage ---------- */
  .acc-invite{ position:relative; display:flex; align-items:center; justify-content:center; gap:9px; margin:0 0 8px; font-size:.95rem; color:#fff; }
  .acc-invite[hidden], .acc-invite-cadeaux[hidden], .acc-invite-note[hidden]{ display:none; }
  .acc-invite .acc-av{ width:30px; height:30px; border-radius:50%; display:grid; place-items:center; font:900 .95rem/1 var(--titre); background: var(--nuit-3); color: var(--c-legendaire); box-shadow:0 0 0 1px rgba(240,180,41,.5); }
  .acc-invite b{ color: var(--c-legendaire); }
  .acc-invite-cadeaux{ position:relative; display:grid; grid-template-columns:1fr 1fr; gap:9px; margin-bottom:10px; }
  .acc-ic{ background: rgba(240,180,41,0.1); border:1px solid rgba(240,180,41,0.3); border-radius:12px; padding:11px; text-align:center; }
  .acc-ic b{ display:block; font:900 1.8rem/1 var(--titre); color: var(--c-legendaire); }
  .acc-ic span{ display:block; font-size:.8rem; margin-top:4px; line-height:1.3; }
  .acc-ic small{ display:block; font-size:.7rem; color: var(--brume); margin-top:2px; }
  .acc-invite-note{ position:relative; font-size:.8rem; color: var(--brume); text-align:center; margin:0 0 14px; }

  .pp-lien{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
  .pp-lien code{ flex:1 1 180px; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; background: var(--nuit); border:1px solid rgba(169,188,212,0.16); border-radius:10px; padding:11px 12px; font:500 .85rem var(--texte); color: var(--papier); }
  .pp-btn{ appearance:none; border:0; cursor:pointer; background: var(--c-legendaire); color: var(--encre); font:800 1.05rem/1 var(--titre); letter-spacing:.03em; border-radius:11px; padding:12px 14px; min-height:44px; box-shadow:0 4px 0 #B7791F; white-space:nowrap; }
  .pp-btn:active{ transform:translateY(3px); box-shadow:0 1px 0 #B7791F; }
  .pp-btn.second{ background: var(--nuit-3); color:#fff; box-shadow:0 4px 0 #0B1830; }
  .pp-btn.copie{ background:#3DD68C; box-shadow:0 4px 0 #1E8E58; }
  .pp-gains{ display:grid; gap:7px; margin-top:12px; }
  .pp-gain{ display:flex; gap:10px; align-items:flex-start; font-size:.83rem; color: var(--brume); }
  .pp-gain b{ color:#fff; font-weight:600; }
  .pp-gain svg{ width:18px; height:18px; flex:none; margin-top:2px; }
  .pp-progres{ margin-top:14px; padding-top:12px; border-top:1px solid rgba(169,188,212,0.09); }
  .pp-ligne{ display:flex; justify-content:space-between; align-items:baseline; font-size:.85rem; margin-bottom:8px; color: var(--brume); }
  .pp-ligne b{ font:900 1.5rem/1 var(--titre); color: var(--c-legendaire); }
  .pp-jauge{ height:8px; border-radius:99px; background: var(--nuit); overflow:hidden; }
  .pp-jauge i{ display:block; height:100%; background: linear-gradient(90deg,#B7791F, var(--c-legendaire)); border-radius:99px; }
  .pp-amis{ list-style:none; margin:10px 0 0; padding:0; }
  .pp-amis li{ display:flex; justify-content:space-between; align-items:center; gap:10px; padding:8px 0; border-bottom:1px solid rgba(169,188,212,.09); font-size:.85rem; }
  .pp-amis li:last-child{ border-bottom:0; }
  .pp-amis .pp-pseudo{ font-weight:600; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .pp-etat{ font-size:.72rem; font-weight:600; padding:3px 9px; border-radius:99px; white-space:nowrap; }
  .pp-etat.ok{ color:#3DD68C; background: rgba(61,214,140,.12); }
  .pp-etat.att{ color: var(--brume); background: rgba(169,188,212,.1); }
  .pp-note{ font-size:.75rem; color:#7F91AB; margin:10px 0 0; }
  .pf-titre-btn{ appearance:none; background:none; border:1px solid rgba(169,188,212,.3); color: var(--brume); border-radius:99px; font:600 .72rem/1 var(--texte); padding:5px 9px; cursor:pointer; }
  .pf-titre-btn:hover{ color:#fff; border-color: rgba(255,255,255,.5); }
  .titres-liste{ display:grid; gap:8px; margin:14px 0 4px; }
  .titre-choix{ display:flex; align-items:center; gap:10px; padding:12px 14px; border-radius:12px; border:1px solid rgba(169,188,212,.2); background: rgba(255,255,255,.03); cursor:pointer; font-size:.95rem; }
  .titre-choix input{ accent-color: var(--c-legendaire); width:18px; height:18px; }
  .titre-choix small{ display:block; color: var(--brume); font-size:.75rem; }
  .titre-choix:has(input:checked){ border-color: rgba(240,180,41,.6); background: rgba(240,180,41,.08); }
  /* ---------- Mot de passe oublié ---------- */""", 'css')
ecrire('style.css', css)

# ---------------------------------------------------------------- app.js
js = lire('app.js')
assert 'declarerParrainSiBesoin' not in js, u'patch152 deja applique'

# 1. démarrage : déclarer le parrain, noter le jour, puis l'accueil
js = rempl(js, u"""  peutEtreMontrerBandeAnnonce().then(peutEtreAfficherAccueil);   // patch150 : la bande-annonce d'abord""",
u"""  // patch150 : la bande-annonce d'abord ; patch152 : le parrain est declare avant l'accueil
  const parrainDeclare = declarerParrainSiBesoin();
  Promise.all([peutEtreMontrerBandeAnnonce(), parrainDeclare]).then(peutEtreAfficherAccueil);
  parrainDeclare.then(parrainageDuJour);""", 'demarrage')

# 2. paquets Terra : réserve au-dessus de 3
js = rempl(js, u"""  return Math.min(3, packStatusCache.jetons_actuels + elapsedMin / minParPaquet());""",
u"""  const j = Number(packStatusCache.jetons_actuels);
  if(j >= 3) return j;   // patch152 : un paquet offert peut faire depasser la reserve de 3
  return Math.min(3, j + elapsedMin / minParPaquet());""", 'liveJetons')
js = rempl(js, u"""  const puces = [`<span class="puce"><b>${dispo} sur 3</b> paquets gratuits</span>`];""",
u"""  const puces = [`<span class="puce"><b>${dispo > 3 ? dispo : dispo + ' sur 3'}</b> paquets gratuits</span>`];""", 'puce paquets')

# 3. badges et titres
js = rempl(js, u"""  navigateur:    { ico: '📡', nom: 'Le Navigateur',    texte: 'Le meilleur Elo au Radar', u: 'Elo' },
};""", u"""  navigateur:    { ico: '📡', nom: 'Le Navigateur',    texte: 'Le meilleur Elo au Radar', u: 'Elo' },
  // patch152 : parrainage (saison « parrainage » : gardes d'une saison a l'autre)
  recruteur:     { ico: '✉️', nom: 'Le Recruteur',     texte: '1 ami invité et actif', u: 'amis actifs' },
  parrain:       { ico: '🎩', nom: 'Le Parrain',       texte: '5 amis invités et actifs', u: 'amis actifs' },
  ambassadeur:   { ico: '🌍', nom: 'L’Ambassadeur',    texte: '10 amis invités et actifs', u: 'amis actifs' },
};
// patch152 : titres a choisir a la place du titre de region (l'id vient du serveur)
const TITRES = { parrain: 'Le Parrain' };
const titreAffiche = (p, choisi) => TITRES[choisi] || titreDepuisDeps(p.deps);""", 'badges')
js = rempl(js, u"""<small>${echapperTexte(nomSaison(b.saison))}${b.valeur != null && b.badge !== 'og' ? ' · ' + Number(b.valeur).toLocaleString('fr-FR') + (d.u ? ' ' + d.u : '') : ''}</small>""",
u"""<small>${echapperTexte([nomSaison(b.saison), b.valeur != null && b.badge !== 'og' ? Number(b.valeur).toLocaleString('fr-FR') + (d.u ? ' ' + d.u : '') : ''].filter(Boolean).join(' · '))}</small>""", 'ligne badge')

# 4. profil : chargement
js = rempl(js, u"""    [profilPanneau.vitrine, profilPanneau.badges, profilPanneau.echanges] = await Promise.all([chargerVitrine(id), chargerBadges(id), chargerStatEchanges(id)]);""",
u"""    [profilPanneau.vitrine, profilPanneau.badges, profilPanneau.echanges, profilPanneau.titres, profilPanneau.parrainage] =
      await Promise.all([chargerVitrine(id), chargerBadges(id), chargerStatEchanges(id), chargerMesTitres(), chargerParrainage()]);""", 'profil chargement')
# titre du profil (le sien)
js = rempl(js, u"""          <span class="pf-titre"><b>${echapperTexte(titreDepuisDeps(p.deps))}</b></span>""",
u"""          <span class="pf-titre"><b>${echapperTexte(titreAffiche(p, (p.titres || {}).choisi))}</b></span>
          ${((p.titres || {}).disponibles || []).length ? '<button type="button" class="pf-titre-btn" data-pf="titre">Changer de titre</button>' : ''}""", 'profil titre')
js = rempl(js, u"""    ${blocBadges(p, false)}
    ${blocsProfil(p)}""", u"""    ${blocBadges(p, false)}
    ${blocParrainage(p.parrainage)}
    ${blocsProfil(p)}""", 'profil bloc')
js = rempl(js, u"""  if(e.target.closest('[data-pf="supprimer"]')) ouvrirSuppressionCompte();""",
u"""  if(e.target.closest('[data-pf="supprimer"]')) ouvrirSuppressionCompte();
  const cp = e.target.closest('[data-pf="copier-ref"]');
  if(cp) copierLienParrain(cp);
  if(e.target.closest('[data-pf="partager-ref"]')) partagerLienParrain();
  if(e.target.closest('[data-pf="titre"]')) ouvrirChoixTitre();""", 'profil clics')

# fiche d'un autre joueur : son titre choisi
js = rempl(js, u"""  const [{ data, error }, vitrine, badges, echanges] = await Promise.all([
    sb.rpc('profil_joueur', { p_joueur: joueurId }), chargerVitrine(joueurId), chargerBadges(joueurId),
    chargerStatEchanges(joueurId)]);""", u"""  const [{ data, error }, vitrine, badges, echanges, titre] = await Promise.all([
    sb.rpc('profil_joueur', { p_joueur: joueurId }), chargerVitrine(joueurId), chargerBadges(joueurId),
    chargerStatEchanges(joueurId), chargerTitreJoueur(joueurId)]);""", 'fiche chargement')
js = rempl(js, u"""  profilEnCours.echanges = echanges;
  rendreProfil();""", u"""  profilEnCours.echanges = echanges;
  profilEnCours.titre = titre;
  rendreProfil();""", 'fiche titre')
js = rempl(js, u"""          gradeDe(Number(p.niveau)).nom}</span> ` : ''}<b>${echapperTexte(titreDepuisDeps(p.deps))}</b>${""",
u"""          gradeDe(Number(p.niveau)).nom}</span> ` : ''}<b>${echapperTexte(titreAffiche(p, p.titre))}</b>${""", 'fiche affichage')

# 5. accueil de l'invité
js = rempl(js, u"""  const voile = document.getElementById('voileAccueil');
  if(!voile) return;
  voile.hidden = false;""", u"""  const voile = document.getElementById('voileAccueil');
  if(!voile) return;
  if(parrainAccueil) remplirAccueilInvite(parrainAccueil);   // patch152
  voile.hidden = false;""", 'accueil')

# 6. les fonctions
js = rempl(js, u"""// ---------- Mot d'accueil, au tout premier lancement ----------""", u"""// ---------- patch152 : parrainage ----------
// Le lien : ?ref=<pseudo>. Garde dans le navigateur 7 jours, le temps de
// creer son compte (la confirmation par e-mail recharge la page sans ?ref).
const CLE_REF = 'tf-parrain-ref';
(function memoriserRef(){
  try{
    const r = (new URLSearchParams(location.search).get('ref') || '').trim();
    if(r.length >= 3 && r.length <= 20) localStorage.setItem(CLE_REF, JSON.stringify({ p: r, t: Date.now() }));
  } catch(e){}
})();
let parrainAccueil = null;

async function declarerParrainSiBesoin(){
  let ref = null;
  try{
    const v = JSON.parse(localStorage.getItem(CLE_REF) || 'null');
    if(v && v.p && Date.now() - Number(v.t) < 7 * 864e5) ref = v.p;
    else if(v) localStorage.removeItem(CLE_REF);
  } catch(e){}
  if(!ref) return;
  try{
    const { data, error } = await sb.rpc('declarer_parrain', { p_ref: ref });
    if(error){ console.error(error); return; }   // fonction absente : on garde le lien pour plus tard
    try{ localStorage.removeItem(CLE_REF); } catch(e){}
    const r = data && data[0];
    if(r && r.statut === 'ok'){
      parrainAccueil = r.parrain;
      loadPackStatus();
      majEnergie();
    }
  } catch(e){ console.error(e); }
}

async function chargerParrainage(){
  try{ const { data, error } = await sb.rpc('mon_parrainage'); return error ? null : data; }
  catch(e){ return null; }
}
async function chargerMesTitres(){
  try{ const { data, error } = await sb.rpc('mes_titres'); return error ? null : data; }
  catch(e){ return null; }
}
async function chargerTitreJoueur(id){
  try{ const { data, error } = await sb.rpc('titre_joueur', { p_joueur: id }); return error ? null : data; }
  catch(e){ return null; }
}

// Note le jour joue (le 3e jour valide l'ami aupres de son parrain), puis
// montre au parrain ce qu'il a recu depuis sa derniere visite.
async function parrainageDuJour(){
  try{ const { error } = await sb.rpc('parrainage_jour'); if(error) return; } catch(e){ return; }
  const d = await chargerParrainage();
  if(!d) return;
  const nv = d.nouveaux || [];
  if(!nv.length) return;
  const actifs = Number(d.actifs || 0), avant = actifs - nv.length;
  let t = 1800;
  for(const n of nv){
    const paye = Number(n.energie) > 0;
    setTimeout(() => notifier({ type: 'succes', titre: n.pseudo + ' a joué 3 jours', duree: 6000,
      texte: paye ? "Merci de l'avoir invité : +10 énergie" : "Merci de l'avoir invité ! L'énergie est limitée à 5 amis par saison." }), t);
    t += 1400;
  }
  for(const [seuil, nom] of [[1, 'Le Recruteur'], [5, 'Le Parrain'], [10, 'L’Ambassadeur']]){
    if(avant < seuil && actifs >= seuil){
      setTimeout(() => notifier({ type: 'succes', titre: 'Badge « ' + nom + ' »', duree: 7000,
        texte: seuil === 5 ? '5 amis actifs : choisis le titre « Le Parrain » dans ton profil.'
                           : seuil + ' ami' + (seuil > 1 ? 's' : '') + ' invité' + (seuil > 1 ? 's' : '') + ' et actif' + (seuil > 1 ? 's' : '') }), t);
      t += 1400;
    }
  }
  majEnergie();
  profilPanneau = null;   // le profil se rechargera avec les nouveaux chiffres
}

function lienParrain(pseudo){ return location.origin + '/?ref=' + encodeURIComponent(pseudo || ''); }

function blocParrainage(d){
  if(!d) return '';
  const nb = (x) => Number(x || 0).toLocaleString('fr-FR');
  const lien = lienParrain(d.pseudo);
  const lisible = location.host + '/?ref=' + (d.pseudo || '');
  const actifs = Number(d.actifs || 0);
  const palier = actifs < 1 ? 1 : actifs < 5 ? 5 : 10;
  const part = Math.min(100, Math.round(100 * actifs / palier));
  const nomPalier = { 1: '« Le Recruteur »', 5: '« Le Parrain »', 10: '« L’Ambassadeur »' }[palier];
  const amis = (d.amis || []).slice(0, 30).map(a => `<li><span class="pp-pseudo">${echapperTexte(a.pseudo)}</span>${
    a.valide ? `<span class="pp-etat ok">Actif${Number(a.energie) > 0 ? ' · +10 ⚡' : ''}</span>`
             : `<span class="pp-etat att">${nb(a.jours)} / 3 jours</span>`}</li>`).join('');
  const haut = d.peut_parrainer ? `
      <div class="pp-lien">
        <code>${echapperTexte(lisible)}</code>
        <button type="button" class="pp-btn" data-pf="copier-ref" data-lien="${echapperTexte(lien)}">Copier</button>
        ${navigator.share ? '<button type="button" class="pp-btn second" data-pf="partager-ref">Partager</button>' : ''}
      </div>` : `<p class="pp-note" style="margin-top:0">Tu pourras inviter des amis 3 jours après ton inscription.</p>`;
  return `<div class="pf-bloc pf-parrain">
      <h3>Inviter des amis</h3>
      ${haut}
      <div class="pp-gains">
        <div class="pp-gain"><svg viewBox="0 0 24 24" fill="none" stroke="#F0B429" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 10h18v10H3zM3 6h18v4H3zM12 6v14"/></svg><span>Ton ami reçoit <b>1 paquet Terra</b> et <b>10 énergie</b> en Front.</span></div>
        <div class="pp-gain"><svg viewBox="0 0 24 24" fill="none" stroke="#3DD68C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13 2 4 14h7l-1 8 9-12h-7z"/></svg><span>Toi, <b>+10 énergie</b> quand il a joué <b>3 jours</b>. Jusqu'à 5 amis par saison (${nb(d.payes_saison)} / 5).</span></div>
      </div>
      <div class="pp-progres">
        <div class="pp-ligne"><span>${actifs >= 10 ? 'Amis actifs · tous les badges obtenus' : 'Amis actifs · prochain badge ' + nomPalier}</span><b>${actifs >= 10 ? nb(actifs) : nb(actifs) + ' / ' + palier}</b></div>
        <div class="pp-jauge" role="img" aria-label="${nb(actifs)} amis actifs sur ${palier}"><i style="width:${part}%"></i></div>
        ${amis ? `<ul class="pp-amis">${amis}</ul>` : ''}
        <p class="pp-note">Un ami compte quand il a joué 3 jours différents.</p>
      </div>
    </div>`;
}

function copierLienParrain(bouton){
  const lien = bouton.getAttribute('data-lien') || '';
  const fait = () => { bouton.textContent = 'Copié'; bouton.classList.add('copie');
    setTimeout(() => { bouton.textContent = 'Copier'; bouton.classList.remove('copie'); }, 1600); };
  const secours = () => {
    const code = bouton.parentElement && bouton.parentElement.querySelector('code');
    if(code){ const r = document.createRange(); r.selectNodeContents(code); const s = getSelection(); s.removeAllRanges(); s.addRange(r); }
    notifier({ type: 'info', titre: 'Lien sélectionné', texte: 'Copie-le pour l’envoyer à tes amis.' });
  };
  try{ navigator.clipboard.writeText(lien).then(fait, secours); } catch(e){ secours(); }
}
function partagerLienParrain(){
  const d = (profilPanneau || {}).parrainage;
  if(!d || !navigator.share) return;
  navigator.share({ title: 'TerraFront', text: 'Viens jouer à TerraFront avec moi : les communes de France en cartes à collectionner.',
                    url: lienParrain(d.pseudo) }).catch(() => {});
}

function ouvrirChoixTitre(){
  const p = profilPanneau;
  if(!p || !p.titres) return;
  const choisi = p.titres.choisi || 'region';
  const options = [['region', titreDepuisDeps(p.deps), 'Selon la région où tu as le plus de communes']]
    .concat((p.titres.disponibles || []).filter(t => TITRES[t]).map(t => [t, TITRES[t], t === 'parrain' ? '5 amis invités et actifs' : '']));
  const fermer = ouvrirFenetre(`
    <form class="fenetre prix" role="dialog" aria-modal="true" aria-labelledby="titreChoixT" novalidate>
      <h2 id="titreChoixT">Ton titre</h2>
      <p class="prix-aide" style="margin:4px 0 0">Il s'affiche sous ton pseudo, pour tous les joueurs.</p>
      <div class="titres-liste">${options.map(([id, nom, aide]) => `
        <label class="titre-choix"><input type="radio" name="titre" value="${echapperTexte(id)}"${id === choisi ? ' checked' : ''}>
          <span><b>${echapperTexte(nom)}</b>${aide ? `<small>${echapperTexte(aide)}</small>` : ''}</span></label>`).join('')}
      </div>
      <div class="prix-boutons">
        <button type="button" class="open-btn secondary" data-t="annuler">Annuler</button>
        <button type="submit" class="open-btn">Choisir</button>
      </div>
    </form>`);
  const f = document.querySelector('#fenetre form');
  f.querySelector('[data-t="annuler"]').addEventListener('click', () => fermer(null));
  f.addEventListener('submit', async (e) => {
    e.preventDefault();
    const v = (f.querySelector('input[name="titre"]:checked') || {}).value || 'region';
    const { data, error } = await sb.rpc('choisir_titre', { p_titre: v });
    if(error){ notifier({ type: 'erreur', titre: 'Titre non changé', texte: messageLisible(error.message) }); return; }
    p.titres.choisi = data || null;
    fermer(true);
    rendreProfilPanneau();
    notifier({ type: 'succes', titre: 'Titre choisi', texte: titreAffiche(p, p.titres.choisi) });
  });
}

function remplirAccueilInvite(pseudo){
  const qui = document.getElementById('accueilInvite');
  const cadeaux = document.getElementById('accueilInviteCadeaux');
  const note = document.getElementById('accueilInviteNote');
  if(!qui || !cadeaux || !note) return;
  const init = String(pseudo || '?').trim().charAt(0).toUpperCase();
  qui.innerHTML = `<span class="acc-av" aria-hidden="true">${echapperTexte(init)}</span><span><b>${echapperTexte(pseudo)}</b> t'a invité</span>`;
  note.textContent = 'Joue 3 jours et ' + pseudo + ' reçoit lui aussi un petit coup de pouce.';
  qui.hidden = false; cadeaux.hidden = false; note.hidden = false;
}

// ---------- Mot d'accueil, au tout premier lancement ----------""", 'fonctions')
ecrire('app.js', js)
print(u'patch152 applique. Lancer : python3 maj-version.py')
