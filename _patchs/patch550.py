# patch550 : Profil › Personnaliser devient le seul endroit (Mes cartes · Mon paquet · Mon territoire).
# L'onglet Atelier quitte la Boutique (ses blocs passent dans Mes cartes) ; la vitrine n'est plus en double.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
D = os.path.dirname(os.path.abspath(__file__))
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
def ajouter(f, src, marque):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if marque in t: print(f'{f} : déjà ajouté'); return
    open(p, 'a', encoding='utf-8').write(open(os.path.join(D, src), encoding='utf-8').read()); print(f'{f} : ajouté')
# l'atelier sait se rendre ailleurs que dans la Boutique
rep('app.js', "let atbVue = 'cartes';\n", "let atbVue = 'cartes', atbCible = null;   // patch550 : atbCible = rendre ailleurs (Personnaliser)\n")
rep('app.js', "function atbRendre(){\n  const corps = document.getElementById('atbCorps');", "function atbRendre(){\n  const corps = atbCible || document.getElementById('atbCorps');")
# la Boutique perd son onglet Atelier
rep('app.js', "  document.querySelectorAll('.vol-atelier').forEach(b => { b.hidden = !ok; });", "  document.querySelectorAll('.vol-atelier').forEach(b => { b.hidden = true; });   // patch550 : l'atelier est dans Profil › Personnaliser")
rep('app.js', """  const t = document.querySelector('.tab[data-tab="atelierbq"]');
  if(t) t.click();
  atbVue = 'territoire'; atbRendre();
  motOuvrir();""", """  grOuvrir('territoire');   // patch550
  motOuvrir();""")
rep('app.js', "dans Boutique › Atelier › Mon territoire.'", "dans Profil › Personnaliser › Mon territoire.'")
# la garde-robe en trois parties
rep('app.js', """  corps.innerHTML = `
    <div class="bourse-section gr-bloc">
      <h2>Mes cartes</h2>${atlBlocGardeRobe()}
      <div class="gr-titre">Dos de carte <span>${dos.length} possédé${dos.length > 1 ? 's' : ''}</span></div>
      <div class="gr-objets">${dos.map(o => tuile('dos', o, dosApercuHtml(o.id))).join('')}</div>
      ${SAISON2 ? blocDosCartesHtml() + blocSkinsHtml() : ''}
      <div class="gr-titre">Habillage de paquet <span>${habs.length} possédé${habs.length > 1 ? 's' : ''}</span></div>
      <div class="gr-objets">${habs.map(o => tuile('habillage', o, habVignette(habCle(o.id), 66))).join('')}</div>
      <div class="gr-voir"><p>D'autres dos et habillages t'attendent : à gagner en jouant ou dans la boutique.</p>
        <button type="button" class="bq-btn secondaire" data-gr-boutique>Voir la boutique</button></div>
    </div>
    <div class="bourse-section gr-bloc">
      <h2>Ma vitrine</h2>
      <div class="gr-vitrine"><span>${grVitrine == null ? 'Tes plus belles cartes Terra, sur ton profil' : `<b>${grVitrine} / ${VITRINE_MAX}</b> cartes exposées`}</span>
        <button type="button" class="bq-btn secondaire" data-gr-vitrine>Modifier</button></div>
    </div>`;
  habGl.demarrer();""", """  // patch550 : trois parties ; la vitrine reste dans Profil
  const voir = `<div class="gr-voir"><p>D'autres dos et habillages t'attendent : à gagner en jouant ou dans la boutique.</p>
        <button type="button" class="bq-btn secondaire" data-gr-boutique>Voir la boutique</button></div>`;
  if(grVue === 'paquet') corps.innerHTML = grSegHtml() + `
    <div class="bourse-section gr-bloc">
      <h2>Mon paquet</h2>
      <div class="gr-titre">Habillage de paquet <span>${habs.length} possédé${habs.length > 1 ? 's' : ''}</span></div>
      <div class="gr-objets">${habs.map(o => tuile('habillage', o, habVignette(habCle(o.id), 66))).join('')}</div>
      ${voir}
    </div>`;
  else if(grVue === 'territoire') corps.innerHTML = grSegHtml() + `
    <div class="bourse-section gr-bloc">
      <h2>Mon territoire</h2>
      <div class="gr-terr"><div class="atb-bloc atb-terr">${blocCouleur()}</div>${motBlocAtelier()}</div>
    </div>`;
  else corps.innerHTML = grSegHtml() + `
    <div class="bourse-section gr-bloc">
      <h2>Mes cartes</h2>${atlBlocGardeRobe()}<div class="gr-atb-moi"></div>
      <div class="gr-titre">Dos de carte <span>${dos.length} possédé${dos.length > 1 ? 's' : ''}</span></div>
      <div class="gr-objets">${dos.map(o => tuile('dos', o, dosApercuHtml(o.id))).join('')}</div>
      ${SAISON2 ? blocDosCartesHtml() + blocSkinsHtml() : ''}
      <div class="gr-atb-zone"><h3>Styles à débloquer</h3><div class="gr-atb"></div></div>
    </div>`;
  if(grVue === 'cartes') try{ grAtelierRemplir(corps); }catch(e){}
  if(grVue === 'territoire') try{ grTerrDessiner(corps); }catch(e){}
  if(grVue === 'paquet') habGl.demarrer();""")
ajouter('app.js', 'patch550-perso.js', 'patch550 : Personnaliser, le seul endroit')
ajouter('style.css', 'patch550.css', 'patch550 : Personnaliser en trois parties')
p = os.path.join(R, 'data/nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
assert d[0]['date'] == '2026-11-26'
n1 = "🎨 Tout ce qui se personnalise est maintenant au même endroit : Profil › Personnaliser, en trois parties (Mes cartes, Mon paquet, Mon territoire). L'atelier y a déménagé depuis la Boutique."
if n1 not in d[0]['nouveautes']: d[0]['nouveautes'].append(n1)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('nouveautes : ok')
