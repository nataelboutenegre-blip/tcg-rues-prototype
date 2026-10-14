# -*- coding: utf-8 -*-
u"""
patch132 — les distinctions de fin de saison et le badge OG (idée de
LeoLesel, badge OG : Nataël).

Le profil (le sien et la fiche des autres) montre un bloc « Distinctions » :
le badge OG (a joué la saison 1) et les titres de fin de saison (Le
Conquérant, Le Rempart...). Une petite marque « OG » suit le pseudo.
Les badges viennent de badges_joueur() (_sql/badges-1-installation.sql) ;
tant que la table est vide, rien ne s'affiche.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)
js = lire('app.js'); css = lire('style.css')
assert 'blocBadges' not in js, u'patch132 deja applique'

js = rempl(js, u"""function blocsProfil(p){""", u"""// ---------- patch132 : distinctions et badge OG ----------
const BADGES = {
  og:            { ico: 'OG', nom: 'OG',               texte: 'A joué la saison 1' },
  conquerant:    { ico: '🗺️', nom: 'Le Conquérant',    texte: 'Le plus de conquêtes', u: 'conquêtes' },
  rempart:       { ico: '🛡️', nom: 'Le Rempart',       texte: 'Le plus de défenses réussies', u: 'défenses' },
  cible:         { ico: '🎯', nom: 'La Cible',         texte: 'Le plus attaqué', u: 'attaques subies' },
  obstine:       { ico: '🪨', nom: 'L’Obstiné',        texte: 'Le plus d’assauts ratés', u: 'assauts ratés' },
  malchanceux:   { ico: '🍀', nom: 'Le Malchanceux',   texte: 'Le plus de communes perdues', u: 'communes perdues' },
  marchand:      { ico: '💰', nom: 'Le Marchand',      texte: 'Le plus de ventes à la Bourse', u: 'ventes' },
  diplomate:     { ico: '🤝', nom: 'Le Diplomate',     texte: 'Le plus d’échanges conclus', u: 'échanges' },
  collectionneur:{ ico: '🃏', nom: 'Le Collectionneur', texte: 'Le plus de communes', u: 'communes' },
  geographe:     { ico: '📍', nom: 'Le Géographe',     texte: 'La plus longue série à la Commune du jour', u: 'jours de série' },
  navigateur:    { ico: '📡', nom: 'Le Navigateur',    texte: 'Le meilleur Elo au Radar', u: 'Elo' },
};
const nomSaison = (s) => { const m = /(\\d+)$/.exec(String(s || '')); return m ? 'Saison ' + m[1] : ''; };
const estOG = (p) => (p.badges || []).some(b => b.badge === 'og');
const marqueOG = (p) => estOG(p) ? '<span class="bg-og-marque" title="A joué la saison 1">OG</span>' : '';
function blocBadges(p, fiche){
  const liste = (p.badges || []).filter(b => BADGES[b.badge])
    .sort((a, b) => (a.badge === 'og' ? -1 : b.badge === 'og' ? 1 : 0));
  if(!liste.length) return '';
  const items = liste.map(b => {
    const d = BADGES[b.badge];
    return `<div class="bg-badge ${b.badge === 'og' ? 'og' : ''}" title="${echapperTexte(d.texte)}">
      <span class="bg-medaille">${d.ico}</span>
      <span class="bg-txt"><b>${echapperTexte(d.nom)}</b><small>${echapperTexte(nomSaison(b.saison))}${b.valeur != null && b.badge !== 'og' ? ' · ' + Number(b.valeur).toLocaleString('fr-FR') + (d.u ? ' ' + d.u : '') : ''}</small></span>
    </div>`;
  }).join('');
  return fiche ? `<h3>Distinctions</h3><div class="bg-liste">${items}</div>`
               : `<div class="pf-bloc"><h3>Distinctions</h3><div class="bg-liste">${items}</div></div>`;
}

function blocsProfil(p){""", u'bloc')

# le panneau Profil : marque OG apres le pseudo, bloc apres la vitrine
js = rempl(js, u"""        <h2>${echapperTexte(p.pseudo)}</h2>
        <div class="pf-rangs">""", u"""        <h2>${echapperTexte(p.pseudo)}${marqueOG(p)}</h2>
        <div class="pf-rangs">""", u'pseudo panneau')
js = rempl(js, u"""    ${blocVitrine(p.vitrine || [], true)}
    ${blocsProfil(p)}""", u"""    ${blocVitrine(p.vitrine || [], true)}
    ${blocBadges(p, false)}
    ${blocsProfil(p)}""", u'bloc panneau')
# la fiche d'un joueur
js = rempl(js, u"""        <h2 id="prNom">${echapperTexte(p.pseudo)}</h2>""", u"""        <h2 id="prNom">${echapperTexte(p.pseudo)}${marqueOG(p)}</h2>""", u'pseudo fiche')
js = rempl(js, u"""        ${blocVitrine(p.vitrine || [], moi)}

        <h3>Territoire</h3>""", u"""        ${blocVitrine(p.vitrine || [], moi)}
        ${blocBadges(p, true)}

        <h3>Territoire</h3>""", u'bloc fiche')

css += u"""
/* ---------- patch132 : distinctions et badge OG ---------- */
.bg-liste{ display:grid; grid-template-columns:repeat(auto-fill, minmax(190px, 1fr)); gap:8px; margin-bottom:6px; }
.bg-badge{ display:flex; align-items:center; gap:10px; padding:8px 10px; border-radius:12px; background: rgba(255,255,255,.04); border:1px solid rgba(169,188,212,.16); min-width:0; }
.bg-medaille{ width:40px; height:40px; flex:none; border-radius:50%; display:grid; place-items:center; font-size:20px; line-height:1;
  background: radial-gradient(circle at 35% 30%, #2C4A75, #162C4B); box-shadow: inset 0 0 0 2px rgba(169,188,212,.35); }
.bg-txt{ display:flex; flex-direction:column; min-width:0; }
.bg-txt b{ font-family: var(--titre); font-weight:800; font-size:17px; letter-spacing:.02em; text-transform:uppercase; line-height:1.05; color:#fff; }
.bg-txt small{ font-size:12px; color: var(--brume); }
.bg-badge.og{ background: linear-gradient(120deg, rgba(120,220,255,.10), rgba(200,140,255,.10) 50%, rgba(255,210,140,.10)); border-color: rgba(200,180,255,.45); }
.bg-badge.og .bg-medaille{ width:46px; height:46px; border-radius:0; color:#16213A; font-family: var(--titre); font-weight:900; font-size:20px; letter-spacing:.02em;
  clip-path: polygon(50% 0, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%); box-shadow:none;
  background: linear-gradient(115deg, #8FF3FF 0%, #C7A6FF 28%, #FFB7E3 46%, #FFE7A3 64%, #9CF7C9 82%, #8FF3FF 100%); background-size:220% 220%;
  animation: ogHolo 6s ease-in-out infinite; }
.bg-badge.og .bg-txt b{ background: linear-gradient(90deg, #8FF3FF, #C7A6FF, #FFB7E3, #FFE7A3); -webkit-background-clip:text; background-clip:text; color:transparent; }
.bg-og-marque{ display:inline-block; margin-left:8px; vertical-align:middle; font-family: var(--titre); font-weight:900; font-size:.42em; letter-spacing:.06em;
  color:#16213A; border-radius:5px; padding:2px 6px 1px; line-height:1.1; transform:translateY(-3px);
  background: linear-gradient(115deg, #8FF3FF, #C7A6FF 35%, #FFB7E3 55%, #FFE7A3 80%); background-size:220% 220%; animation: ogHolo 6s ease-in-out infinite; }
@keyframes ogHolo{ 0%, 100%{ background-position:0% 50%; } 50%{ background-position:100% 50%; } }
@media (prefers-reduced-motion: reduce){ .bg-badge.og .bg-medaille, .bg-og-marque{ animation:none; } }
"""
# les badges arrivent par badges_joueur(), a cote de la vitrine
js = rempl(js, u"""    profilPanneau = data;
    profilPanneau.vitrine = await chargerVitrine(id);""", u"""    profilPanneau = data;
    [profilPanneau.vitrine, profilPanneau.badges] = await Promise.all([chargerVitrine(id), chargerBadges(id)]);""", u'badges panneau')
js = rempl(js, u"""  const [{ data, error }, vitrine] = await Promise.all([
    sb.rpc('profil_joueur', { p_joueur: joueurId }), chargerVitrine(joueurId)]);""", u"""  const [{ data, error }, vitrine, badges] = await Promise.all([
    sb.rpc('profil_joueur', { p_joueur: joueurId }), chargerVitrine(joueurId), chargerBadges(joueurId)]);""", u'badges fiche')
js = rempl(js, u"""  profilEnCours.vitrine = vitrine;""", u"""  profilEnCours.vitrine = vitrine;
  profilEnCours.badges = badges;""", u'badges fiche 2')
js = rempl(js, u"""function blocBadges(p, fiche){""", u"""// sans badges-1-installation.sql, la fonction n'existe pas : liste vide
async function chargerBadges(id){
  try{ const { data, error } = await sb.rpc('badges_joueur', { p_joueur: id }); return error ? [] : (data || []); }
  catch(e){ return []; }
}
function blocBadges(p, fiche){""", u'charger badges')
ecrire('app.js', js); ecrire('style.css', css)
print(u'patch132 applique')
