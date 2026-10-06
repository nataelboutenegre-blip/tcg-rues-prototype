# -*- coding: utf-8 -*-
u"""
patch77 — Radar : moins de banlieue parisienne à l'entraînement.

Même tirage que le Radar classé (_sql/radar-4-tirage.sql) : 5 zones
différentes, pondérées par la racine carrée de leur nombre de communes,
puis une commune au hasard dans chaque zone.
- Grandes villes / Toutes : une zone par département, l'Île-de-France
  compte pour une seule zone.
- Une région : une zone par département de la région. Quand la région a
  moins de 5 départements (Corse, Bretagne), on repart sur les zones
  restantes, sans jamais reprendre une commune déjà tirée.
"""
import io, os

ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI

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
js = rempl(js,
u'''  // 5 communes au hasard, en évitant celles de la partie précédente quand c'est possible
  const dispo = pool.length >= ENTR_MANCHES * 3 ? pool.filter(c => !entr.derniers.includes(c.nom + c.dept)) : pool.slice();
  const choix = [];
  while(choix.length < ENTR_MANCHES && dispo.length){ choix.push(dispo.splice(Math.floor(Math.random() * dispo.length), 1)[0]); }''',
u'''  // 5 communes, en évitant celles de la partie précédente quand c'est possible
  const dispo = pool.length >= ENTR_MANCHES * 3 ? pool.filter(c => !entr.derniers.includes(c.nom + c.dept)) : pool.slice();
  const choix = entrTirer(dispo, entr.niveau === 'region');''', 'tirage')
js = rempl(js,
u'''function entrManche(){''',
u'''// Le tirage du Radar classé (radar-4-tirage.sql) : des zones différentes,
// pondérées par la racine carrée de leur taille, puis une commune par zone.
// Hors mode région, l'Île-de-France ne compte que pour une zone.
const ENTR_IDF = new Set(ENTR_REGIONS['Île-de-France']);
function entrTirer(dispo, parDepartement){
  const zoneDe = (c) => (!parDepartement && ENTR_IDF.has(c.dept)) ? 'IDF' : c.dept;
  const zones = new Map();
  for(const c of dispo){ const z = zoneDe(c); if(!zones.has(z)) zones.set(z, []); zones.get(z).push(c); }
  const choix = [];
  while(choix.length < ENTR_MANCHES && zones.size){
    // une manche de tirage : chaque zone au plus une fois
    const tour = [...zones.keys()];
    while(choix.length < ENTR_MANCHES && tour.length){
      const poids = tour.map(z => Math.sqrt(zones.get(z).length));
      let r = Math.random() * poids.reduce((a, b) => a + b, 0), i = 0;
      while(i < tour.length - 1 && r >= poids[i]){ r -= poids[i]; i++; }
      const z = tour.splice(i, 1)[0], liste = zones.get(z);
      choix.push(liste.splice(Math.floor(Math.random() * liste.length), 1)[0]);
      if(!liste.length) zones.delete(z);
    }
  }
  // l'ordre de jeu ne trahit pas l'ordre du tirage
  for(let i = choix.length - 1; i > 0; i--){ const j = Math.floor(Math.random() * (i + 1)); [choix[i], choix[j]] = [choix[j], choix[i]]; }
  return choix;
}

function entrManche(){''', 'entrTirer')
ecrire('app.js', js)
print(u'patch77 : OK')
