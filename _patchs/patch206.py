# -*- coding: utf-8 -*-
u"""
patch206 — quand un joueur demande l'annulation d'un achat (livraison
différée), le jeu appelle la fonction « prevenir-retractation » : Nataël reçoit
un e-mail sur contact@terrafront.fr avec le lien du paiement à rembourser.
Un échec de l'appel ne gêne pas le joueur (sa demande est déjà enregistrée).
SQL : _boutique-euros/17-prevenir-retractation.sql ; fonction Edge à déployer.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)

js = lire('app.js')
assert 'patch206' not in js
avant = u"""  if(error){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible(error.message) }); r.disabled = false; return; }
  bqeCommandes = data || [];
  renderBoutiqueEuros();"""
apres = u"""  if(error){ notifier({ type: 'erreur', titre: 'Impossible', texte: messageLisible(error.message) }); r.disabled = false; return; }
  // patch206 : prévenir Nataël par e-mail (la demande est déjà enregistrée, un échec ne bloque rien)
  try{ sb.functions.invoke('prevenir-retractation', { body: {} }).catch(() => {}); }catch(err){}
  bqeCommandes = data || [];
  renderBoutiqueEuros();"""
assert js.count(avant) == 1
ecrire('app.js', js.replace(avant, apres))
print(u'patch206 applique. Lancer : python3 maj-version.py')
