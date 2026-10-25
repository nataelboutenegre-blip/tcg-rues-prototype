# -*- coding: utf-8 -*-
u"""
patch186 — onglet Clan : toucher un clan du classement (ou en formation)
deplie ses membres : pseudo (ouvre la fiche), Chef, communes en Front,
point vert si joue dans les 7 derniers jours. Apercu valide le 26 octobre.
SQL : _sql/s2-28-clans-membres.sql (clan_membres_voir), a passer AVANT.
Sans le SQL : le depliage affiche « Membres indisponibles », rien ne casse.
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

js = lire('app.js')
assert 'clan_membres_voir' not in js, u'patch186 deja applique'

# 1. les outils : etat ouvert / ferme, cache des membres, bloc deplie
js = rempl(js, u"""function membreActif(a){""", u"""// patch186 : les membres des autres clans, depliables dans le classement
const clansOuverts = new Set();
const clanMembresVus = new Map();   // clan_id -> liste, 'erreur' ou 'charge'
const CHEVRON_CLAN = '<svg class="cl-chevron" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M5 8l5 5 5-5"/></svg>';
function membresClanHtml(x, chef){
  const liste = clanMembresVus.get(x.clan_id);
  let corps;
  if(liste === 'charge' || liste === undefined) corps = '<div class="cl-pied">Chargement…</div>';
  else if(liste === 'erreur') corps = '<div class="cl-pied">Membres indisponibles pour le moment.</div>';
  else {
    const actifs = liste.filter(m => membreActif(m)).length;
    corps = liste.map(m => {
      const j = joursDepuis(m.dernier_jour);
      const actif = membreActif(m);
      const etat = actif ? 'Actif' : (j === null ? 'Pas encore joué' : `Absent depuis ${j} jour${j > 1 ? 's' : ''}`);
      return `<div class="cl-mb"><span class="av" aria-hidden="true">${echapperTexte((m.pseudo || '?')[0].toUpperCase())}</span>
        <div class="qui"><button type="button" class="cl-mb-pseudo" data-clan-profil="${echapperTexte(m.joueur_id)}">${echapperTexte(m.pseudo)}</button>
          <div class="cl-mb-info"><span class="cl-mb-point${actif ? '' : ' off'}" aria-hidden="true"></span>${etat}${m.chef ? ' · <span class="cl-mb-chef">Chef</span>' : ''}</div></div>
        <span class="cl-mb-nb"><b>${nbClan(m.communes)}</b> commune${m.communes > 1 ? 's' : ''}</span></div>`;
    }).join('') + (chef
      ? `<div class="cl-pied">Pour le rejoindre, demande une invitation à ${echapperTexte(chef)} (Discord, salon recrutement-clans).</div>`
      : `<div class="cl-pied">${liste.length} membre${liste.length > 1 ? 's' : ''} sur 6 · ${actifs} actif${actifs > 1 ? 's' : ''}</div>`);
  }
  return `<div class="cl-membres" style="--clan:${x.couleur}">${corps}</div>`;
}
async function basculerClanVu(id){
  if(clansOuverts.has(id)){ clansOuverts.delete(id); renderClan(); return; }
  clansOuverts.add(id);
  const deja = clanMembresVus.get(id);
  if(Array.isArray(deja)){ renderClan(); return; }
  clanMembresVus.set(id, 'charge');
  renderClan();
  try{
    const { data, error } = await sb.rpc('clan_membres_voir', { p_clan: id });
    clanMembresVus.set(id, error ? 'erreur' : (data || []));
  }catch(e){ clanMembresVus.set(id, 'erreur'); }
  renderClan();
}
function membreActif(a){""", 'outils')

# 2. le classement : lignes cliquables
js = rempl(js, u"""    ? classement.map((x, i) => `<div class="cl-ligne${c && x.clan_id === c.id ? ' moi' : ''}"><b>${i + 1}</b>${blasonHtml(x.tag, x.couleur, true)}<span>${echapperTexte(x.nom)}</span><span class="cl-score">${nbClan(x.moyenne)}<small>${x.actifs != null ? 'par membre actif' : 'par membre'}</small></span></div>`).join('')""",
u"""    ? classement.map((x, i) => `<div class="cl-bloc"><button type="button" class="cl-ligne cl-depli${c && x.clan_id === c.id ? ' moi' : ''}" data-clan-voir="${x.clan_id}" aria-expanded="${clansOuverts.has(x.clan_id)}"><b>${i + 1}</b>${blasonHtml(x.tag, x.couleur, true)}<span class="cl-nom">${echapperTexte(x.nom)}</span><span class="cl-score">${nbClan(x.moyenne)}<small>${x.actifs != null ? 'par membre actif' : 'par membre'}</small></span>${CHEVRON_CLAN}</button>${clansOuverts.has(x.clan_id) ? membresClanHtml(x) : ''}</div>`).join('') + '<p class="clan-note">Touche un clan pour voir ses membres.</p>'""", 'classement')

# 3. les clans en formation : idem
js = rempl(js, u"""    ${formation.map(x => `<div class="cl-ligne formation">${blasonHtml(x.tag, x.couleur, true)}<span>${echapperTexte(x.nom)}<small>${x.chef ? 'chef : ' + echapperTexte(x.chef) : ''}</small></span><span class="cl-score">${x.membres} / 3<small>membres</small></span></div>`).join('')}""",
u"""    ${formation.map(x => `<div class="cl-bloc"><button type="button" class="cl-ligne cl-depli formation" data-clan-voir="${x.clan_id}" aria-expanded="${clansOuverts.has(x.clan_id)}">${blasonHtml(x.tag, x.couleur, true)}<span class="cl-nom">${echapperTexte(x.nom)}<small>${x.chef ? 'chef : ' + echapperTexte(x.chef) : ''}</small></span><span class="cl-score">${x.membres} / 3<small>membres</small></span>${CHEVRON_CLAN}</button>${clansOuverts.has(x.clan_id) ? membresClanHtml(x, x.chef || 'son chef') : ''}</div>`).join('')}""", 'formation')

# 4. les clics
js = rempl(js, u"""  if(b.dataset.clanCouleur){ clanCouleurChoisie""", u"""  if(b.dataset.clanVoir){ basculerClanVu(b.dataset.clanVoir); return; }   // patch186
  if(b.dataset.clanProfil){ ouvrirProfil(b.dataset.clanProfil); return; }
  if(b.dataset.clanCouleur){ clanCouleurChoisie""", 'clics')
ecrire('app.js', js)

css = lire('style.css')
css = rempl(css, u""".clan-carte .cl-ligne.moi{""", u"""/* patch186 : les membres des clans, depliables */
.clan-carte .cl-bloc{ border-top:1px solid rgba(169,188,212,0.1); }
.clan-carte .cl-bloc .cl-ligne{ border-top:0; }
.clan-carte .cl-depli{ width:100%; grid-template-columns:22px 30px minmax(0,1fr) auto 18px; background:none; border:0; color:inherit; font:inherit; text-align:left; cursor:pointer; border-radius:8px; }
.clan-carte .cl-depli.formation{ grid-template-columns:30px minmax(0,1fr) auto 18px; }
.clan-carte .cl-depli:hover{ background: rgba(169,188,212,0.06); }
.clan-carte .cl-depli:focus-visible{ outline:2px solid var(--c-legendaire); outline-offset:2px; }
.clan-carte .cl-nom{ min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.clan-carte .cl-nom small{ display:block; color: var(--brume); font-size:.75rem; }
.cl-chevron{ width:18px; height:18px; color: var(--brume); transition: transform .18s ease; }
.cl-depli[aria-expanded="true"] .cl-chevron{ transform: rotate(180deg); color: var(--c-legendaire); }
.cl-membres{ --clan:#E07A2E; margin:2px 0 10px 34px; padding:6px 10px 8px; background: rgba(11,23,43,0.6); border-radius:10px; border-left:2px solid var(--clan); }
.cl-mb{ display:grid; grid-template-columns:28px minmax(0,1fr) auto; gap:10px; align-items:center; padding:7px 0; }
.cl-mb + .cl-mb{ border-top:1px solid rgba(169,188,212,0.12); }
.cl-mb .av{ width:28px; height:28px; border-radius:50%; background: var(--nuit-3); display:flex; align-items:center; justify-content:center; font-family: var(--titre); font-weight:800; font-size:.85rem; box-shadow:0 0 0 2px var(--clan); }
.cl-mb .qui{ min-width:0; }
.cl-mb-pseudo{ background:none; border:0; padding:0; color:#fff; font:inherit; font-weight:600; cursor:pointer; text-decoration:underline; text-decoration-color: rgba(169,188,212,.35); text-underline-offset:3px; max-width:100%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.cl-mb-pseudo:hover{ text-decoration-color: var(--c-legendaire); }
.cl-mb-info{ display:flex; gap:6px; align-items:center; flex-wrap:wrap; color: var(--brume); font-size:.76rem; margin-top:2px; }
.cl-mb-chef{ color: var(--c-legendaire); font-weight:700; }
.cl-mb-point{ width:7px; height:7px; border-radius:50%; background:#3DDC84; box-shadow:0 0 6px rgba(61,220,132,.6); display:inline-block; }
.cl-mb-point.off{ background:#5B6E88; box-shadow:none; }
.cl-mb-nb{ color: var(--brume); font-size:.82rem; text-align:right; font-variant-numeric: tabular-nums; white-space:nowrap; }
.cl-mb-nb b{ color:#fff; }
.cl-membres .cl-pied{ color: var(--brume); font-size:.76rem; padding-top:6px; border-top:1px solid rgba(169,188,212,0.12); margin-top:2px; }
@media (max-width:720px){ .cl-membres{ margin-left:8px; } }
@media (prefers-reduced-motion: reduce){ .cl-chevron{ transition:none; } }
.clan-carte .cl-ligne.moi{""", 'css')
ecrire('style.css', css)
print(u'patch186 applique. Lancer : python3 maj-version.py')
