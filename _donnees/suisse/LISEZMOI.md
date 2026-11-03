# Suisse : données préparées pour le jeu (saison 3)

Sources : swisstopo (swissBOUNDARIES3D 2026-01 pour les communes et la population,
swissTLMRegio 2026 pour les lacs), usage commercial autorisé, **« © swisstopo » à afficher
dans le jeu** ; Wikidata (CC0) pour les noms français, les articles et les photos.
Les fichiers bruts sont dans `brut/` (ignoré par git), recréés par `telecharger-suisse.py`.

- `jeu/communes-suisse.csv` : 2 110 communes. Code « CH » + numéro OFS, nom (français pour
  15 villes connues : ≥ 30 000 hab. ou chef-lieu ; officiel sans le suffixe « (GE) » ailleurs),
  canton (département du jeu), population swisstopo, position (point intérieur de la commune,
  lacs exclus), rareté avec les seuils de la saison 2 (30 000 / 8 000 / 2 300 / 450).
- `jeu/contours/XX.json` : contours des communes, un fichier par canton, même format que
  `contours/74.json` (lacs découpés, simplification qui garde les limites communes).
- `jeu/cantons.json` : contours des cantons (vue de loin), même format que `contours-departements.json`.
- `jeu/lacs.json` : lacs de plus de 0,3 km² qui touchent la Suisse (Léman, Constance, Majeur, Lugano en entier).
- `jeu/suisse-contour.json` : la terre suisse (lacs exclus) ; `jeu/suisse-frontiere.json` : la frontière nationale (passe au milieu des lacs).
- `prep/` : les scripts qui ont produit ces fichiers (chemins de l'espace de travail de Claude).

Rien de tout ça n'est encore lu par le jeu.
