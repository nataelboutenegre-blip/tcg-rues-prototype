# -*- coding: utf-8 -*-
u"""
patch57 — Une commune deja promise ne reste plus proposable (signale par Nataël).

CE QU'IL VOYAIT
  On lance un echange, on valide la proposition, et la commune qu'on vient
  d'engager reste affichee dans la liste de ses communes disponibles a
  l'echange. On peut donc la proposer une seconde fois a quelqu'un d'autre.

CE QUE C'ETAIT
  Reproduit sur le banc : une proposition en attente sur Nantes, et Nantes
  figure toujours parmi les 250 communes offertes.

  Le serveur, lui, est correct : cibles_echange ecarte deja toute commune
  engagee dans un echange en attente, des deux cotes, et une commune vendue
  ou conquise entre-temps fait annuler la proposition. Le defaut est
  uniquement a l'affichage, dans la liste de MES communes : elle ecartait
  celles mises en vente a la Bourse, mais pas celles deja promises.

CE QUE JE FAIS
  Rien de plus a demander au serveur : mes_echanges renvoie deja le code de
  la commune que je donne, pour les propositions envoyees comme pour celles
  recues. Il suffit de s'en servir.

  Une commune engagee disparait donc de la liste, comme disparait deja une
  commune mise en vente. Et si toutes celles d'un palier sont engagees, le
  message le dit au lieu d'affirmer qu'on n'en a aucune.

CE QUE JE NE FAIS PAS, ET POURQUOI
  Le meme trou existe a la Bourse et au Contrat : rien n'empeche de mettre
  en vente ou de sacrifier une commune deja promise. Les consequences sont
  propres — la proposition s'annule d'elle-meme a la consultation suivante,
  c'est le travail de echanges-caducs.sql — donc personne ne perd rien.

  Le boucher serait de charger les echanges en cours au demarrage de chaque
  session, pour une situation rare. Je prefere le dire plutot que de payer
  une requete a tout le monde sans que tu l'aies demande.
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
u"""  const miennes = [...collectionMap.values()]
    .filter(c => c.tier && c.tier.id === echangeTier)
    .filter(c => !(c.bouclierJusqua > maintenant))
    .filter(c => !myListings.has(c.code))
    .filter(c => correspondRecherche(c.nom, c.dept, rechercheM))
    .sort((a, b) => a.nom.localeCompare(b.nom, 'fr'));

  if(miennes.length === 0){
    zone.innerHTML = rechercheM
      ? '<p class="collection-empty">Aucune de tes communes ne correspond à cette recherche.</p>'
      : '<p class="collection-empty">Tu n\\'as aucune commune échangeable de cette rareté.</p>';""",
u"""  // Une commune deja engagee dans une proposition en attente ne peut pas etre
  // promise une seconde fois. Le serveur le sait et la refuse, mais elle
  // restait affichee comme disponible. mes_echanges renvoie deja le code de
  // celle que je donne, pour les propositions envoyees comme pour les recues :
  // il n'y a rien de plus a lui demander.
  const engagees = new Set((echangesEnCours || []).map(e => e.je_donne_code));

  const duPalier = [...collectionMap.values()]
    .filter(c => c.tier && c.tier.id === echangeTier)
    .filter(c => !(c.bouclierJusqua > maintenant))
    .filter(c => !myListings.has(c.code));
  const miennes = duPalier
    .filter(c => !engagees.has(c.code))
    .filter(c => correspondRecherche(c.nom, c.dept, rechercheM))
    .sort((a, b) => a.nom.localeCompare(b.nom, 'fr'));

  if(miennes.length === 0){
    // dire « tu n'en as aucune » alors qu'elles sont toutes promises, c'est
    // envoyer le joueur chercher une erreur qui n'existe pas
    const toutesPromises = !rechercheM && duPalier.length > 0;
    zone.innerHTML = rechercheM
      ? '<p class="collection-empty">Aucune de tes communes ne correspond à cette recherche.</p>'
      : (toutesPromises
         ? '<p class="collection-empty">Toutes tes communes de cette rareté sont déjà engagées dans une proposition.</p>'
         : '<p class="collection-empty">Tu n\\'as aucune commune échangeable de cette rareté.</p>');""",
u'les communes deja promises disparaissent de la liste')

ecrire('app.js', js)
print(u'patch57 applique.')
