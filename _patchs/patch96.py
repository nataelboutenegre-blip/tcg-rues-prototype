# -*- coding: utf-8 -*-
u"""
patch96 — des points pour les mini-jeux. SQL : _sql/mini-jeux-gains.sql
(À PASSER AVANT LE PUSH : sans lui, l'app n'affiche simplement aucun gain).

- Commune du jour : 50 pts trouvée en 1 essai, puis 40, 30, 20, 15, 10.
  Écran de fin : « +40 pts sur ton solde ». Texte de l'onglet et carte du QG.
- Radar : 20 pts par victoire en duel classé, 5 victoires payées par jour.
  Résumé du duel : « +20 pts sur ton solde ». Carte du QG.
- Le solde affiché se met à jour après un gain.
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
assert 'mj-gain' not in js, u'patch96 deja applique'

# Commune du jour : ecran de fin + solde
js = rempl(js, u"""  z.innerHTML = `<h2 class="${e.trouve ? 'gagne' : ''}">${e.trouve ? `Trouvée en ${nb}` : 'Pas trouvée'}</h2>
""", u"""  z.innerHTML = `<h2 class="${e.trouve ? 'gagne' : ''}">${e.trouve ? `Trouvée en ${nb}` : 'Pas trouvée'}</h2>
    ${e.trouve && e.gain ? `<p class="mj-gain">+${Number(e.gain).toLocaleString('fr-FR')} pts sur ton solde</p>` : ''}
""", 'cdj fin', 2)   # aussi l'ecran du visiteur, sans gain (e.gain absent)
js = rempl(js, u"""      ({ data, error } = await sb.rpc('cdj_essayer', { p_code: cdjChoix.code }));
    }
    if(error) throw error;""", u"""      ({ data, error } = await sb.rpc('cdj_essayer', { p_code: cdjChoix.code }));
    }
    if(error) throw error;
    // patch96 : trouvee = des points, le solde affiche suit
    if(!cdjInvite && data && data.trouve && data.gain) loadPackStatus();""", 'cdj solde')

# Radar : resume d'un duel classe
js = rempl(js, u"""      <div class="rd-elo"><span>Elo</span><b class="${delta >= 0 ? 'plus' : 'moins'}">${delta >= 0 ? '+' : ''}${delta}</b><span class="qg-petit">${fmt(p.elo_apres)} · ${apres}${apres !== avant ? (delta > 0 ? ' (promu !)' : ' (rétrogradé)') : ''}</span></div>`;""",
           u"""      <div class="rd-elo"><span>Elo</span><b class="${delta >= 0 ? 'plus' : 'moins'}">${delta >= 0 ? '+' : ''}${delta}</b><span class="qg-petit">${fmt(p.elo_apres)} · ${apres}${apres !== avant ? (delta > 0 ? ' (promu !)' : ' (rétrogradé)') : ''}</span></div>
      ${p.gain ? `<p class="mj-gain">+${fmt(p.gain)} pts sur ton solde</p>` : ''}`;
    if(p.gain && !radarGainVu.has(p.id)){ radarGainVu.add(p.id); loadPackStatus(); }""", 'radar resume')
js = rempl(js, u"let cdjEtat = null;\n", u"let cdjEtat = null;\nconst radarGainVu = new Set();   // patch96 : un gain ne recharge le solde qu'une fois\n", 'radar vu')
ecrire('app.js', js)

html = lire('index.html')
html = rempl(html, u"<p>Solo · une commune mystère par jour</p>",
             u"<p>Solo · une commune mystère par jour · jusqu'à 50 pts</p>", 'qg cdj')
html = rempl(html, u"<p>Duel classé · place 5 communes sur la carte</p>",
             u"<p>Duel classé · 20 pts par victoire, 5 par jour</p>", 'qg radar')
html = rempl(html, u"Nouvelle commune chaque jour à minuit.</div>",
             u"Nouvelle commune chaque jour à minuit. La trouver rapporte des points : 50 en un essai, puis 40, 30, 20, 15 et 10.</div>", 'cdj sub')
ecrire('index.html', html)

css = lire('style.css')
assert '.mj-gain' not in css
css += u"""
/* patch96 : points gagnes aux mini-jeux */
.mj-gain{ align-self:flex-start; margin:0; padding:6px 12px; border-radius:999px; font-weight:800; font-size:.9rem;
  color:#0B2A1D !important; background: var(--c-peucommun); }
"""
ecrire('style.css', css)
print(u'patch96 applique')
