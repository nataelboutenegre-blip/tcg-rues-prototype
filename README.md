# TCG Rues de France — prototype

Prototype de test pour la mécanique de tirage de cartes-rues pondérée sur les vraies données de la Base Adresse Nationale (BAN).

## Structure
- `index.html` — structure de la page
- `style.css` — mise en forme
- `app.js` — logique (tirage pondéré, paliers de rareté, collection)
- `data/communes.json` — 34 888 communes (population, nombre de voies, coordonnées)

## Lancer en local
Ouvrir `index.html` via un serveur local (ex. `python3 -m http.server` dans ce dossier), pas en double-clic direct — le fetch de `data/communes.json` ne fonctionne pas en `file://`.

## Sur GitHub Pages
Une fois le dépôt poussé sur GitHub, activer GitHub Pages (Settings > Pages > Deploy from branch > main) pour avoir un lien direct.
