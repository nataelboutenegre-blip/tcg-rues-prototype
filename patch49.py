# -*- coding: utf-8 -*-
u"""
patch49 — La Collection et la Bourse passent aussi par lots.

Le mecanisme afficherParLots() a ete ecrit generique au patch precedent.
On l'applique aux trois dernieres grosses listes :

  Collection de Maroli    38 491 elements
  Bourse, mes communes    14 663
  Bourse, les annonces     (varie)
  Defense, les boucliers   4 938

CE QUI EST PARTICULIER A LA COLLECTION
  Ses cartes portent maintenant une photo. L'affichage par lots et le
  chargement differe des images vont dans le meme sens : une carte qui
  n'est pas fabriquee ne demande pas sa photo. Pour un joueur qui cherche
  une commune precise, cela fait zero image telechargee au lieu de 900.

CE QUI RESTE VRAI
  Un changement de filtre repart du premier lot. Un simple rafraichissement
  garde le nombre de cartes affichees. C'est la signature passee a
  afficherParLots() qui fait la difference.
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


js = lire('app.js')

# ---------------------------------------------------------------------------
#  1. La Collection
# ---------------------------------------------------------------------------
js = rempl(js,
u"""  gridEl.innerHTML = visibles.map(entry => {
    const s = sieges.get(entry.code);""",
u"""  const carteMini = (entry) => {
    const s = sieges.get(entry.code);""",
u'fabrique d une vignette de collection')

js = rempl(js,
u"""        <div class="mini-lisere"><span></span><span></span><span></span></div>
      </div>
    </div>`;
  }).join('');
}""",
u"""        <div class="mini-lisere"><span></span><span></span><span></span></div>
      </div>
    </div>`;
  };

  // le siege d'une commune peut changer sans que le joueur ait touche a un
  // filtre : il ne doit pas perdre sa place pour autant, donc il n'entre pas
  // dans la signature
  const signature = [vueCollection, collectionFilterTier, etiquetteFiltre,
                     recherche, visibles.length].join('|');
  afficherParLots(gridEl, visibles, carteMini, signature);
}""",
u'appel a afficherParLots pour la Collection')

# ---------------------------------------------------------------------------
#  2. La Defense : les boucliers
# ---------------------------------------------------------------------------
js = rempl(js,
u"""  grid.innerHTML = protegeables.map(e => {
    const etat = etatBouclier(e, now);""",
u"""  const ligneBouclier = (e) => {
    const etat = etatBouclier(e, now);""",
u'fabrique d une ligne de bouclier')

js = rempl(js,
u"""        </div>
        ${bouton}
      </div>`;
  }).join('');
}""",
u"""        </div>
        ${bouton}
      </div>`;
  };
  afficherParLots(grid, protegeables, ligneBouclier,
                  [boucliersTout, rechercheB, protegeables.length].join('|'));
}""",
u'appel a afficherParLots pour les boucliers')

# ---------------------------------------------------------------------------
#  3. La Bourse : mes communes
# ---------------------------------------------------------------------------
js = rempl(js,
u"""  grid.innerHTML = entries.map(entry => {
    const listedPrice = myListings.get(entry.code);""",
u"""  const ligneVente = (entry) => {
    const listedPrice = myListings.get(entry.code);""",
u'fabrique d une ligne de vente')

js = rempl(js,
u"""          <span class="ligne-detail">${DEPT_NAMES[entry.dept] ? DEPT_NAMES[entry.dept] + ' ' : ''}(${entry.dept}), ${entry.tier.label.toLowerCase()}</span>
        </div>
        ${actions}
      </div>`;
  }).join('');
}""",
u"""          <span class="ligne-detail">${DEPT_NAMES[entry.dept] ? DEPT_NAMES[entry.dept] + ' ' : ''}(${entry.dept}), ${entry.tier.label.toLowerCase()}</span>
        </div>
        ${actions}
      </div>`;
  };
  afficherParLots(grid, entries, ligneVente,
                  [sellFilterTier, searchText, entries.length].join('|'));
}""",
u'appel a afficherParLots pour mes communes en vente')

# ---------------------------------------------------------------------------
#  4. La Bourse : les annonces
# ---------------------------------------------------------------------------
js = rempl(js,
u"""  grid.innerHTML = market.map(a => {
    const c = a.communes;""",
u"""  const ligneAnnonce = (a) => {
    const c = a.communes;""",
u'fabrique d une ligne d annonce')

js = rempl(js,
u"""        <span class="ligne-prix">${Number(a.prix).toLocaleString('fr-FR')}<small>pts</small></span>
        <div class="ligne-actions">${action}</div>
      </div>`;
  }).join('');
}""",
u"""        <span class="ligne-prix">${Number(a.prix).toLocaleString('fr-FR')}<small>pts</small></span>
        <div class="ligne-actions">${action}</div>
      </div>`;
  };
  afficherParLots(grid, market, ligneAnnonce, 'marche|' + market.length);
}""",
u'appel a afficherParLots pour les annonces')

ecrire('app.js', js)
print(u'patch49 applique.')
