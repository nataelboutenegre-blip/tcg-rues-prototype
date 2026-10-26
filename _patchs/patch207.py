# -*- coding: utf-8 -*-
u"""
patch207 — la fiche d'achat de la boutique montre l'objet en grand avant
d'acheter : la carte 3D du jeu (inclinable, retournable) avec le dos ou le
skin ; une collection montre le skin devant et le dos derrière ; un
habillage montre le paquet en grand. Ma plus belle carte Terra sert d'exemple.
Les objets déjà possédés s'ouvrent aussi en aperçu (sans achat). Aucun SQL.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)

js = lire('app.js')
assert 'patch207' not in js
def rempl(avant, apres):
    global js
    assert js.count(avant) == 1, (js.count(avant), avant[:70])
    js = js.replace(avant, apres)

# la fiche d'achat arme sa carte 3D (avant d'ajouter l'aperçu seul, qui a la même ligne)
rempl(u"""  f.querySelector('.bqe-fermer').addEventListener('click', () => fermer(null));
  habGl.demarrer();""", u"""  f.querySelector('.bqe-fermer').addEventListener('click', () => fermer(null));
  bqeArmerApercu(f, a);   // patch207
  habGl.demarrer();""")

# l'aperçu en grand
rempl(u"""function bqeOuvrirFiche(id){""", u"""// patch207 : l'objet en grand, sur une vraie carte du jeu
function bqeGrandApercu(a){
  const ex = { ...carteExemple(), exemplaires: 1, aurore: 0 };
  const c = a.contenu || [];
  if(a.type === 'dos') return carte3dDebut(150, 225, 1.45) + miniTerra(ex) + carte3dFin(dosCle(a.id));
  if(a.type === 'skin') return carte3dDebut(150, 225, 1.45) + miniTerra({ ...ex, skin: skinCle(a.id) }) + carte3dFin();
  if(a.type === 'collection'){
    const d = c.find(x => x.startsWith('dos-')), s = c.find(x => x.startsWith('skin-'));
    return carte3dDebut(150, 225, 1.45) + miniTerra({ ...ex, skin: skinCle(s) }) + carte3dFin(dosCle(d));
  }
  return `<div class="hab-grand bqe-hab-grand">${habVignette(habCle(a.id), 150).replace('data-fixe="1" ', '')}</div>`;
}
function bqeArmerApercu(f, a){
  const c3d = f.querySelector('.bqe-apercu .c3d');
  if(!c3d) return;
  armerCarte3d(c3d);
  // un dos se montre côté dos ; skin et collection côté face (on retourne pour voir le dos)
  if(a.type === 'dos'){ const carte = c3d.querySelector('.c3d-carte'); if(carte) carte.classList.add('retournee'); }
  const aide = c3d.querySelector('.c3d-aide');
  if(aide && a.type === 'collection') aide.textContent = 'Fais glisser pour incliner · touche pour voir le dos';
}
function bqeApercuSeul(a){
  const fermer = ouvrirFenetre(`
    <div class="fenetre bqe-fiche bqe-fiche-apercu" role="dialog" aria-modal="true" aria-labelledby="bqeNomA">
      <button type="button" class="bqe-fermer" aria-label="Fermer">×</button>
      <div class="bqe-apercu">${bqeGrandApercu(a)}</div>
      <div class="bqe-tete-a"><small>Dans ta garde-robe</small><h2 id="bqeNomA">${echapperTexte(bqeNomCourt(a))}</h2></div>
      <p class="bqe-recoit">${echapperTexte(a.description || '')}. Tu l'as déjà : équipe-le ou pose-le sur tes cartes dans Profil › Personnaliser.</p>
    </div>`);
  const f = document.querySelector('#fenetre .bqe-fiche-apercu');
  if(!f) return;
  f.querySelector('.bqe-fermer').addEventListener('click', () => fermer(null));
  bqeArmerApercu(f, a);
  habGl.demarrer();
}

function bqeOuvrirFiche(id){""")

# les objets possédés : aperçu au lieu d'une simple notification
rempl(u"""  if(a.possede){ notifier({ type: 'info', titre: 'Tu l\\'as déjà', texte: 'Il est dans Profil › Personnaliser.' }); return; }""",
      u"""  if(a.possede){ bqeApercuSeul(a); return; }   // patch207""")

# la fiche d'achat : l'aperçu en grand au-dessus du titre
rempl(u"""const grand = a.type === 'dos' ? dosApercuHtml(a.id) : a.type === 'skin' || a.type === 'collection' ? bqeVignette(a) : `<div class="hab-grand">${habVignette(habCle(a.id), 92).replace('data-fixe="1" ', '')}</div>`;""",
      u"""const grand = bqeGrandApercu(a);   // patch207""")
rempl(u"""      <div class="bqe-tete"><div class="bqe-grand">${grand}</div>""",
      u"""      <div class="bqe-apercu">${grand}</div>
      <div class="bqe-tete">""")
ecrire('app.js', js)

css = lire('style.css')
assert 'patch207' not in css
css = css.rstrip('\n') + u"""

/* ---------- patch207 : l'objet en grand dans la fiche d'achat ---------- */
.bqe-apercu{ display: grid; justify-items: center; padding: 4px 0 2px; }
.bqe-apercu .c3d-aide{ font-size: .72rem; }
.bqe-hab-grand{ display: grid; justify-items: center; }
.bqe-fiche .bqe-tete{ grid-template-columns: minmax(0, 1fr); padding-right: 0; text-align: center; }
.bqe-tete-a{ text-align: center; }
.bqe-tete-a small{ color: var(--brume); font-size: .78rem; }
.bqe-tete-a h2{ font-family: var(--titre); font-weight: 900; font-size: 1.9rem; line-height: .95; margin: 2px 0; }
.fenetre.bqe-fiche{ max-height: 92vh; overflow-y: auto; }
"""
ecrire('style.css', css)
print(u'patch207 applique. Lancer : python3 maj-version.py')
