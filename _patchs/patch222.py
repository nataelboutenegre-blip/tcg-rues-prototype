# -*- coding: utf-8 -*-
u"""
patch222 — le centre de notifications (aperçu validé le 27/10 : « très bien »).

- Une cloche dans l'en-tête (PC : sous le logo ; téléphone : à côté des
  Règles), pastille rouge = nouveautés.
- Panneau « À faire » : on t'attaque (Défendre, 🔕 sourdine), échange reçu,
  échange de clan, invitation de clan, alerte d'échange disponible, quêtes à
  réclamer (avant minuit), récolte des légendaires, réserve de paquets pleine
  (désactivé par défaut). Chaque ligne mène au bon mode et au bon onglet.
- « Depuis ta dernière visite » : le journal qui me concerne, 7 jours
  (commune perdue, défense réussie, échange conclu).
- « Mes notifications » : chaque type dans le jeu / sur le téléphone, seuil de
  rareté des attaques, communes en sourdine. Réglage du compte (s2-38).
  Sans s2-38, la cloche marche avec les réglages par défaut.
- Lu / non lu retenu sur l'appareil. Rafraîchi toutes les 3 min (jeu à
  l'écran) et au retour sur l'onglet.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rep(s, a, b, n=1):
    c = s.count(a); assert c == n, ('MATCH', a[:70], 'trouve', c, 'attendu', n); return s.replace(a, b)

BLOC = r'''// ---------- patch222 : le centre de notifications ----------
// Une cloche dans l'en-tête : « À faire » (ce qui demande une action) et
// « Depuis ta dernière visite » (le journal qui me concerne, 7 jours). Tout
// vient de fonctions qui existent déjà ; ce qui a été lu est retenu sur
// l'appareil. Les réglages (s2-38) valent pour le compte, et pour le
// téléphone aussi (seuil de rareté, communes en sourdine).
const NC_DEFAUT = { jeu: { attaque: true, perdue: true, defense: true, echange: true, alerte: true, quete: true, recolte: true, clan: true, paquet: false },
                    tel: { attaque: true, paquet: true }, seuil: 'commun', sourdine: [] };
const NC = { prefs: null, prefsDispo: true, d: {}, items: [], ouvert: false, vue: 'liste', demarre: false };
const NC_ORDRE = ['commun', 'peucommun', 'rare', 'epique', 'legendaire'];
const NC_CLOCHE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z"/><path d="M10 20a2 2 0 0 0 4 0"/></svg>';
const NC_REGLER = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2"/><circle cx="10" cy="17" r="2"/></svg>';

function ncPrefs(){ return NC.prefs || NC_DEFAUT; }
function ncVus(){ try{ return new Set(JSON.parse(localStorage.getItem('tf-nc-vus') || '[]')); }catch(e){ return new Set(); } }
function ncMarquerVus(cles){
  const v = ncVus();
  for(const c of cles) v.add(c);
  try{ localStorage.setItem('tf-nc-vus', JSON.stringify([...v].slice(-500))); }catch(e){}
}
function ncPrefsDepuis(p){
  if(!p || typeof p !== 'object') return null;
  return { ...NC_DEFAUT, ...p, jeu: { ...NC_DEFAUT.jeu, ...(p.jeu || {}) }, tel: { ...NC_DEFAUT.tel, ...(p.tel || {}) },
           sourdine: Array.isArray(p.sourdine) ? p.sourdine.map(String) : [] };
}

function ncDemarrer(){
  if(NC.demarre) return;
  NC.demarre = true;
  const poser = (avant, id) => {
    const ref = document.getElementById(avant);
    if(!ref || document.getElementById(id)) return;
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'nc-cloche'; b.id = id;
    b.setAttribute('aria-label', 'Notifications');
    b.innerHTML = NC_CLOCHE + '<span class="nc-pastille" hidden></span>';
    b.addEventListener('click', () => ncOuvrir());
    ref.insertAdjacentElement('beforebegin', b);
  };
  poser('reglesBtn', 'ncCloche');
  poser('reglesBtnMobile', 'ncClocheMobile');
  ncCharger();
  setInterval(siVisible(ncCharger), 180000);
  VERIF_AU_RETOUR.push(ncCharger);
}

async function ncCharger(){
  const rpc = async (n, a) => { try{ const { data, error } = await sb.rpc(n, a); return error ? undefined : data; }catch(e){ return undefined; } };
  const [prefs, journal, sieges, ech, clanE, alertes, quetes, recolte, clan] = await Promise.all([
    NC.prefs ? null : rpc('mes_notif_preferences'),
    rpc('journal', { p_mode: 'moi', p_limite: 40 }),
    rpc('sieges_contre_moi'),
    SAISON2 ? rpc('terra_mes_echanges') : rpc('mes_echanges'),
    SAISON2 && CLANS ? rpc('clan_ech_etat') : null,
    SAISON2 ? rpc('terra_mes_alertes') : null,
    SAISON2 ? rpc('quetes') : null,
    SAISON2 ? rpc('front_recolte_etat') : null,
    CLANS ? rpc('mon_clan') : null,
  ]);
  if(!NC.prefs){
    if(prefs === undefined) NC.prefsDispo = false;
    else { NC.prefsDispo = true; NC.prefs = ncPrefsDepuis(prefs); }
  }
  NC.d = { journal, sieges, ech, clanE, alertes, quetes, recolte: Array.isArray(recolte) ? recolte[0] : recolte, clan };
  ncConstruire();
}

function ncConstruire(){
  const p = ncPrefs(), d = NC.d, items = [];
  const nb = (x) => Number(x || 0);
  const tierDe = (code) => { const e = collectionMap.get(code) || othersMap.get(code); return e && e.tier ? e.tier.id : null; };
  const nomDe = (code) => { const e = collectionMap.get(code) || othersMap.get(code); return e ? e.nom : code; };
  const label = (t) => { const x = TIERS.find(y => y.id === t); return x ? x.label : ''; };
  const sousSeuil = (code) => { const t = tierDe(code); return t && NC_ORDRE.indexOf(t) < NC_ORDRE.indexOf(p.seuil || 'commun'); };

  // --- À faire ---
  if(p.jeu.attaque && Array.isArray(d.sieges)){
    for(const m of d.sieges){
      if(nb(m.victoires_consecutives) < 1 || p.sourdine.includes(String(m.commune_code)) || sousSeuil(m.commune_code)) continue;
      items.push({ cle: `att|${m.commune_code}|${m.attaquant_id}|${m.victoires_consecutives}`, sec: 'afaire', c: 'danger', i: '⚔️', mode: 'front',
        t: `<b>${echapperTexte(m.attaquant_pseudo || 'Un joueur')}</b> t'attaque à <b>${echapperTexte(nomDe(m.commune_code))}</b>`,
        s: `Série ${nb(m.victoires_consecutives)} / 3${m.dernier_round ? ' · ' + ilYA(m.dernier_round) : ''}`,
        a: 'Défendre', rouge: true, sourdine: String(m.commune_code), aller: () => ncAller('front', 'defense') });
    }
  }
  if(p.jeu.echange && Array.isArray(d.ech)){
    for(const e of d.ech.filter(x => x.sens === 'recu')){
      const h = Math.max(0, Math.round((new Date(e.expire_le).getTime() - Date.now()) / 36e5));
      items.push({ cle: `ech|${e.id}`, sec: 'afaire', c: 'echange', i: '🔁', mode: SAISON2 ? 'terra' : null,
        t: `<b>${echapperTexte(e.autre_pseudo || 'Un joueur')}</b> te propose <b>${echapperTexte(e.je_recois_nom || '')}</b> contre <b>${echapperTexte(e.je_donne_nom || '')}</b>`,
        s: h ? `Encore ${h} h pour répondre` : 'Expire bientôt', a: 'Voir',
        aller: () => ncAller('terra', 'echange', () => { const b = document.querySelector('[data-ech-vue="cours"]'); if(b) b.click(); }) });
    }
  }
  if(p.jeu.clan && d.clanE && Array.isArray(d.clanE.recus)){
    for(const x of d.clanE.recus){
      items.push({ cle: `cle|${x.id}`, sec: 'afaire', c: 'clan', i: '🛡️', mode: 'front',
        t: `<b>${echapperTexte(x.pseudo || 'Un membre')}</b> te propose un échange de clan`,
        s: `Tu reçois ${echapperTexte((x.donne && x.donne.nom) || '')}, tu donnes ${echapperTexte((x.recoit && x.recoit.nom) || '')}`,
        a: 'Voir', aller: () => ncAller('front', 'clan') });
    }
  }
  if(p.jeu.clan && d.clan && Array.isArray(d.clan.invitations)){
    for(const i of d.clan.invitations){
      items.push({ cle: `inv|${i.tag}|${i.par}`, sec: 'afaire', c: 'clan', i: '🛡️',
        t: `<b>${echapperTexte(i.par || 'Un chef')}</b> t'invite dans le clan <b>[${echapperTexte(i.tag || '')}]</b>`,
        s: echapperTexte(i.nom || ''), a: 'Voir', aller: () => ncAller(null, 'clan') });
    }
  }
  if(p.jeu.alerte && d.alertes && Array.isArray(d.alertes.je_cherche)){
    for(const c of d.alertes.je_cherche){
      const dispo = c.dispo || [];
      if(!dispo.length) continue;
      items.push({ cle: `al|${c.code}|${dispo.map(x => x.id).sort().join(',')}`, sec: 'afaire', c: 'alerte', i: '🔔', mode: 'terra',
        t: dispo.length === 1 ? `<b>${echapperTexte(dispo[0].pseudo || 'Un joueur')}</b> a <b>${echapperTexte(c.nom)}</b> en double`
                              : `<b>${echapperTexte(c.nom)}</b> est en double chez ${dispo.length} joueurs`,
        s: 'Une commune de tes alertes', a: 'Échanger',
        aller: () => ncAller('terra', 'echange', () => { const b = document.querySelector('[data-ech-vue="alertes"]'); if(b) b.click(); }) });
    }
  }
  if(p.jeu.quete && Array.isArray(d.quetes)){
    const jour = new Date().toLocaleDateString('fr-CA', { timeZone: 'Europe/Paris' });
    for(const mode of ['terra', 'front']){
      const prets = d.quetes.filter(q => q.reclamable && !q.reclame && (!SAISON2 || q.mode === mode));
      if(!prets.length) continue;
      const duJour = prets.filter(q => q.categorie === 'jour').length;
      items.push({ cle: `q|${mode}|${jour}|${prets.length}`, sec: 'afaire', c: 'quete', i: '⭐', mode: SAISON2 ? mode : null,
        t: `<b>${prets.length} quête${prets.length > 1 ? 's' : ''}</b> à réclamer`,
        s: duJour ? 'Avant minuit, sinon celles du jour sont perdues' : 'Des défis permanents', a: 'Réclamer',
        aller: () => ncAller(mode, 'tirage', () => { const o = document.getElementById('objectifs'); if(o && o.scrollIntoView) o.scrollIntoView({ behavior: 'smooth', block: 'center' }); }) });
      if(!SAISON2) break;
    }
  }
  if(p.jeu.recolte && d.recolte && nb(d.recolte.pretes) > 0 && !d.recolte.recoltee){
    const jour = new Date().toLocaleDateString('fr-CA', { timeZone: 'Europe/Paris' });
    items.push({ cle: `rc|${jour}`, sec: 'afaire', c: 'energie', i: '⚡', mode: 'front',
      t: `Récolte prête : <b>+${nb(d.recolte.energie)} énergie</b>`,
      s: `${nb(d.recolte.pretes)} légendaire${nb(d.recolte.pretes) > 1 ? 's' : ''} tenue${nb(d.recolte.pretes) > 1 ? 's' : ''} depuis 24 h`,
      a: 'Récolter', aller: () => ncAller('front', 'combat') });
  }
  if(p.jeu.paquet && typeof packStatusCache !== 'undefined' && packStatusCache && Number(packStatusCache.jetons_actuels) >= 3){
    items.push({ cle: `pq|${SAISON2 ? modeJeu : ''}|${new Date().toLocaleDateString('fr-CA')}`, sec: 'afaire', c: 'quete', i: '📦', mode: SAISON2 ? modeJeu : null,
      t: 'Ta réserve de <b>paquets gratuits</b> est pleine', s: 'Ouvre-en un pour qu’elle se recharge', a: 'Ouvrir', aller: () => ncAller(null, 'tirage') });
  }

  // --- Depuis ta dernière visite (7 jours) ---
  const limite = Date.now() - 7 * 864e5;
  for(const e of Array.isArray(d.journal) ? d.journal : []){
    if(new Date(e.cree_le).getTime() < limite) continue;
    const nom = `<b>${echapperTexte(e.commune_nom || '')}</b>`;
    if(e.type === 'conquete' && e.je_suis_cible && p.jeu.perdue)
      items.push({ cle: `j|${e.id}`, sec: 'histo', c: 'histo', i: '🏴', mode: 'front', t: `<b>${echapperTexte(e.acteur_pseudo || 'Un joueur')}</b> t'a pris ${nom}`, s: `${label(e.tier)} · ${ilYA(e.cree_le)}` });
    else if(e.type === 'defense' && e.je_suis_acteur && p.jeu.defense)
      items.push({ cle: `j|${e.id}`, sec: 'histo', c: 'histo', i: '🛡️', mode: 'front', t: `Tu as repoussé <b>${echapperTexte(e.cible_pseudo || 'un joueur')}</b> à ${nom}`, s: `Défense réussie · ${ilYA(e.cree_le)}` });
    else if(e.type === 'echange' && (e.je_suis_acteur || e.je_suis_cible) && p.jeu.echange)
      items.push({ cle: `j|${e.id}`, sec: 'histo', c: 'histo', i: '🤝', t: `Échange conclu avec <b>${echapperTexte((e.je_suis_acteur ? e.cible_pseudo : e.acteur_pseudo) || 'un joueur')}</b> · ${nom}`, s: ilYA(e.cree_le) });
  }

  const vus = ncVus();
  for(const it of items) it.neuf = !vus.has(it.cle);
  NC.items = items;
  const n = items.filter(x => x.neuf).length;
  document.querySelectorAll('.nc-cloche').forEach(b => {
    const pa = b.querySelector('.nc-pastille');
    pa.hidden = n === 0; pa.textContent = n > 9 ? '9+' : String(n);
    b.setAttribute('aria-label', n ? `Notifications : ${n} nouvelle${n > 1 ? 's' : ''}` : 'Notifications');
  });
  if(NC.ouvert && NC.vue === 'liste') ncRendre();
}

function ncAller(mode, onglet, apres){
  ncFermer();
  if(SAISON2 && mode && modeJeu !== mode){
    const b = document.querySelector('#modeBascule [data-mode="' + mode + '"]');
    if(b) b.click();
  }
  setTimeout(() => {
    const t = document.querySelector('.tab[data-tab="' + onglet + '"]');
    if(t) t.click();
    if(apres) setTimeout(apres, 200);
  }, 60);
}

function ncOuvrir(vue){
  NC.vue = vue || 'liste';
  NC.ouvert = true;
  if(!document.getElementById('ncPanneau')){
    document.body.insertAdjacentHTML('beforeend', '<div class="nc-voile" id="ncVoile"></div><div class="nc-panneau" id="ncPanneau" role="dialog" aria-modal="true"></div>');
    document.getElementById('ncVoile').addEventListener('click', ncFermer);
    document.getElementById('ncPanneau').addEventListener('click', ncClic);
  }
  ncRendre();
  if(NC.vue === 'liste') ncCharger();
}

function ncFermer(){
  if(!NC.ouvert) return;
  NC.ouvert = false;
  // ce qui a été montré est lu
  ncMarquerVus(NC.items.map(x => x.cle));
  ncConstruire();
  const v = document.getElementById('ncVoile'), p = document.getElementById('ncPanneau');
  if(v) v.remove();
  if(p) p.remove();
}
document.addEventListener('keydown', (e) => { if(e.key === 'Escape' && NC.ouvert) ncFermer(); });

function ncRendre(){
  const el = document.getElementById('ncPanneau');
  if(!el) return;
  if(NC.vue === 'reglages') return ncRendreReglages(el);
  if(NC.vue === 'sourdine') return ncRendreSourdine(el);
  el.setAttribute('aria-label', 'Notifications');
  const ligne = (it, k) => `<div class="nc-item${it.neuf ? ' neuf' : ''}"><span class="nc-ico ${it.c}" aria-hidden="true">${it.i}</span>
    <div class="nc-txt">${it.mode && SAISON2 ? `<span class="nc-mode ${it.mode}">${it.mode === 'terra' ? 'TERRA' : 'FRONT'}</span>` : ''}${it.t}<small>${it.s || ''}</small></div>
    ${it.a ? `<button type="button" class="nc-action${it.rouge ? ' rouge' : ''}" data-nc-aller="${k}">${it.a}</button>` : ''}
    ${it.sourdine ? `<button type="button" class="nc-muet" data-nc-muet="${echapperTexte(it.sourdine)}" title="Ne plus me prévenir pour cette commune" aria-label="Ne plus me prévenir pour cette commune">🔕</button>` : ''}</div>`;
  const af = NC.items.map((x, k) => [x, k]).filter(([x]) => x.sec === 'afaire');
  const hi = NC.items.map((x, k) => [x, k]).filter(([x]) => x.sec === 'histo');
  el.innerHTML = `<div class="nc-tete"><h2>Notifications</h2>
      ${NC.items.some(x => x.neuf) ? '<button type="button" data-nc="lu">Tout marquer comme lu</button>' : ''}
      <button type="button" class="nc-reglage" data-nc="reglages" aria-label="Choisir mes notifications">${NC_REGLER}</button>
      <button type="button" class="nc-x" data-nc="fermer" aria-label="Fermer">✕</button></div>
    <div class="nc-corps">
      <p class="nc-titre">À faire</p>${af.length ? af.map(([x, k]) => ligne(x, k)).join('') : '<p class="nc-vide">Rien à faire pour l’instant.</p>'}
      <p class="nc-titre">Depuis ta dernière visite</p>${hi.length ? hi.map(([x, k]) => ligne(x, k)).join('') : '<p class="nc-vide">Rien de neuf ces 7 derniers jours.</p>'}
      <p class="nc-pied">Les 7 derniers jours · tout le reste est dans le Journal</p></div>`;
}

const NC_LIGNES = [
  ['attaque', 'On t’attaque', 'Une série en cours contre une de tes communes', true],
  ['perdue', 'Commune perdue', 'Un joueur t’a pris une commune', false],
  ['defense', 'Défenses', 'Tes défenses réussies', false],
  ['echange', 'Échanges', 'Propositions reçues, échanges conclus', false],
  ['alerte', 'Alertes d’échange', 'Une commune que tu cherches est disponible', false],
  ['quete', 'Quêtes à réclamer', 'Rappel avant minuit', false],
  ['recolte', 'Récolte des légendaires', 'L’énergie est prête', false],
  ['clan', 'Clan', 'Invitations, échanges de clan', false],
  ['paquet', 'Paquet gratuit prêt', 'Ta réserve de paquets est pleine', true],
];
function ncRendreReglages(el){
  const p = ncPrefs(), off = !NC.prefsDispo;
  el.setAttribute('aria-label', 'Choisir mes notifications');
  const inter = (canal, type, v) => `<button type="button" class="nc-inter${v ? ' on' : ''}" role="switch" aria-checked="${!!v}" data-nc-inter="${canal}|${type}"${off ? ' disabled' : ''}></button>`;
  const seuils = [['commun', 'Toutes'], ['peucommun', 'Peu commune et +'], ['rare', 'Rare et +'], ['epique', 'Épique et +'], ['legendaire', 'Légendaires']];
  el.innerHTML = `<div class="nc-tete"><button type="button" class="nc-retour" data-nc="liste" aria-label="Retour">←</button><h2>Mes notifications</h2>
      <button type="button" class="nc-x" data-nc="fermer" aria-label="Fermer">✕</button></div>
    <div class="nc-corps"><p class="nc-r-intro">${off ? 'Les réglages arrivent très bientôt.' : 'Choisis ce qui te prévient. Le réglage vaut pour ton compte, sur tous tes appareils.'}</p>
      <div class="nc-r-entete"><span style="text-align:left">Quand…</span><span>Dans le jeu</span><span>Téléphone</span></div>
      ${NC_LIGNES.map(([id, nom, desc, tel]) => `<div class="nc-r-ligne"><div><b>${nom}</b><small>${desc}</small></div>
        <div class="nc-r-c">${inter('jeu', id, p.jeu[id])}</div><div class="nc-r-c">${tel ? inter('tel', id, p.tel[id]) : '<span class="nc-r-sans">—</span>'}</div></div>` +
        (id === 'attaque' ? `<div class="nc-r-fin"><p>Seulement pour les communes…</p>
          <div class="nc-puces">${seuils.map(([t, n]) => `<button type="button" class="nc-puce${(p.seuil || 'commun') === t ? ' on' : ''}" data-nc-seuil="${t}"${off ? ' disabled' : ''}>${n}</button>`).join('')}</div>
          <div class="nc-sourdine"><span>🔕 <b>${p.sourdine.length} commune${p.sourdine.length > 1 ? 's' : ''}</b> en sourdine</span>${p.sourdine.length ? '<button type="button" data-nc="sourdine">Gérer</button>' : ''}</div></div>` : '')).join('')}
      <p class="nc-pied">« Téléphone » : seulement si tu as activé les notifications de TerraFront sur cet appareil.</p></div>`;
}
function ncRendreSourdine(el){
  const p = ncPrefs();
  el.innerHTML = `<div class="nc-tete"><button type="button" class="nc-retour" data-nc="reglages" aria-label="Retour">←</button><h2>En sourdine</h2>
      <button type="button" class="nc-x" data-nc="fermer" aria-label="Fermer">✕</button></div>
    <div class="nc-corps"><p class="nc-r-intro">Tu n'es plus prévenu quand ces communes sont attaquées, ni dans le jeu ni sur ton téléphone.</p>
      ${p.sourdine.length ? p.sourdine.map(code => {
        const e = collectionMap.get(code) || othersMap.get(code);
        return `<div class="nc-s-ligne"><span><b>${echapperTexte(e ? e.nom : code)}</b><small>${echapperTexte(e ? (DEPT_NAMES[e.dept] || e.dept) : '')}</small></span><button type="button" data-nc-demuet="${echapperTexte(code)}">Réactiver</button></div>`;
      }).join('') : '<p class="nc-vide">Aucune commune en sourdine.</p>'}</div>`;
}

async function ncRegler(fn, args){
  const { data, error } = await sb.rpc(fn, args);
  if(error){ notifier({ type: 'erreur', titre: 'Réglage non enregistré', texte: messageLisible(error.message) }); return false; }
  NC.prefs = ncPrefsDepuis(data) || NC.prefs;
  ncConstruire();
  return true;
}

async function ncClic(e){
  const b = e.target.closest('button');
  if(!b) return;
  if(b.dataset.nc === 'fermer') return ncFermer();
  if(b.dataset.nc === 'lu'){ ncMarquerVus(NC.items.map(x => x.cle)); ncConstruire(); return ncRendre(); }
  if(b.dataset.nc){ NC.vue = b.dataset.nc; return ncRendre(); }
  if(b.dataset.ncAller !== undefined){
    const it = NC.items[Number(b.dataset.ncAller)];
    if(it){ ncMarquerVus([it.cle]); it.aller(); }
    return;
  }
  if(b.dataset.ncMuet){
    const code = b.dataset.ncMuet, nom = (collectionMap.get(code) || {}).nom || code;
    if(await ncRegler('notif_sourdine', { p_code: code, p_on: true }))
      notifier({ type: 'info', titre: `${nom} en sourdine`, texte: 'Tu ne seras plus prévenu de ses attaques. Ça se réactive dans les réglages de la cloche.' });
    return ncRendre();
  }
  if(b.dataset.ncDemuet){ await ncRegler('notif_sourdine', { p_code: b.dataset.ncDemuet, p_on: false }); return ncRendre(); }
  if(b.dataset.ncInter){
    const [canal, type] = b.dataset.ncInter.split('|');
    const actuel = !!ncPrefs()[canal][type];
    b.classList.toggle('on', !actuel);   // tout de suite, le serveur confirme ensuite
    await ncRegler('regler_notif', { p_canal: canal, p_type: type, p_actif: !actuel });
    return ncRendre();
  }
  if(b.dataset.ncSeuil){ await ncRegler('regler_notif_seuil', { p_tier: b.dataset.ncSeuil }); return ncRendre(); }
}
'''
CSS = r'''/* =====================================================================
   patch222 — le centre de notifications
   ===================================================================== */
.nc-cloche{ position:relative; width:38px; height:38px; border-radius:11px; border:1px solid rgba(169,188,212,.22); background:rgba(15,31,56,.7);
  color:#E8EEF7; display:inline-flex; align-items:center; justify-content:center; cursor:pointer; flex:none; }
.nc-cloche svg{ width:20px; height:20px; }
.nc-cloche .nc-pastille{ position:absolute; top:-5px; right:-5px; min-width:19px; height:19px; padding:0 5px; border-radius:999px; background:#E5484D; color:#fff;
  font-size:.68rem; font-weight:800; display:flex; align-items:center; justify-content:center; box-shadow:0 0 0 2px #0B1A30; }
.nc-voile{ position:fixed; inset:0; background:rgba(3,8,18,.55); z-index:900; }
.nc-panneau{ position:fixed; z-index:901; background:#0F213C; border:1px solid rgba(169,188,212,.2); box-shadow:0 24px 60px rgba(0,0,0,.6);
  display:flex; flex-direction:column; color:#E8EEF7; }
@media (max-width:760px){ .nc-panneau{ left:0; right:0; bottom:0; max-height:84vh; border-radius:20px 20px 0 0; } }
@media (min-width:761px){ .nc-panneau{ top:64px; right:24px; width:400px; max-height:calc(100vh - 90px); border-radius:16px; } }
.nc-tete{ display:flex; align-items:center; gap:10px; padding:14px 16px 10px; border-bottom:1px solid rgba(169,188,212,.12); }
.nc-tete h2{ margin:0; font-family:var(--titre); font-size:1.35rem; flex:1; }
.nc-tete button{ border:none; background:none; color:var(--brume); font:inherit; font-size:.78rem; cursor:pointer; }
.nc-tete .nc-x{ font-size:1.2rem; color:#fff; }
.nc-corps{ overflow:auto; padding:6px 0 14px; }
.nc-titre{ margin:12px 16px 6px; font-size:.7rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; color:var(--brume); }
.nc-item{ display:flex; gap:11px; align-items:flex-start; padding:10px 16px; position:relative; }
.nc-item.neuf{ background:rgba(240,180,41,.06); }
.nc-item.neuf::before{ content:''; position:absolute; left:6px; top:18px; width:6px; height:6px; border-radius:50%; background:#F0B429; }
.nc-ico{ width:34px; height:34px; border-radius:10px; flex:none; display:flex; align-items:center; justify-content:center; font-size:1rem; }
.nc-ico.danger{ background:rgba(229,72,77,.18); } .nc-ico.echange{ background:rgba(47,124,246,.18); } .nc-ico.alerte{ background:rgba(44,198,201,.16); }
.nc-ico.quete{ background:rgba(240,180,41,.16); } .nc-ico.energie{ background:rgba(61,214,140,.16); } .nc-ico.clan{ background:rgba(155,92,246,.18); }
.nc-ico.histo{ background:rgba(169,188,212,.1); }
.nc-txt{ flex:1; min-width:0; font-size:.86rem; line-height:1.3; }
.nc-txt b{ color:#fff; } .nc-txt small{ display:block; color:var(--brume); font-size:.72rem; margin-top:2px; }
.nc-txt .nc-mode{ display:inline-block; font-size:.6rem; font-weight:800; letter-spacing:.05em; padding:1px 6px; border-radius:999px; margin-right:5px; vertical-align:1px; }
.nc-mode.terra{ background:rgba(53,185,126,.2); color:#7FE3B4; } .nc-mode.front{ background:rgba(229,72,77,.2); color:#FF9DA0; }
.nc-action{ flex:none; align-self:center; border:1px solid rgba(240,180,41,.45); background:rgba(240,180,41,.12); color:#F7D27A; font:inherit; font-size:.76rem;
  font-weight:700; padding:6px 11px; border-radius:999px; cursor:pointer; }
.nc-action.rouge{ border-color:rgba(229,72,77,.5); background:rgba(229,72,77,.14); color:#FF9DA0; }
.nc-pied{ text-align:center; color:var(--brume); font-size:.72rem; padding:8px 16px 0; }
.nc-reglage{ border:none; background:none; color:var(--brume); cursor:pointer; padding:4px; display:flex; }
.nc-reglage svg{ width:19px; height:19px; }
.nc-r-intro{ margin:10px 16px 4px; font-size:.78rem; color:var(--brume); }
.nc-r-entete, .nc-r-ligne{ display:grid; grid-template-columns:1fr 64px 64px; align-items:center; gap:6px; padding:9px 16px; }
.nc-r-entete{ font-size:.64rem; font-weight:800; letter-spacing:.06em; text-transform:uppercase; color:var(--brume); padding-bottom:4px; }
.nc-r-entete span{ text-align:center; }
.nc-r-ligne{ border-top:1px solid rgba(169,188,212,.08); }
.nc-r-ligne b{ display:block; font-size:.86rem; } .nc-r-ligne small{ color:var(--brume); font-size:.7rem; }
.nc-r-ligne .nc-r-c{ display:flex; justify-content:center; }
.nc-inter{ width:40px; height:24px; border-radius:999px; background:rgba(169,188,212,.22); position:relative; border:none; cursor:pointer; }
.nc-inter::after{ content:''; position:absolute; top:3px; left:3px; width:18px; height:18px; border-radius:50%; background:#fff; transition:.15s; }
.nc-inter.on{ background:#35B97E; } .nc-inter.on::after{ left:19px; }
.nc-r-sans{ color:rgba(169,188,212,.35); font-size:.9rem; }
.nc-retour{ border:none; background:none; color:#fff; font-size:1.2rem; cursor:pointer; padding:0 4px; }
.nc-r-fin{ padding:2px 16px 12px; display:flex; flex-direction:column; gap:8px; }
.nc-r-fin p{ margin:0; font-size:.72rem; color:var(--brume); }
.nc-puces{ display:flex; flex-wrap:wrap; gap:6px; }
.nc-puce{ border:1px solid rgba(169,188,212,.25); background:none; color:var(--brume); font:inherit; font-size:.74rem; padding:5px 10px; border-radius:999px; cursor:pointer; }
.nc-puce.on{ background:#2F7CF6; border-color:#2F7CF6; color:#fff; }
.nc-sourdine{ display:flex; align-items:center; justify-content:space-between; background:rgba(169,188,212,.07); border-radius:10px; padding:8px 10px; font-size:.8rem; }
.nc-sourdine button{ border:none; background:none; color:#F7D27A; font:inherit; font-size:.76rem; font-weight:700; cursor:pointer; }
.nc-muet{ flex:none; align-self:center; border:none; background:none; color:var(--brume); font-size:1rem; cursor:pointer; padding:4px; margin-left:-4px; }
.nc-vide{ margin:4px 16px 8px; font-size:.8rem; color:var(--brume); }
.nc-s-ligne{ display:flex; justify-content:space-between; align-items:center; gap:10px; padding:10px 16px; border-top:1px solid rgba(169,188,212,.08); font-size:.86rem; }
.nc-s-ligne small{ display:block; color:var(--brume); font-size:.7rem; }
.nc-s-ligne button{ border:1px solid rgba(53,185,126,.5); background:rgba(53,185,126,.12); color:#7FE3B4; font:inherit; font-size:.76rem; font-weight:700; padding:5px 10px; border-radius:999px; cursor:pointer; }
.nc-inter:disabled, .nc-puce:disabled{ opacity:.4; cursor:default; }
#ncClocheMobile{ margin-right:8px; width:34px; height:34px; }
'''

js = lire('app.js')
assert 'patch222' not in js
js = rep(js, r"""  majWhoami(session_.user.id);
""", r"""  majWhoami(session_.user.id);
  ncDemarrer();   // patch222 : la cloche
""")
js = js.rstrip('\n') + '\n\n' + BLOC
ecrire('app.js', js)

css = lire('style.css')
assert 'patch222' not in css
ecrire('style.css', css.rstrip('\n') + '\n\n' + CSS)
print('patch222 OK')
