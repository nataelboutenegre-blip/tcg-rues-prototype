# -*- coding: utf-8 -*-
u"""
patch176 — clans en formation (25 octobre 2026). Sous le classement des
clans : les clans de 1 ou 2 membres, avec leur chef, pour qu'on puisse lui
demander une invitation. SQL : _sql/clans-en-formation.sql (sans lui, la
liste n'apparaît simplement pas).
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
assert 'clans_en_formation' not in js, u'patch176 deja applique'
js = rempl(js, u"""  const [mc, cl] = await Promise.all([sb.rpc('mon_clan'), sb.rpc('clans_classement')]);
  if(mc.error){ zone.innerHTML = `<p class="collection-empty">${echapperTexte(messageLisible(mc.error.message))}</p>`; return; }
  clanCache = { moi: mc.data || {}, classement: cl.error ? [] : (cl.data || []) };""",
u"""  const [mc, cl, cf] = await Promise.all([sb.rpc('mon_clan'), sb.rpc('clans_classement'), sb.rpc('clans_en_formation')]);
  if(mc.error){ zone.innerHTML = `<p class="collection-empty">${echapperTexte(messageLisible(mc.error.message))}</p>`; return; }
  clanCache = { moi: mc.data || {}, classement: cl.error ? [] : (cl.data || []), formation: cf.error ? [] : (cf.data || []) };""", 'loadClan')
js = rempl(js, u"""  const blocClassement = `<div class="clan-carte"><h2>Classement des clans</h2>${lignesClassement}
    <p class="clan-note">À la moyenne de communes du Front par membre, jamais au total : un gros clan n'a pas d'avantage.</p></div>`;""",
u"""  // patch176 : les clans de 1 ou 2 membres, pour pouvoir demander une invitation
  const formation = (clanCache.formation || []).filter(x => !c || x.clan_id !== c.id);
  const blocFormation = formation.length ? `<h3 class="cl-formation-titre">En formation <small>${formation.length} clan${formation.length > 1 ? 's' : ''} cherche${formation.length > 1 ? 'nt' : ''} des membres</small></h3>
    ${formation.map(x => `<div class="cl-ligne formation">${blasonHtml(x.tag, x.couleur, true)}<span>${echapperTexte(x.nom)}<small>${x.chef ? 'chef : ' + echapperTexte(x.chef) : ''}</small></span><span class="cl-score">${x.membres} / 3<small>membres</small></span></div>`).join('')}
    <p class="clan-note">Pour en rejoindre un, demande une invitation à son chef (sur le Discord, salon recrutement-clans). Il sera classé à partir de 3 membres.</p>` : '';
  const blocClassement = `<div class="clan-carte"><h2>Classement des clans</h2>${lignesClassement}
    <p class="clan-note">À la moyenne de communes du Front par membre, jamais au total : un gros clan n'a pas d'avantage.</p>${blocFormation}</div>`;""", 'classement')
ecrire('app.js', js)
css = lire('style.css')
assert 'patch176' not in css
css += u"""

/* ---------- patch176 : clans en formation ---------- */
.cl-formation-titre{ font-family: var(--titre); font-weight: 800; font-size: 1.15rem; margin: 20px 0 8px; padding-top: 14px; border-top: 1px solid rgba(169,188,212,0.16); }
.cl-formation-titre small{ font-family: var(--texte); font-weight: 500; font-size: .78rem; color: var(--brume); margin-left: 6px; }
.clan-carte .cl-ligne.formation{ grid-template-columns: 30px minmax(0,1fr) auto; cursor: default; }
.cl-ligne.formation span small{ display: block; color: var(--brume); font-size: .74rem; }
.cl-ligne.formation .cl-score{ color: var(--brume); font-size: 1.05rem; }
"""
ecrire('style.css', css)
print(u'patch176 applique')
