# -*- coding: utf-8 -*-
"""
patch43 — Le departement a cote du nom, dans Combat et Defense.

ETAT AVANT
  Combat  : le departement est deja la, en gros chiffre sur la vignette.
            On n'y touche pas : ce chiffre fait partie du dessin de la
            carte et il suffit.
  Defense : nulle part, ni dans les communes attaquees, ni dans la liste
            des boucliers, ni dans la fenetre d'achat de bouclier.

CE QUE FAIT CE CORRECTIF
  La pastille du departement, deja utilisee dans l'onglet Contrat, devient
  un element commun et se pose a cote du nom aux trois endroits de la
  Defense qui en manquaient.

  La classe passe de .ct-dp a .dep : elle ne sert plus seulement au
  contrat. Un seul emetteur, badgeDept(), pour que le jour ou on change
  l'apparence, on la change une fois.

"""
import io, os

BASE = os.path.dirname(os.path.abspath(__file__))

def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f:
        return f.read()

def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f:
        f.write(s)

def rempl(src, avant, apres, etiquette):
    n = src.count(avant)
    assert n == 1, u'%s : %d occurrences (attendu 1)' % (etiquette, n)
    return src.replace(avant, apres)


# ===========================================================================
#  style.css
# ===========================================================================
css = lire('style.css')

css = rempl(css,
u"""  .ct-dp{ font-size:0.62rem; font-weight:700; color:#7F91AB; flex-shrink:0;
          background:rgba(169,188,212,0.13); border-radius:4px; padding:1px 4px; }""",
u"""  /* la pastille du departement : contrat, combat, defense, boucliers */
  .dep{ font-size:0.62rem; font-weight:700; color:#7F91AB; flex-shrink:0;
        background:rgba(169,188,212,0.13); border-radius:4px; padding:1px 4px;
        vertical-align:middle; white-space:nowrap; }""",
u'pastille generique')

# --- Combat : le nom devient une ligne souple ------------------------------
css = rempl(css,
u"""  .ct-liste{ overflow-y:auto; flex:1; margin:0 -4px; padding:0 4px; }""",
u"""  .ct-liste{ overflow-y:auto; flex:1; margin:0 -4px; padding:0 4px; }

  /* Boucliers : la pastille suit le nom sur la meme ligne */
  .ligne-nom{ display:inline-flex; align-items:baseline; gap:6px;
              min-width:0; max-width:100%; }
  .ligne-nom span.nm-tx{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }""",
u'nom + pastille dans Combat et Boucliers')

ecrire('style.css', css)


# ===========================================================================
#  app.js
# ===========================================================================
js = lire('app.js')

# --- 1. la fonction devient commune et change de nom ------------------------
js = rempl(js,
u"""// La pastille du departement. Vide si la base ne le connait pas : mieux
// vaut pas de pastille qu'une pastille vide.
function ctDept(dep){
  const d = String(dep || '').trim();
  if(!d) return '';
  const nom = DEPT_NAMES[d] || '';
  return `<span class="ct-dp"${nom ? ` title="${echapperTexte(nom)}"` : ''}>${echapperTexte(d)}</span>`;
}""",
u"""// La pastille du departement, commune au contrat, au combat et a la
// defense. Vide si la base ne le connait pas : mieux vaut pas de pastille
// qu'une pastille vide. Un seul emetteur, pour n'avoir qu'un endroit a
// changer le jour ou son apparence bouge.
function badgeDept(dep){
  const d = String(dep || '').trim();
  if(!d) return '';
  const nom = DEPT_NAMES[d] || '';
  return `<span class="dep"${nom ? ` title="${echapperTexte(nom)}"` : ''}>${echapperTexte(d)}</span>`;
}""",
u'badgeDept')

js = js.replace(u'${ctDept(', u'${badgeDept(')

# --- 3. Defense : les communes attaquees ------------------------------------
# sieges_contre_moi() ne renvoie pas le departement, mais la commune est a
# moi : collectionMap le connait deja, et la variable est deja lue juste
# au-dessus pour le bouclier. Aucun changement en base.
js = rempl(js,
u"""<b>${m.nom}</b> <span>${tier ? '(' + tier.label.toLowerCase() + ')' : ''}, attaquée par ${echapperTexte(m.attaquant_pseudo)}</span>""",
u"""<b>${m.nom}</b>${badgeDept(miennne ? miennne.dept : '')} <span>${tier ? '(' + tier.label.toLowerCase() + ')' : ''}, attaquée par ${echapperTexte(m.attaquant_pseudo)}</span>""",
u'Defense : communes attaquees')

# --- 4. Defense : la liste des boucliers ------------------------------------
js = rempl(js,
u"""          <span class="ligne-nom">${e.nom}</span>
          <span class="ligne-etat ${etat.code === 'actif' || etat.code === 'programme' ? 'bleu' : ''}">""",
u"""          <span class="ligne-nom"><span class="nm-tx">${e.nom}</span>${badgeDept(e.dept)}</span>
          <span class="ligne-etat ${etat.code === 'actif' || etat.code === 'programme' ? 'bleu' : ''}">""",
u'Defense : liste des boucliers')

# --- 5. Defense : la fenetre d'achat de bouclier ----------------------------
# Ici il y a la place pour le nom entier du departement, comme a la Bourse.
js = rempl(js,
u"""        <p class="prix-commune">${echapperTexte(entry.nom)}, ${entry.tier.label.toLowerCase()}</p>""",
u"""        <p class="prix-commune">${echapperTexte(entry.nom)}${entry.dept ? ` — ${echapperTexte(DEPT_NAMES[entry.dept] || '')} (${echapperTexte(entry.dept)})` : ''}, ${entry.tier.label.toLowerCase()}</p>""",
u'Defense : fenetre du bouclier')

ecrire('app.js', js)

print(u'patch43 applique.')
