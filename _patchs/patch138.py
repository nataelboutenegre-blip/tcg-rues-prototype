# -*- coding: utf-8 -*-
u"""
patch138 — bloc « Échanges » sur le profil (idée d'Arkhannou) : échanges
conclus et joueurs différents. Chiffres lus par echanges_joueur()
(_sql/echanges-profil.sql), chargés à part comme les badges : si la fonction
manque, le bloc ne s'affiche pas. Sur deux colonnes, Assiduité occupe deux
rangées pour qu'Échanges vienne juste sous Défense.
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
assert 'chargerStatEchanges' not in js, u'patch138 deja applique'

js = rempl(js, u"""// sans badges-1-installation.sql, la fonction n'existe pas : liste vide
async function chargerBadges(id){""", u"""// patch138 : sans echanges-profil.sql, la fonction n'existe pas : null, pas de bloc
async function chargerStatEchanges(id){
  try{ const { data, error } = await sb.rpc('echanges_joueur', { p_joueur: id }); return error ? null : (data || null); }
  catch(e){ return null; }
}
// sans badges-1-installation.sql, la fonction n'existe pas : liste vide
async function chargerBadges(id){""", u'fonction')

js = rempl(js, u"""    <div class="pf-bloc">
      <h3>Assiduité</h3>""", u"""    <div class="pf-bloc pf-assid">
      <h3>Assiduité</h3>""", u'assiduite')

js = rempl(js, u"""      <div class="pf-ligne"><span>Cartes tirées</span><b>${nb(p.cartes_tirees)}</b></div>
    </div>` : '';""", u"""      <div class="pf-ligne"><span>Cartes tirées</span><b>${nb(p.cartes_tirees)}</b></div>
    </div>
    ${p.echanges ? `<div class="pf-bloc">
      <h3>Échanges</h3>
      <div class="pf-paire">
        <div class="pf-ch"><b style="color:var(--c-legendaire)">${nb(p.echanges.echanges)}</b><span>échange${Number(p.echanges.echanges) > 1 ? 's' : ''} conclu${Number(p.echanges.echanges) > 1 ? 's' : ''}</span></div>
        <div class="pf-ch"><b>${nb(p.echanges.partenaires)}</b><span>joueur${Number(p.echanges.partenaires) > 1 ? 's' : ''} différent${Number(p.echanges.partenaires) > 1 ? 's' : ''}</span></div>
      </div>
    </div>` : ''}` : '';""", u'bloc')

js = rempl(js, u"""    [profilPanneau.vitrine, profilPanneau.badges] = await Promise.all([chargerVitrine(id), chargerBadges(id)]);""",
 u"""    [profilPanneau.vitrine, profilPanneau.badges, profilPanneau.echanges] = await Promise.all([chargerVitrine(id), chargerBadges(id), chargerStatEchanges(id)]);""", u'chargement')

css += u"""
/* ---------- patch138 : bloc Échanges du profil ---------- */
/* Assiduité sur deux rangées : Échanges remonte sous Défense (sans effet sur une colonne) */
.pf-bloc.pf-assid{ grid-row: span 2; }
"""
ecrire('app.js', js); ecrire('style.css', css)
print(u'patch138 applique')
