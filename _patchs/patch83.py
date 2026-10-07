# -*- coding: utf-8 -*-
u"""
patch83 — Radar : défier un joueur (avec _sql/radar-5-defis.sql).

- QG : bouton « Défier un joueur » (choix parmi ses amis et le classement
  Radar), et un bloc « Défis » : défis reçus (Relever / Décliner, date
  d'expiration) et défis envoyés en attente.
- Fiche d'un joueur : bouton « Défier au Radar ».
- Écran d'avant-partie : « Défi amical » au lieu de l'Elo.
- Résumé : un défi n'affiche pas d'Elo ; défi envoyé, décliné ou expiré
  ont leur propre phrase.
- Tes derniers duels : « Amical » à la place du gain d'Elo ; « Décliné »
  et « Expiré » pour les défis sans réponse.
- La pastille du QG compte aussi les défis reçus.
Sécurité : supabase-js figé en version 2.117.2 (avant : « @2 », donc
n'importe quelle nouvelle version publiée arrivait chez les joueurs sans
avoir été essayée).
Le SQL radar-5-defis.sql doit être passé AVANT le push.
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

def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)

# --- index.html ----------------------------------------------------------------
html = lire('index.html')
html = rempl(html,
u'''<button type="button" class="qg-btn" id="qgEntr">S'entraîner</button>''',
u'''<button type="button" class="qg-btn" id="qgEntr">S'entraîner</button><button type="button" class="qg-btn" id="qgDefier">Défier un joueur</button>''',
'bouton defier')
html = rempl(html,
u'''        <div class="qg-carte" id="qgDerniersBloc" hidden>''',
u'''        <div class="qg-carte" id="qgDefisBloc" hidden>
          <h3 class="qg-h3">Défis</h3>
          <ul class="qg-duels qg-defis" id="qgDefis"></ul>
        </div>

        <div class="qg-carte" id="qgDerniersBloc" hidden>''', 'bloc defis')
html = rempl(html,
u'''<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>''',
u'''<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.2/dist/umd/supabase.js"></script>''',
'supabase-js fige')
ecrire('index.html', html)

js = lire('app.js')

# --- pastille du QG -----------------------------------------------------------
js = rempl(js,
u'''  const nonVus = radarEtat ? Number(radarEtat.non_vus || 0) : 0;
  const n = (cdjAJouer ? 1 : 0) + nonVus;''',
u'''  const nonVus = radarEtat ? Number(radarEtat.non_vus || 0) : 0;
  const defis = radarEtat && Array.isArray(radarEtat.defis_recus) ? radarEtat.defis_recus.length : 0;
  const n = (cdjAJouer ? 1 : 0) + nonVus + defis;''', 'badge')

# --- QG : bloc Defis et lignes des derniers duels -----------------------------
js = rempl(js,
u'''  + d.map(x => {
    const delta = (x.elo_apres != null && x.elo_avant != null) ? x.elo_apres - x.elo_avant : 0;
    const mot = x.resultat === 'victoire' ? 'Victoire' : x.resultat === 'defaite' ? 'Défaite' : 'Égalité';
    return `<li class="${x.vu ? '' : 'nouveau'}" data-id="${Number(x.id)}" tabindex="0" role="button"><span class="qg-res ${x.resultat}">${mot}</span>
      <span class="qg-adv">contre <b>${echapperTexte(x.adversaire || 'un joueur')}</b><small>${kmQG(x.total_km)} km contre ${kmQG(x.adversaire_km)} km</small></span>
      <span class="qg-delta ${delta >= 0 ? 'plus' : 'moins'}">${delta >= 0 ? '+' : ''}${delta}</span><span class="qg-chev" aria-hidden="true">›</span></li>`;
  }).join('');''',
u'''  + d.map(x => {
    const nomAdv = echapperTexte(x.adversaire || 'un joueur');
    // defi sans reponse (patch83)
    if(x.resultat === 'refuse' || x.resultat === 'expire'){
      return `<li class="${x.vu ? '' : 'nouveau'}" data-id="${Number(x.id)}" tabindex="0" role="button"><span class="qg-res sans-reponse">${x.resultat === 'refuse' ? 'Décliné' : 'Expiré'}</span>
        <span class="qg-adv">défi à <b>${nomAdv}</b><small>${x.resultat === 'refuse' ? 'il a décliné' : 'pas relevé à temps'} · ${kmQG(x.total_km)} km</small></span>
        <span></span><span class="qg-chev" aria-hidden="true">›</span></li>`;
    }
    const delta = (x.elo_apres != null && x.elo_avant != null) ? x.elo_apres - x.elo_avant : 0;
    const mot = x.resultat === 'victoire' ? 'Victoire' : x.resultat === 'defaite' ? 'Défaite' : 'Égalité';
    return `<li class="${x.vu ? '' : 'nouveau'}" data-id="${Number(x.id)}" tabindex="0" role="button"><span class="qg-res ${x.resultat}">${mot}</span>
      <span class="qg-adv">${x.amical ? 'défi contre' : 'contre'} <b>${nomAdv}</b><small>${kmQG(x.total_km)} km contre ${kmQG(x.adversaire_km)} km</small></span>
      ${x.amical ? '<span class="qg-amical">Amical</span>'
        : `<span class="qg-delta ${delta >= 0 ? 'plus' : 'moins'}">${delta >= 0 ? '+' : ''}${delta}</span>`}<span class="qg-chev" aria-hidden="true">›</span></li>`;
  }).join('');

  // les defis (patch83) : recus a relever, envoyes en attente
  const recus = r.defis_recus || [], envoyes = r.defis_envoyes || [];
  document.getElementById('qgDefisBloc').hidden = recus.length === 0 && envoyes.length === 0;
  const resteJours = (iso) => {
    const j = Math.ceil((new Date(iso).getTime() - Date.now()) / 864e5);
    return j <= 1 ? 'expire aujourd’hui' : `encore ${j} jours`;
  };
  document.getElementById('qgDefis').innerHTML = recus.map(x =>
    `<li class="recu"><span class="qg-res defi">Défi</span>
      <span class="qg-adv"><b>${echapperTexte(x.pseudo)}</b> te défie<small>${echapperTexte(radarQuand(x.fin))} · ${resteJours(x.expire_le)}</small></span>
      <span class="qg-defi-actions"><button type="button" class="qg-btn plein" data-relever="${Number(x.id)}" data-pseudo="${echapperTexte(x.pseudo)}">Relever</button><button type="button" class="qg-btn" data-decliner="${Number(x.id)}">Décliner</button></span></li>`).join('')
  + envoyes.map(x =>
    `<li data-id="${Number(x.id)}" tabindex="0" role="button"><span class="qg-res attente">Envoyé</span>
      <span class="qg-adv">défi à <b>${echapperTexte(x.pseudo)}</b><small>${kmQG(x.total_km)} km · en attente de sa réponse</small></span>
      <span></span><span class="qg-chev" aria-hidden="true">›</span></li>`).join('');''', 'derniers + defis')

# --- defier, relever, decliner --------------------------------------------------
js = rempl(js,
u'''function radarRangDe(elo){''',
u'''// ----- les defis (patch83) -----
// L'ecran d'avant-partie d'un defi : pas d'Elo, le nom de l'autre.
function radarVsDefi(data, pseudo, texte){
  radarMontrer('rdVs');
  document.getElementById('rdVsMoi').textContent = 'Défi amical';
  document.getElementById('rdVsLui').textContent = pseudo;
  document.getElementById('rdVsLuiInfo').textContent = 'sans Elo';
  document.getElementById('rdVsTexte').textContent = texte;
  setTimeout(radarSuite, 2600);
}
async function radarDefier(id, pseudo){
  radarModeEntr = false; clearInterval(radarChrono);
  try{
    const { data, error } = await sb.rpc('radar_defier', { p_cible: id });
    if(error) throw error;
    radarPartie = data;
    const t = document.querySelector('.tab[data-tab="radar"]'); if(t) t.click();
    radarVsDefi(data, pseudo, `Tu joues 5 communes. ${pseudo} aura 7 jours pour relever ton défi et faire mieux.`);
  } catch(err){
    notifier({ type: 'erreur', titre: 'Défi', texte: messageLisible(err.message) });
    chargerRadar();
  }
}
async function radarRelever(id, pseudo){
  radarModeEntr = false; clearInterval(radarChrono);
  try{
    const { data, error } = await sb.rpc('radar_relever', { p_id: id });
    if(error) throw error;
    radarPartie = data;
    const t = document.querySelector('.tab[data-tab="radar"]'); if(t) t.click();
    radarVsDefi(data, pseudo, `${pseudo} a joué ces 5 communes. À toi de faire mieux.`);
  } catch(err){
    notifier({ type: 'erreur', titre: 'Défi', texte: messageLisible(err.message) });
    chargerRadar();
  }
}
async function radarDecliner(id){
  const { error } = await sb.rpc('radar_refuser', { p_id: id });
  if(error) notifier({ type: 'erreur', titre: 'Défi', texte: messageLisible(error.message) });
  chargerRadar();
}
// Choisir qui defier : ses amis, puis le classement Radar.
function radarChoisirAdversaire(){
  const vus = new Set([ID_MOI]);
  const ligne = (id, pseudo, info) => {
    if(!id || vus.has(id)) return '';
    vus.add(id);
    return `<button type="button" class="dc-joueur" data-defier="${echapperTexte(id)}" data-pseudo="${echapperTexte(pseudo)}"><b>${echapperTexte(pseudo)}</b><span>${info}</span></button>`;
  };
  const amis = (amisListe || []).filter(x => x.etat === 'accepte').map(x => ligne(x.id, x.pseudo, 'ami')).join('');
  const classes = ((radarEtat && radarEtat.classement) || []).filter(x => !x.moi).map(x =>
    ligne(x.id, x.pseudo, `${echapperTexte(x.rang)} · ${Number(x.elo).toLocaleString('fr-FR')}`)).join('');
  const fermer = ouvrirFenetre(`
    <div class="fenetre defi-choix" role="dialog" aria-modal="true" aria-labelledby="dcTitre">
      <h2 id="dcTitre">Défier un joueur</h2>
      <p class="dc-aide">Défi amical, sans Elo. Tu joues 5 communes maintenant ; ton adversaire a 7 jours pour faire mieux.</p>
      ${amis ? `<h3>Tes amis</h3><div class="dc-liste">${amis}</div>` : ''}
      ${classes ? `<h3>Classement Radar</h3><div class="dc-liste">${classes}</div>` : ''}
      ${!amis && !classes ? '<p class="dc-aide">Personne à proposer pour l’instant.</p>' : ''}
      <p class="dc-aide petit">Tu peux aussi défier n’importe quel joueur depuis sa fiche.</p>
      <button type="button" class="open-btn secondary" data-dc-fermer>Annuler</button>
    </div>`);
  const fen = document.querySelector('#fenetre .defi-choix');
  fen.addEventListener('click', (e) => {
    if(e.target.closest('[data-dc-fermer]')){ fermer(null); return; }
    const b = e.target.closest('[data-defier]');
    if(!b) return;
    fermer(null);
    radarDefier(b.dataset.defier, b.dataset.pseudo);
  });
}
document.getElementById('qgDefier').addEventListener('click', async () => {
  if(typeof amisCharges !== 'undefined' && !amisCharges) await loadAmis();
  radarChoisirAdversaire();
});
(function(){
  const liste = document.getElementById('qgDefis');
  liste.addEventListener('click', (e) => {
    const rel = e.target.closest('[data-relever]');
    if(rel){ rel.disabled = true; radarRelever(Number(rel.dataset.relever), rel.dataset.pseudo); return; }
    const dec = e.target.closest('[data-decliner]');
    if(dec){ dec.disabled = true; radarDecliner(Number(dec.dataset.decliner)); return; }
    const li = e.target.closest('li[data-id]'); if(li) radarOuvrirResume(Number(li.dataset.id));
  });
  liste.addEventListener('keydown', (e) => {
    if(e.key !== 'Enter' && e.key !== ' ') return;
    const li = e.target.closest('li[data-id]'); if(!li || e.target !== li) return;
    e.preventDefault(); radarOuvrirResume(Number(li.dataset.id));
  });
})();

function radarRangDe(elo){''', 'fonctions defi')

# --- resume : pas d'Elo pour un defi, phrases propres aux defis -------------------
js = rempl(js,
u'''  } else if(adv){
    const mot = p.resultat === 'victoire' ? 'Victoire' : p.resultat === 'defaite' ? 'Défaite' : 'Égalité';
    const delta = p.elo_apres - p.elo_avant;
    const avant = radarRangDe(p.elo_avant), apres = radarRangDe(p.elo_apres);
    tete = `<div class="rd-titre"><h2 class="${p.resultat}">${mot}</h2><span>contre <b>${nomAdv}</b>${quand ? ` · ${quand}` : ''}</span></div>
      <div class="rd-score"><div><b>${fmt(p.total_km)} km</b><span>Toi</span></div><em>contre</em><div><b>${fmt(adv.total_km)} km</b><span>${nomAdv}</span></div></div>
      <div class="rd-elo"><span>Elo</span><b class="${delta >= 0 ? 'plus' : 'moins'}">${delta >= 0 ? '+' : ''}${delta}</b><span class="qg-petit">${fmt(p.elo_apres)} · ${apres}${apres !== avant ? (delta > 0 ? ' (promu !)' : ' (rétrogradé)') : ''}</span></div>`;
  } else {''',
u'''  } else if(adv && p.amical){
    const mot = p.resultat === 'victoire' ? 'Victoire' : p.resultat === 'defaite' ? 'Défaite' : 'Égalité';
    tete = `<span class="rd-etiq">Défi amical</span>
      <div class="rd-titre"><h2 class="${p.resultat}">${mot}</h2><span>contre <b>${nomAdv}</b>${quand ? ` · ${quand}` : ''}</span></div>
      <div class="rd-score"><div><b>${fmt(p.total_km)} km</b><span>Toi</span></div><em>contre</em><div><b>${fmt(adv.total_km)} km</b><span>${nomAdv}</span></div></div>
      <p class="qg-petit">Un défi ne compte pas dans l’Elo.</p>`;
  } else if(adv){
    const mot = p.resultat === 'victoire' ? 'Victoire' : p.resultat === 'defaite' ? 'Défaite' : 'Égalité';
    const delta = p.elo_apres - p.elo_avant;
    const avant = radarRangDe(p.elo_avant), apres = radarRangDe(p.elo_apres);
    tete = `<div class="rd-titre"><h2 class="${p.resultat}">${mot}</h2><span>contre <b>${nomAdv}</b>${quand ? ` · ${quand}` : ''}</span></div>
      <div class="rd-score"><div><b>${fmt(p.total_km)} km</b><span>Toi</span></div><em>contre</em><div><b>${fmt(adv.total_km)} km</b><span>${nomAdv}</span></div></div>
      <div class="rd-elo"><span>Elo</span><b class="${delta >= 0 ? 'plus' : 'moins'}">${delta >= 0 ? '+' : ''}${delta}</b><span class="qg-petit">${fmt(p.elo_apres)} · ${apres}${apres !== avant ? (delta > 0 ? ' (promu !)' : ' (rétrogradé)') : ''}</span></div>`;
  } else if(p.cible){
    const cible = echapperTexte(p.cible);
    const phrase = p.resultat === 'refuse' ? `${cible} a décliné ton défi.`
      : p.resultat === 'expire' ? `${cible} n’a pas relevé ton défi à temps.`
      : `Défi envoyé à ${cible} : il a 7 jours pour le relever. Le résultat arrivera dans le QG.`;
    tete = `<span class="rd-etiq">Défi amical</span><h2>${fmt(p.total_km)} km</h2><p class="qg-petit">${phrase}</p>`;
  } else {''', 'resume')

# --- fiche joueur : Defier au Radar --------------------------------------------
js = rempl(js,
u'''    : `<button class="pr-btn principal" data-pr="territoire">Voir son territoire</button>
       <button class="pr-btn" data-pr="echange">Proposer un échange</button>`;''',
u'''    : `<button class="pr-btn principal" data-pr="territoire">Voir son territoire</button>
       <button class="pr-btn" data-pr="echange">Proposer un échange</button>
       <button class="pr-btn" data-pr="defier">Défier au Radar</button>`;''', 'fiche bouton')
js = rempl(js,
u'''  if(action === 'territoire'){
    const id = p.est_moi ? ID_MOI : p.id;''',
u'''  if(action === 'defier'){
    if(fermerProfil) fermerProfil(null);
    radarDefier(p.id, p.pseudo);
    return;
  }

  if(action === 'territoire'){
    const id = p.est_moi ? ID_MOI : p.id;''', 'fiche action')
ecrire('app.js', js)

css = lire('style.css')
css += u'''

/* ---------- patch83 : defis Radar ---------- */
.qg-res.defi{ color: var(--c-legendaire); }
.qg-res.sans-reponse{ color: var(--brume); }
.qg-amical{ font-size:11px; font-weight:600; color: var(--brume); border:1px solid rgba(169,188,212,.3); border-radius:999px; padding:1px 7px; }
.qg-defis li.recu{ grid-template-columns:84px minmax(0,1fr) auto; background: rgba(240,180,41,.08); }
.qg-defi-actions{ display:flex; gap:6px; }
.qg-defi-actions .qg-btn{ padding:6px 12px; font-size:.82rem; }
.fenetre.defi-choix{ text-align:left; width:min(420px, 100%); max-height:min(80vh, 640px); overflow:auto; }
.defi-choix h2{ font-size:1.9rem; }
.defi-choix h3{ margin:14px 0 6px; font-size:.75rem; letter-spacing:.06em; text-transform:uppercase; color: var(--brume); }
.dc-aide{ margin:0 0 6px; color: var(--brume); font-size:.86rem; line-height:1.45; }
.dc-aide.petit{ font-size:.78rem; margin-top:14px; }
.dc-liste{ display:flex; flex-direction:column; gap:4px; }
.dc-joueur{ display:flex; justify-content:space-between; align-items:center; gap:12px; width:100%; font:inherit; color:#fff; text-align:left;
  background: rgba(255,255,255,.04); border:1px solid rgba(169,188,212,.16); border-radius:10px; padding:9px 12px; cursor:pointer; }
.dc-joueur:hover, .dc-joueur:focus-visible{ border-color: var(--c-legendaire); outline:none; }
.dc-joueur span{ font-size:.78rem; color: var(--brume); }
.defi-choix .open-btn{ margin-top:12px; width:100%; }
@media (max-width:520px){
  .qg-defis li.recu{ grid-template-columns:64px minmax(0,1fr); }
  .qg-defi-actions{ grid-column:1 / -1; justify-content:flex-end; }
}
'''
ecrire('style.css', css)
print(u'patch83 : OK')
