# -*- coding: utf-8 -*-
u"""
patch99 — Défendre lisible + départements à défendre en priorité.
SQL : _sql/defense-departements.sql (à passer avant le push ; sans lui, le
volet marche, simplement sans départements prioritaires).

- Une ligne par COMMUNE (ses attaquants regroupés dessous), au lieu d'une
  carte par attaque.
- Trois blocs : « À défendre maintenant » (une victoire de plus et elle
  tombe), « Attaquées », « Repoussées · 24 h » (replié).
- « Mes départements » : jusqu'à 5, choisis par le joueur (suggestions = ses
  départements les plus fournis), réglage du compte. Leurs communes passent
  en tête de chaque bloc (épingle) ; filtre « Mes départements ».
- Le coût du bouton Défendre s'affiche en énergie en saison 2 (avant : « pts »).
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

def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)

js = lire('app.js')
assert 'defPrio' not in js, u'patch99 deja applique'

debut = js.index(u"  const now = Date.now();\n  liste.innerHTML = menaces.map(m => {")
fin = js.index(u"document.getElementById('boucliersToutToggle')", debut)
ancien = js[debut:fin]
assert ancien.count(u"liste.innerHTML = menaces.map") == 1
js = js[:debut] + u"""  renderDefenseLisible(liste);
}

// ---------- patch99 : Defendre lisible + departements prioritaires ----------
let defPrio = [];            // codes de departement, dans l'ordre d'ajout
let defPrioCharge = false;
let defFiltre = 'tout';      // 'tout' | 'prio'
let defAjoutOuvert = false;
const DEF_PRIO_MAX = 5;

async function chargerDefPrio(){
  if(defPrioCharge) return;
  defPrioCharge = true;
  const { data, error } = await sb.rpc('mes_departements_defense');
  if(error){ defPrio = null; return; }          // SQL pas encore passe : pas de priorites
  defPrio = (data || []).map(x => x.departement);
}

function deptDe(m){
  const c = collectionMap.get(m.commune_code);
  return c ? String(c.dept || '') : '';
}

// mes departements les plus fournis, pour proposer sans rien taper
function suggestionsDefPrio(){
  const n = {};
  for(const e of collectionMap.values()){
    if(e.perdue || !e.dept) continue;
    n[e.dept] = (n[e.dept] || 0) + 1;
  }
  return Object.entries(n).filter(([d]) => !(defPrio || []).includes(d))
    .sort((a, b) => b[1] - a[1]).slice(0, 6);
}

function renderDefenseLisible(liste){
  const now = Date.now();
  const prio = new Set(defPrio || []);
  // regroupement par commune
  const parCommune = new Map();
  for(const m of menaces){
    let g = parCommune.get(m.commune_code);
    if(!g){ g = { code: m.commune_code, nom: m.nom, tier: m.tier, dept: deptDe(m), attaques: [] }; parCommune.set(m.commune_code, g); }
    g.attaques.push(m);
  }
  const groupes = [...parCommune.values()].map(g => {
    const c = collectionMap.get(g.code);
    g.bouclier = c && c.bouclierJusqua > now ? c.bouclierJusqua : 0;
    g.vmax = Math.max(...g.attaques.map(a => a.victoires_consecutives));
    g.prio = prio.has(g.dept);
    g.favori = favorisSet.has(g.code);
    g.prochain = Math.min(...g.attaques.filter(a => a.victoires_consecutives > 0)
      .map(a => new Date(a.dernier_round).getTime() + (DELAI_ATTAQUE_MS[g.tier] || 0)), Infinity);
    g.attaques.sort((a, b) => b.victoires_consecutives - a.victoires_consecutives);
    return g;
  });
  const vus = defFiltre === 'prio' ? groupes.filter(g => g.prio) : groupes;
  const tri = (a, b) => (b.prio - a.prio) || (b.favori - a.favori) || (b.vmax - a.vmax) || (a.prochain - b.prochain);
  const urgentes = vus.filter(g => g.vmax >= 2 && !g.bouclier).sort(tri);
  const attaquees = vus.filter(g => g.vmax > 0 && !(g.vmax >= 2 && !g.bouclier)).sort(tri);
  const repoussees = vus.filter(g => g.vmax === 0).sort(tri);
  const nbPrio = groupes.filter(g => g.prio && g.vmax > 0).length;

  const ligneAttaque = (g, m) => {
    const v = m.victoires_consecutives;
    const serie = [0, 1, 2].map(i => `<i class="${i < v ? 'pris' : ''}"></i>`).join('');
    let quand = '';
    if(v === 0) quand = `repoussée il y a ${formatDuree(now - new Date(m.dernier_round).getTime())}`;
    else if(g.bouclier) quand = 'en pause (bouclier)';
    else {
      const p = new Date(m.dernier_round).getTime() + (DELAI_ATTAQUE_MS[g.tier] || 0);
      quand = now < p ? `prochain assaut dans ${formatDuree(p - now)}` : 'peut attaquer maintenant';
    }
    let action = '';
    if(v > 0 && !g.bouclier){
      action = m.defense_utilisee ? '<span class="df-note">défense déjà utilisée</span>'
        : (m.attaquant_id ? `<button class="menace-defendre" data-commune="${m.commune_code}" data-attaquant="${m.attaquant_id}" data-nom="${echapperTexte(g.nom)}">${ICONE_BOUCLIER}${coutTexte(coutIntensite(g.tier))}</button>` : '');
    }
    return `<div class="df-att"><span class="menace-serie" title="${v} victoire${v > 1 ? 's' : ''} d'affilée sur 3">${serie}</span>
      <span class="df-qui"><b>${echapperTexte(m.attaquant_pseudo || 'Un joueur')}</b><small>${quand}</small></span>${action}</div>`;
  };
  const ligne = (g) => {
    const tier = TIERS.find(t => t.id === g.tier);
    return `<div class="df-ligne${g.vmax >= 2 && !g.bouclier ? ' urgente' : ''}${g.prio ? ' prio' : ''}">
      <div class="df-tete"><span class="menace-point" style="background:${COULEURS_FILTRE[g.tier] || '#7E8BA0'}"></span>
        ${g.prio ? '<span class="df-epingle" title="Département prioritaire">📍</span>' : ''}${g.favori ? '<span class="menace-etoile" title="Une de tes cinq communes gardées">★</span>' : ''}
        <b>${echapperTexte(g.nom)}</b>${badgeDept(g.dept)}<span class="df-rarete">${tier ? tier.label.toLowerCase() : ''}</span>
        ${g.bouclier ? `<span class="df-bouclier">${ICONE_BOUCLIER}${formatDuree(g.bouclier - now)}</span>` : ''}</div>
      ${g.attaques.map(m => ligneAttaque(g, m)).join('')}
    </div>`;
  };
  const bloc = (classe, titre, liste_, aide) => liste_.length ? `<div class="df-bloc ${classe}"><h3>${titre} <span>${liste_.length}</span></h3>${aide ? `<p class="df-aide">${aide}</p>` : ''}${liste_.map(ligne).join('')}</div>` : '';

  // la barre des departements prioritaires
  let barre = '';
  if(defPrio !== null){
    const chips = (defPrio || []).map(d => `<button type="button" class="df-dep" data-def-dep="${echapperTexte(d)}" title="Retirer">${echapperTexte(d)} <span>${echapperTexte(DEPT_NAMES[d] || '')}</span> ×</button>`).join('');
    const sugg = defAjoutOuvert ? `<div class="df-sugg">${suggestionsDefPrio().map(([d, n]) =>
        `<button type="button" class="df-dep ajout" data-def-dep="${echapperTexte(d)}">+ ${echapperTexte(d)} <span>${echapperTexte(DEPT_NAMES[d] || '')} · ${n}</span></button>`).join('') || '<span class="df-aide">Tous tes départements sont déjà choisis.</span>'}
        <input type="text" id="defDepChamp" maxlength="30" placeholder="Autre : 33 ou Gironde" autocomplete="off"></div>` : '';
    barre = `<div class="df-prio"><div class="df-prio-ligne"><span class="df-prio-t">📍 Mes départements</span>${chips}
        ${(defPrio || []).length < DEF_PRIO_MAX ? `<button type="button" class="df-dep plus" data-def-ajout>${defAjoutOuvert ? 'Fermer' : '+ Ajouter'}</button>` : ''}</div>
        ${!(defPrio || []).length && !defAjoutOuvert ? '<p class="df-aide">Choisis jusqu\\'à 5 départements : leurs communes attaquées passent en tête.</p>' : ''}${sugg}</div>
      ${(defPrio || []).length ? `<div class="df-filtres"><button class="filter-pill ${defFiltre === 'tout' ? 'active' : ''}" data-def-filtre="tout">Tout</button><button class="filter-pill ${defFiltre === 'prio' ? 'active' : ''}" data-def-filtre="prio">Mes départements <b class="df-nb">${nbPrio}</b></button></div>` : ''}`;
  }

  const corps = bloc('urgent', 'À défendre maintenant', urgentes, 'Une victoire de plus et la commune est perdue.')
    + bloc('', 'Attaquées', attaquees, '')
    + (repoussees.length ? `<details class="df-bloc repoussees"><summary>Repoussées · 24 h <span>${repoussees.length}</span></summary>${repoussees.map(ligne).join('')}</details>` : '');
  liste.innerHTML = barre + (corps || `<p class="collection-empty">${defFiltre === 'prio' ? 'Aucune attaque dans tes départements.' : 'Aucune attaque en cours.'}</p>`);
}

async function basculerDefPrio(dep){
  const { data, error } = await sb.rpc('basculer_departement_defense', { p_dep: dep });
  if(error){ notifier({ type: 'erreur', titre: 'Départements', texte: messageLisible(error.message) }); return; }
  defPrio = (data || []).map(x => x.departement);
  if(!defPrio.length) defFiltre = 'tout';
  renderMenaces();
}

function trouverDepartementSaisi(txt){
  const t = sansAccents(String(txt || '').trim()).toLowerCase();
  if(!t) return null;
  const code = t.toUpperCase();
  if(DEPT_NAMES[code]) return code;
  if(DEPT_NAMES['0' + code]) return '0' + code;
  const e = Object.entries(DEPT_NAMES).find(([, nom]) => sansAccents(nom).toLowerCase() === t);
  return e ? e[0] : null;
}

document.getElementById('combatMenacesListe').addEventListener('click', (e) => {
  const f = e.target.closest('[data-def-filtre]');
  if(f){ defFiltre = f.dataset.defFiltre; renderMenaces(); return; }
  if(e.target.closest('[data-def-ajout]')){ defAjoutOuvert = !defAjoutOuvert; renderMenaces();
    if(defAjoutOuvert){ const c = document.getElementById('defDepChamp'); if(c && !/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) c.focus(); }
    return; }
  const d = e.target.closest('[data-def-dep]');
  if(d){ basculerDefPrio(d.dataset.defDep); return; }
});
document.getElementById('combatMenacesListe').addEventListener('keydown', (e) => {
  if(e.key !== 'Enter' || e.target.id !== 'defDepChamp') return;
  const code = trouverDepartementSaisi(e.target.value);
  if(!code){ notifier({ type: 'erreur', titre: 'Département inconnu', texte: 'Tape son numéro (16) ou son nom (Charente).' }); return; }
  basculerDefPrio(code);
});

""" + js[fin:]

# le bloc reste visible pour choisir ses departements, meme sans attaque
js = rempl(js, u"""  bloc.hidden = menaces.length === 0;
  if(menaces.length === 0){ liste.innerHTML = ''; return; }""", u"""  bloc.hidden = menaces.length === 0 && defPrio === null;
  if(bloc.hidden){ liste.innerHTML = ''; return; }""", 'bloc vide')

# chargement des priorites avec les menaces
js = rempl(js, u"""async function loadMenaces(){
  const { data, error } = await sb.rpc('sieges_contre_moi');""", u"""async function loadMenaces(){
  await chargerDefPrio();
  const { data, error } = await sb.rpc('sieges_contre_moi');""", 'load')
ecrire('app.js', js)


css = lire('style.css')
assert '.df-ligne' not in css
css += u"""
/* patch99 : Defendre lisible + departements prioritaires */
.df-prio{ display:flex; flex-direction:column; gap:8px; margin-bottom:10px; }
.df-prio-ligne{ display:flex; flex-wrap:wrap; align-items:center; gap:6px; }
.df-prio-t{ font-weight:700; font-size:.85rem; margin-right:4px; }
.df-dep{ border:1px solid rgba(240,180,41,.45); background: rgba(240,180,41,.1); color:#fff; border-radius:999px; padding:4px 10px; font:inherit; font-size:.78rem; font-weight:700; cursor:pointer; }
.df-dep span{ font-weight:400; color: var(--brume); }
.df-dep.ajout{ border-color: rgba(169,188,212,.3); background: transparent; }
.df-dep.plus{ border-style:dashed; border-color: rgba(169,188,212,.45); background:transparent; color: var(--brume); }
.df-sugg{ display:flex; flex-wrap:wrap; gap:6px; align-items:center; }
.df-sugg input{ flex:1 1 160px; min-width:0; background: var(--nuit-2); border:1px solid rgba(169,188,212,.25); border-radius:999px; color:#fff; padding:6px 12px; font:inherit; font-size:.8rem; }
.df-filtres{ display:flex; gap:8px; margin-bottom:12px; }
.df-aide{ margin:0 0 6px; font-size:.75rem; color: var(--brume); }
.df-bloc{ display:flex; flex-direction:column; gap:8px; margin-bottom:16px; }
.df-bloc h3, .df-bloc summary{ margin:0; font-family: var(--titre); font-weight:800; font-size:1.05rem; text-transform:uppercase; letter-spacing:.02em; display:flex; align-items:center; gap:8px; }
.df-bloc h3 span, .df-bloc summary span{ font-family: inherit; font-size:.75rem; background: rgba(255,255,255,.1); border-radius:999px; padding:1px 8px; }
.df-bloc.urgent h3{ color:#FF8A8D; }
.df-bloc.urgent h3 span{ background: var(--c-rouge); color:#fff; }
.df-bloc.repoussees summary{ cursor:pointer; color: var(--brume); list-style:none; }
.df-bloc.repoussees summary::-webkit-details-marker{ display:none; }
.df-bloc.repoussees summary::before{ content:'▸'; }
.df-bloc.repoussees[open] summary::before{ content:'▾'; }
.df-bloc.repoussees[open]{ gap:8px; }
.df-ligne{ background: var(--nuit-2); border:1px solid rgba(169,188,212,.16); border-radius:10px; padding:9px 12px; display:flex; flex-direction:column; gap:6px; }
.df-ligne.urgente{ border-left:3px solid var(--c-rouge); }
.df-ligne.prio{ border-color: rgba(240,180,41,.4); }
.df-tete{ display:flex; align-items:center; gap:6px; flex-wrap:wrap; font-size:.92rem; }
.df-tete b{ font-weight:700; }
.df-rarete{ font-size:.75rem; color: var(--brume); }
.df-bouclier{ margin-left:auto; display:inline-flex; align-items:center; gap:4px; font-size:.75rem; color:#9FD3FF; }
.df-bouclier svg{ width:13px; height:13px; }
.df-att{ display:flex; align-items:center; gap:10px; padding-left:15px; }
.df-qui{ flex:1; min-width:0; display:flex; flex-direction:column; font-size:.82rem; }
.df-qui small{ font-size:.72rem; color: var(--brume); }
.df-ligne.urgente .df-qui small{ color:#FFB3B5; }
.df-att .menace-defendre{ margin-top:0; font-size:.85rem; padding:5px 10px 6px; }
.df-note{ font-size:.72rem; color: var(--brume); font-style: italic; }
.df-epingle{ font-size:.85rem; }
.df-nb{ margin-left:4px; font-weight:800; color: var(--c-legendaire); }
"""
ecrire('style.css', css)
print(u'patch99 applique')
