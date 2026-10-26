# -*- coding: utf-8 -*-
u"""
patch204 — skins : la grande vitrine anime ses cartes habillées (12 images
par seconde, l'effet d'apparition suit la révélation carte par carte) ; le
bilan du Tirage montre le skin de mes doublons. Aucun SQL.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)

js = lire('app.js')
assert 'patch204' not in js
def rempl(avant, apres):
    global js
    assert js.count(avant) == 1, (js.count(avant), avant[:70])
    js = js.replace(avant, apres)

rempl(u"""    // 1. les cartes en grand (fiche) : animées
    for(const mini of document.querySelectorAll('.c3d .mini')){
      const k = skinDe(mini);
      if(!skinConnu(k) || progs.get(k) === false){ if(mini.classList.contains('skin')) retirer(mini); continue; }
      const carte = mini.closest('.c3d-carte');
      const face = carte && !carte.classList.contains('retournee');
      if(!face){ if(carte) revs.delete(carte); continue; }
      const r = mini.getBoundingClientRect();
      if(!r.width || r.bottom < 0 || r.top > innerHeight) continue;
      const tex = texture(mini); const e = programme(k);
      if(!e || !tex.pret){ if(!tex.echec) attente = true; continue; }
      if(!revs.has(carte)) revs.set(carte, now);
      const [w, h] = taille(mini, r);
      const s = carte.style;
      const tilt = reduit ? [.15, -.1] : [(parseFloat(s.getPropertyValue('--ry')) || 0) / 20, -(parseFloat(s.getPropertyValue('--rx')) || 0) / 16];
      rendre(e, tex, w, h, reduit ? (SKIN_T_FIXE[k] || 2.2) : t, tilt, reduit ? 99 : (now - revs.get(carte)) / 1000);
      copier(habiller(mini, k, true), w, h);
      if(!reduit) anime = true;
    }""",
u"""    // 1. les cartes en grand (fiche) et la grande vitrine (patch204) : animées
    for(const mini of document.querySelectorAll('.c3d .mini, .vt-grande .mini')){
      const k = skinDe(mini);
      if(!skinConnu(k) || progs.get(k) === false){ if(mini.classList.contains('skin')) retirer(mini); continue; }
      const carte = mini.closest('.c3d-carte');
      if(carte && carte.classList.contains('retournee')){ revs.delete(carte); continue; }   // côté dos
      const r = mini.getBoundingClientRect();
      if(!r.width || r.bottom < 0 || r.top > innerHeight) continue;
      // la grande vitrine : 12 images par seconde, il peut y avoir 20 cartes
      if(!carte && !reduit && now - (mini._skt || 0) < 80){ anime = true; continue; }
      const tex = texture(mini); const e = programme(k);
      if(!e || !tex.pret){ if(!tex.echec) attente = true; continue; }
      const cleRev = carte || mini;
      if(!revs.has(cleRev)){
        // dans la grande vitrine, l'effet d'apparition attend que la carte se retourne
        const p = mini.closest('.vtg-rev');
        const d = p && !p.classList.contains('vtg-fini') ? (parseFloat(getComputedStyle(p).getPropertyValue('--vtg-d')) || 0) + .3 : 0;
        revs.set(cleRev, now + d * 1000);
      }
      mini._skt = now;
      if(mini._skph == null) mini._skph = Math.random() * 6.28;
      const [w, h] = taille(mini, r);
      let tilt;
      if(reduit) tilt = [.15, -.1];
      else if(carte){ const s = carte.style; tilt = [(parseFloat(s.getPropertyValue('--ry')) || 0) / 20, -(parseFloat(s.getPropertyValue('--rx')) || 0) / 16]; }
      else tilt = [Math.sin(t * .7 + mini._skph) * .42, Math.sin(t * .53 + 1 + mini._skph) * .28];
      rendre(e, tex, w, h, reduit ? (SKIN_T_FIXE[k] || 2.2) : t, tilt, reduit ? 99 : Math.max(0, (now - revs.get(cleRev)) / 1000));
      copier(habiller(mini, k, true), w, h);
      if(!reduit) anime = true;
    }""")
rempl(u"""        if(mini.closest('.c3d')) continue;
        const k = skinDe(mini);""",
u"""        if(mini.closest('.c3d, .vt-grande')) continue;   // animées plus haut
        const k = skinDe(mini);""")
rempl(u"""tierSize: d.tierSize, aurore: d.aurore ? 1 : 0 })}</div>`).join('')}</div>`;""",
u"""tierSize: d.tierSize, aurore: d.aurore ? 1 : 0, skin: d.terraNouvelle ? undefined : skinDeMaCarte('terra', d.code) })}</div>`).join('')}</div>`;""")
ecrire('app.js', js)
print(u'patch204 applique. Lancer : python3 maj-version.py')
