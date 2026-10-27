# -*- coding: utf-8 -*-
u"""
patch224 — notifications par département (aperçu montré le 27/10 ; s2-39).

- Réglages de la cloche : le cadre sous « On t'attaque » résume les
  départements « dès la 1re attaque » et la sourdine ; « Gérer » toujours là.
- Écran « Par département » : ⚡ prévenir dès la 1re attaque (le seuil de
  rareté ne s'applique pas), 🔕 départements en sourdine, communes en
  sourdine. Ajout par recherche (nom ou numéro).
- Dans la cloche, 🔕 sur une attaque propose : cette commune / tout le
  département.
- La cloche applique les deux listes (sourdine du département, seuil ignoré
  pour les départements « dès la 1re attaque »).
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rep(s, a, b, n=1):
    c = s.count(a); assert c == n, ('MATCH', a[:70], 'trouve', c, 'attendu', n); return s.replace(a, b)

s = lire('app.js')

# 1. valeurs par défaut et lecture des préférences
s = rep(s, "tel: { attaque: true, paquet: true }, seuil: 'commun', sourdine: [] };",
           "tel: { attaque: true, paquet: true }, seuil: 'commun', sourdine: [], sourdine_dep: [], alerte_dep: [] };")
s = rep(s, "           sourdine: Array.isArray(p.sourdine) ? p.sourdine.map(String) : [] };",
           "           sourdine: Array.isArray(p.sourdine) ? p.sourdine.map(String) : [],\n"
           "           sourdine_dep: Array.isArray(p.sourdine_dep) ? p.sourdine_dep.map(String) : [],   // patch224\n"
           "           alerte_dep: Array.isArray(p.alerte_dep) ? p.alerte_dep.map(String) : [] };")

# 2. la cloche applique les départements
s = rep(s, "      if(nb(m.victoires_consecutives) < 1 || p.sourdine.includes(String(m.commune_code)) || sousSeuil(m.commune_code)) continue;",
           "      const depM = ncDepDe(m.commune_code);   // patch224\n"
           "      if(nb(m.victoires_consecutives) < 1 || p.sourdine.includes(String(m.commune_code)) || p.sourdine_dep.includes(depM)) continue;\n"
           "      if(!p.alerte_dep.includes(depM) && sousSeuil(m.commune_code)) continue;")

# 3. le 🔕 d'une attaque ouvre le choix commune / département
s = rep(s, "    ${it.sourdine ? `<button type=\"button\" class=\"nc-muet\" data-nc-muet=\"${echapperTexte(it.sourdine)}\" title=\"Ne plus me prévenir pour cette commune\" aria-label=\"Ne plus me prévenir pour cette commune\">🔕</button>` : ''}</div>`;",
           "    ${it.sourdine ? `<button type=\"button\" class=\"nc-muet\" data-nc-muet=\"${echapperTexte(it.sourdine)}\" aria-expanded=\"${NC.muet === it.sourdine}\" title=\"Ne plus être prévenu\" aria-label=\"Ne plus être prévenu des attaques ici\">🔕</button>` : ''}</div>`\n"
           "    + (it.sourdine && NC.muet === it.sourdine ? ncMuetChoix(it.sourdine) : '');")

# 4. le résumé dans les réglages
s = rep(s, "<div class=\"nc-sourdine\"><span>🔕 <b>${p.sourdine.length} commune${p.sourdine.length > 1 ? 's' : ''}</b> en sourdine</span>${p.sourdine.length ? '<button type=\"button\" data-nc=\"sourdine\">Gérer</button>' : ''}</div>",
           "<div class=\"nc-sourdine\"><span>${ncResumeDep(p)}</span>${off ? '' : '<button type=\"button\" data-nc=\"sourdine\">Gérer</button>'}</div>")

# 5. l'écran « Par département » remplace « En sourdine »
a = s.index("function ncRendreSourdine(el){")
b = s.index("async function ncRegler(fn, args){", a)
s = s[:a] + lire('_patchs/patch224-ecran.js') + "\n" + s[b:]

# 6. les clics
s = rep(s, """  if(b.dataset.ncMuet){
    const code = b.dataset.ncMuet, nom = (collectionMap.get(code) || {}).nom || code;""",
"""  if(b.dataset.ncMuet){ NC.muet = NC.muet === b.dataset.ncMuet ? null : b.dataset.ncMuet; return ncRendre(); }   // patch224
  if(b.dataset.ncMuetDep){
    const d = b.dataset.ncMuetDep;
    NC.muet = null;
    if(await ncRegler('notif_departement', { p_liste: 'sourdine', p_dep: d, p_on: true }))
      notifier({ type: 'info', titre: `${DEPT_NAMES[d] || d} en sourdine`, texte: 'Tu ne seras plus prévenu des attaques dans ce département. Ça se réactive dans les réglages de la cloche.' });
    return ncRendre();
  }
  if(b.dataset.ncDepAjout){
    NC.depListe = NC.depListe === b.dataset.ncDepAjout ? null : b.dataset.ncDepAjout;
    NC.depQ = ''; NC.depFocus = true;
    return ncRendre();
  }
  if(b.dataset.ncDep){
    const [liste, d, on] = b.dataset.ncDep.split('|');
    if(await ncRegler('notif_departement', { p_liste: liste, p_dep: d, p_on: on === '1' }) && on === '1'){ NC.depQ = ''; NC.depFocus = true; }
    return ncRendre();
  }
  if(b.dataset.ncMuetOk){
    NC.muet = null;
    const code = b.dataset.ncMuetOk, nom = (collectionMap.get(code) || {}).nom || code;""")

# 7. la recherche de département
s = rep(s, "    document.getElementById('ncPanneau').addEventListener('click', ncClic);",
           "    document.getElementById('ncPanneau').addEventListener('click', ncClic);\n"
           "    document.getElementById('ncPanneau').addEventListener('input', ncSaisie);   // patch224")
ecrire('app.js', s)

c = lire('style.css')
assert 'nc-s-sec' not in c
c = c.rstrip('\n') + '\n' + lire('_patchs/patch224.css')
ecrire('style.css', c)
print('patch224 ok')
