# -*- coding: utf-8 -*-
u"""
patch139 — suite du patch138 : les échanges d'un joueur visibles sur sa
fiche (clic sur son pseudo), en pastille « 🤝 N échanges » dans « En
chiffres ». Même source : echanges_joueur() (_sql/echanges-profil.sql).
Sans la fonction, pas de pastille.
"""
import io, os
ICI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ICI) if os.path.basename(ICI) == '_patchs' else ICI
def lire(n):
    with io.open(os.path.join(BASE, n), encoding='utf-8') as f: return f.read()
def ecrire(n, s):
    with io.open(os.path.join(BASE, n), 'w', encoding='utf-8') as f: f.write(s)
def rempl(src, avant, apres, etiquette, n_attendu=1):
    n = src.count(avant)
    assert n == n_attendu, u'%s : %d occurrences (attendu %d)' % (etiquette, n, n_attendu)
    return src.replace(avant, apres)
js = lire('app.js')
assert 'chargerStatEchanges' in js, u'appliquer patch138 avant'
assert 'pastille echanges' not in js, u'patch139 deja applique'

js = rempl(js, u"""  const [{ data, error }, vitrine, badges] = await Promise.all([
    sb.rpc('profil_joueur', { p_joueur: joueurId }), chargerVitrine(joueurId), chargerBadges(joueurId)]);""",
u"""  const [{ data, error }, vitrine, badges, echanges] = await Promise.all([
    sb.rpc('profil_joueur', { p_joueur: joueurId }), chargerVitrine(joueurId), chargerBadges(joueurId),
    chargerStatEchanges(joueurId)]);""", u'chargement fiche')

js = rempl(js, u"""  profilEnCours.badges = badges;
  rendreProfil();""", u"""  profilEnCours.badges = badges;
  profilEnCours.echanges = echanges;
  rendreProfil();""", u'stockage fiche')

js = rempl(js, u"""          <span class="pr-puce">🛡️ ${nb(p.communes_perdues)} perdue${p.communes_perdues > 1 ? 's' : ''} au combat</span>
""", u"""          <span class="pr-puce">🛡️ ${nb(p.communes_perdues)} perdue${p.communes_perdues > 1 ? 's' : ''} au combat</span>
          ${p.echanges ? `<span class="pr-puce">🤝 ${nb(p.echanges.echanges)} échange${Number(p.echanges.echanges) > 1 ? 's' : ''}</span>` : ''}<!-- patch139 : pastille echanges -->
""", u'pastille')

ecrire('app.js', js)
print(u'patch139 applique')
