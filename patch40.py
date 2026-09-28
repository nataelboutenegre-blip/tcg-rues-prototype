# -*- coding: utf-8 -*-
"""
patch40 — Le fond noir de certaines cartes du defile.

CAUSE
  miniArtSvg() fabrique l'identifiant de son degrade a partir du texte
  qu'on lui donne :

      const id = 'mg' + code;
      ... <rect fill="url(#mgL'Abergement01)"/>

  Partout ailleurs dans le jeu on lui passe le CODE INSEE (« 16186 ») :
  des chiffres, donc un identifiant toujours valide. Le defile du contrat
  etait le seul endroit a lui passer le NOM de la commune, parce que
  contrat_defile() ne renvoie pas le code. Des qu'un nom contient une
  apostrophe ou une espace — « L'Abergement », « Aix en Othe » —
  url(#...) ne se resout plus, le rectangle n'a plus de remplissage, et
  le fond apparait noir. Les noms a trait d'union ou a accent passaient,
  d'ou le « certaines cartes ».

CORRECTIF
  1. miniArtSvg derive son identifiant d'un hachage. Quoi qu'on lui
     passe, l'identifiant est valide. La panne ne peut plus revenir,
     meme si un futur appel lui donne autre chose qu'un code.
  2. carteDefile accepte une graine : le code INSEE quand on l'a. La
     carte gagnante a desormais le MEME dessin dans le defile et dans la
     Collection — ce n'etait pas le cas, deux dessins pour une meme
     commune.
  3. Le decor utilise le code si contrat_defile le renvoie (voir
     _sql/contrat-defile-code.sql), et retombe sur le nom sinon : le
     correctif marche avant comme apres le passage du SQL.
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

# --- 1. un identifiant toujours valide -------------------------------------
js = rempl(js,
u"""  const [clair, fonce] = TEINTES_CARTE[tierId];
  const id = 'mg' + code;""",
u"""  const [clair, fonce] = TEINTES_CARTE[tierId];
  // L'identifiant vient d'un hachage, jamais du texte recu : une
  // apostrophe ou une espace dans un nom de commune (« L'Abergement »,
  // « Aix en Othe ») rendait url(#...) non resoluble, et la carte
  // s'affichait sur fond noir.
  const id = 'mg' + hashTexte(cle).toString(36);""",
u'identifiant du degrade')

# --- 2. une graine explicite pour le defile --------------------------------
js = rempl(js,
u"""function carteDefile(tier, nom, dept, pop, gagnante){
  const t = TIERS.find(x => x.id === tier) || TIERS[0];
  return `<div class="mini ${tier}${gagnante ? ' gagnante' : ''}">
    <div class="mini-int">
      <div class="mini-art">${miniArtSvg(nom + dept, tier)}<span class="mini-dept">${echapperTexte(dept || '')}</span></div>""",
u"""// graine : le code INSEE quand on l'a, pour que la carte gagnante ait le
// meme dessin ici et dans la Collection. Sinon le nom, faute de mieux.
function carteDefile(tier, nom, dept, pop, gagnante, graine){
  const t = TIERS.find(x => x.id === tier) || TIERS[0];
  return `<div class="mini ${tier}${gagnante ? ' gagnante' : ''}">
    <div class="mini-int">
      <div class="mini-art">${miniArtSvg(graine || (nom + dept), tier)}<span class="mini-dept">${echapperTexte(dept || '')}</span></div>""",
u'graine de carteDefile')

# --- 3. les trois appels passent la graine ---------------------------------
js = rempl(js,
u"""    rail.innerHTML = carteDefile(c.vers, carte.nom, carte.departement, carte.population, true);""",
u"""    rail.innerHTML = carteDefile(c.vers, carte.nom, carte.departement, carte.population, true, carte.code);""",
u'graine du raccourci direct')

js = rempl(js,
u"""      if(i === CT_IDX){
        html += carteDefile(c.vers, carte.nom, carte.departement, carte.population, true);
      } else {
        const d = decor[i % decor.length];
        html += carteDefile(c.vers, d.nom, d.departement, d.population, false);
      }""",
u"""      if(i === CT_IDX){
        html += carteDefile(c.vers, carte.nom, carte.departement, carte.population, true, carte.code);
      } else {
        const d = decor[i % decor.length];
        html += carteDefile(c.vers, d.nom, d.departement, d.population, false, d.code);
      }""",
u'graine des cartes du defile')

ecrire('app.js', js)

print(u'patch40 applique.')
