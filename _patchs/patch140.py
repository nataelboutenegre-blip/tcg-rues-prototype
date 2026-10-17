# -*- coding: utf-8 -*-
u"""
patch140 — carte d'attaque : la jauge dit « par round », et une ligne dessous
donne la vraie chance de prendre la commune selon la série en cours
(p^(3 - série)). Les joueurs lisaient 80 % comme « 80 % de conquérir » ;
à 80 % par round, 3 victoires d'affilée ne passent que 51 % du temps.
Sans défense du propriétaire ni garnison (qui a son propre avertissement).
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
assert 'pc-conquete' not in js, u'patch140 deja applique'

js = rempl(js, u"""    <div class="pc-jauge">
      <div class="pc-jauge-tete"><span>Chances de victoire</span><b>${a.chances} %</b></div>
      <div class="pc-jauge-barre"><i style="width:${a.chances}%"></i></div>
    </div>""", u"""    <div class="pc-jauge">
      <div class="pc-jauge-tete"><span>Chances de victoire (par round)</span><b>${a.chances} %</b></div>
      <div class="pc-jauge-barre"><i style="width:${a.chances}%"></i></div>
      ${ligneConquete(a.chances, serie)}
    </div>""", u'jauge')

js = rempl(js, u"""async function lancerAssaut(code){""", u"""// patch140 : la chance de PRENDRE la commune, pas seulement de gagner le round
function ligneConquete(chances, serie){
  const reste = Math.max(1, 3 - (Number(serie) || 0));
  const p = Math.max(0, Math.min(100, Number(chances) || 0)) / 100;
  const proba = Math.round(100 * Math.pow(p, reste));
  const txt = reste === 3 ? `Il faut 3 victoires d’affilée pour la prendre : <b>${proba}\\u00A0%</b> de chances d’y arriver sans perdre un round.`
            : reste === 2 ? `Encore 2 victoires d’affilée pour la prendre : <b>${proba}\\u00A0%</b> de chances.`
            :               `Une dernière victoire pour la prendre : <b>${proba}\\u00A0%</b> de chances.`;
  return `<p class="pc-conquete">${txt}</p>`;
}

async function lancerAssaut(code){""", u'fonction')

css += u"""
/* ---------- patch140 : chance de prendre la commune ---------- */
.pc-conquete{ margin:8px 0 0; font-size:.74rem; line-height:1.4; color:#8FA4BF; }
.pc-conquete b{ color:#fff; font-weight:600; }
"""
ecrire('app.js', js); ecrire('style.css', css)
print(u'patch140 applique')
