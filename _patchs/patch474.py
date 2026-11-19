# patch474 : le sélecteur Terra / Front reste collé en haut quand on fait défiler (idée d'Arkhannou, 19/11).
# Seulement sur téléphone, dans le style de la saison 3 (html.topo). Collé : ombre et fond flouté pour se détacher du contenu.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
rep('style.css', "  html.topo .mode-bascule button.terra{ min-width:0; }\n}",
    "  html.topo .mode-bascule button.terra{ min-width:0; }\n"
    "  /* patch474 : collé en haut quand on fait défiler (même place, l'en-tête part avec la page) */\n"
    "  html.topo .mode-bascule.colle{ position:fixed; top:calc(8px + env(safe-area-inset-top, 0px)); z-index:40;\n"
    "    box-shadow:0 10px 26px rgba(0,0,0,.5); background:rgba(23,34,54,.88); -webkit-backdrop-filter:blur(12px); backdrop-filter:blur(12px); }\n"
    "}")
rep('app.js', "  const entete = document.querySelector('.content .entete-mobile');\n  entete.insertAdjacentElement('afterend', el);\n",
    "  const entete = document.querySelector('.content .entete-mobile');\n  entete.insertAdjacentElement('afterend', el);\n"
    "  // patch474 : un repère en haut de la page ; quand il passe sous le haut de l'écran, le sélecteur est « collé »\n"
    "  if('IntersectionObserver' in window){\n"
    "    const repere = document.createElement('div'); repere.className = 'mb-repere'; repere.setAttribute('aria-hidden', 'true');\n"
    "    repere.style.cssText = 'position:absolute;left:0;top:0;width:1px;height:6px;pointer-events:none;visibility:hidden';\n"
    "    entete.before(repere);\n"
    "    new IntersectionObserver(([e]) => el.classList.toggle('colle', !e.isIntersecting && e.boundingClientRect.top < 0)).observe(repere);\n"
    "  }\n")
print('patch474 : fini')
