# -*- coding: utf-8 -*-
u"""
patch52 — Un numero de version sur l'adresse des photos.

LE PROBLEME
  Les images sont stockees avec le bon reglage de cache (30 jours) : une
  lecture a la source le confirme. Mais Cloudflare, qui sert les images aux
  joueurs, garde une entree datant d'avant la correction. Il demande a
  Supabase « elle a change ? », s'entend repondre non, et ressert sa copie
  AVEC LES EN-TETES QU'IL AVAIT STOCKES — les anciens, en no-cache.

  Resultat : chaque image redemande une verification au serveur a chaque
  affichage. Jusqu'a 900 allers-retours pour une grosse collection.

LA CORRECTION
  On ajoute un numero de version a l'adresse. Pour Cloudflare c'est une
  adresse qu'il n'a jamais vue : il va la chercher a la source, recupere le
  bon en-tete et la garde trente jours. C'est le procede que maj-version.py
  applique deja a app.js et style.css.

  Aucun reimport. Les fichiers ne bougent pas, seule l'adresse change.

SI ON DOIT REMPLACER UNE PHOTO UN JOUR
  Monter ce numero rend d'un coup toutes les adresses neuves. C'est l'outil
  a utiliser si une mauvaise image reste coincee quelque part.
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

js = rempl(js,
u"""// Le bucket « communes » est public : l'adresse se compose a partir de
// celle du projet, que le client connait deja.
const urlPhoto = (fichier) => fichier
  ? SUPABASE_URL + '/storage/v1/object/public/communes/' + fichier
  : null;""",
u"""// Le bucket « communes » est public : l'adresse se compose a partir de
// celle du projet, que le client connait deja.
//
// Le ?v= n'est pas decoratif. Les images sont stockees avec un cache de 30
// jours, mais Cloudflare garde des entrees datant d'avant ce reglage : il
// revalide et ressert ses anciens en-tetes en no-cache, ce qui oblige le
// navigateur a redemander chaque image a chaque affichage. Un numero de
// version rend l'adresse neuve a ses yeux : il va la chercher a la source
// et garde la bonne reponse. Meme procede que app.js?v= dans index.html.
// Monter ce numero rafraichit toutes les photos d'un coup, le jour ou on
// remplacera une mauvaise image.
const PHOTOS_V = '2';
const urlPhoto = (fichier) => fichier
  ? SUPABASE_URL + '/storage/v1/object/public/communes/' + fichier + '?v=' + PHOTOS_V
  : null;""",
u'numero de version sur l adresse des photos')

ecrire('app.js', js)
print(u'patch52 applique.')
