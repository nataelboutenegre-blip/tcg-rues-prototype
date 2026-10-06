# -*- coding: utf-8 -*-
u"""
patch75 — Mise en règle du site (6 octobre).

1. Polices servies depuis le site (dossier fonts/) : plus d'appel aux
   serveurs de Google, donc plus d'adresse IP envoyée à Google. Mêmes
   graisses, mêmes découpages : rendu identique.
2. Trois pages : mentions-legales.html, confidentialite.html, cgu.html
   (fabriquées par _patchs/pages-legales.py, style dans pages.css).
   Liens en bas de la page d'accueil, dans le menu ordinateur et en bas
   du Profil.
3. Inscription : une ligne sous « Créer mon compte » renvoie aux
   conditions et à la confidentialité, avec l'âge minimum (15 ans).
4. Profil : bouton « Supprimer mon compte ». Fenêtre de confirmation, le
   joueur retape son pseudo. Serveur : supprimer_mon_compte()
   (_sql/suppression-1-compte.sql, à passer AVANT le push).
5. Radar : le résumé d'un duel contre un joueur supprimé affiche
   « un joueur » au lieu d'un nom vide.
"""
import io, os, subprocess, sys

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

LIENS = (u'<a href="mentions-legales.html">Mentions légales</a> · '
         u'<a href="confidentialite.html">Confidentialité</a> · '
         u'<a href="cgu.html">Conditions d\'utilisation</a>')

# ---------------------------------------------------------------------
# index.html
# ---------------------------------------------------------------------
h = lire('index.html')
h = rempl(h,
u'''<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700;800;900&family=Instrument+Sans:wght@400;500;600&display=swap" rel="stylesheet">''',
u'''<link rel="stylesheet" href="fonts/polices.css">''', 'polices')
h = rempl(h,
u'''      <span>TerraFront — un jeu indépendant, fait en France.</span>
      <a href="https://discord.gg/T6suSy6xa7" target="_blank" rel="noopener">Rejoindre le Discord</a>
    </div>''',
u'''      <span>TerraFront — un jeu indépendant, fait en France.</span>
      <a href="https://discord.gg/T6suSy6xa7" target="_blank" rel="noopener">Rejoindre le Discord</a>
      <span class="lp-legal">%s</span>
    </div>''' % LIENS, 'pied accueil')
h = rempl(h,
u'''      <button class="auth-valider" id="signupBtn" hidden>Créer mon compte</button>''',
u'''      <button class="auth-valider" id="signupBtn" hidden>Créer mon compte</button>
      <p class="auth-legal" id="authLegal" hidden>En créant un compte, tu acceptes les <a href="cgu.html" target="_blank" rel="noopener">conditions d'utilisation</a> et la <a href="confidentialite.html" target="_blank" rel="noopener">politique de confidentialité</a>, et tu confirmes avoir 15 ans ou l'accord d'un parent.</p>''', 'inscription')
h = rempl(h,
u'''      <span id="whoami"></span>
      <button class="link-btn" id="logoutBtn">Se déconnecter</button>
    </div>''',
u'''      <span id="whoami"></span>
      <button class="link-btn" id="logoutBtn">Se déconnecter</button>
      <p class="liens-legaux"><a href="mentions-legales.html">Mentions légales</a> · <a href="confidentialite.html">Confidentialité</a> · <a href="cgu.html">CGU</a></p>
    </div>''', 'menu ordinateur')
ecrire('index.html', h)

# ---------------------------------------------------------------------
# app.js
# ---------------------------------------------------------------------
js = lire('app.js')
# la ligne d'inscription suit le bouton « Créer mon compte »
js = rempl(js,
u'''  document.getElementById('signupBtn').hidden = !inscription;
  document.getElementById('authPassword')''',
u'''  document.getElementById('signupBtn').hidden = !inscription;
  document.getElementById('authLegal').hidden = !inscription;
  document.getElementById('authPassword')''', 'modeAuth')
js = rempl(js,
u'''    q('loginBtn').hidden = true;
    q('signupBtn').hidden = true;
    const premier''',
u'''    q('loginBtn').hidden = true;
    q('signupBtn').hidden = true;
    q('authLegal').hidden = true;
    const premier''', 'ecran auth')

# Profil : bloc « compte » en bas
js = rempl(js,
u'''    <div class="pf-boutons">
      <button class="pr-btn" data-pf="editer">Changer d'avatar ou de pseudo</button>
    </div>`;
}''',
u'''    <div class="pf-boutons">
      <button class="pr-btn" data-pf="editer">Changer d'avatar ou de pseudo</button>
    </div>
    <div class="pf-compte">
      <p class="pf-legal">%s</p>
      <button type="button" class="pf-suppr" data-pf="supprimer">Supprimer mon compte</button>
    </div>`;
}''' % LIENS.replace(u"'", u"\\'"), 'profil bas')
js = rempl(js,
u'''document.getElementById('pfCorps').addEventListener('click', (e) => {
  if(e.target.closest('[data-pf="editer"]')) ouvrirProfil(window.__monId || null);
});''',
u'''document.getElementById('pfCorps').addEventListener('click', (e) => {
  if(e.target.closest('[data-pf="editer"]')) ouvrirProfil(window.__monId || null);
  if(e.target.closest('[data-pf="supprimer"]')) ouvrirSuppressionCompte();
});

// Suppression de compte (patch75) : le joueur retape son pseudo, le serveur
// verifie aussi. Tout est fait en une transaction (supprimer_mon_compte).
function ouvrirSuppressionCompte(){
  const p = profilPanneau || {};
  const pseudo = String(p.pseudo || '');
  const n = Number(p.communes || 0);
  const fermer = ouvrirFenetre(`
    <form class="fenetre suppr" role="dialog" aria-modal="true" aria-labelledby="supprTitre" novalidate>
      <h2 id="supprTitre">Supprimer ton compte ?</h2>
      <p class="suppr-alerte">C'est définitif : rien ne pourra être récupéré.</p>
      <ul class="suppr-liste">
        <li>${n > 0 ? `Tes <b>${n.toLocaleString('fr-FR')} commune${n > 1 ? 's' : ''}</b> retournent dans les paquets.` : 'Tes communes retournent dans les paquets.'}</li>
        <li>Ton e-mail, ton pseudo, tes amis, tes échanges et leurs messages sont effacés.</li>
        <li>Le journal et les classements passés gardent les parties jouées, sous « un joueur ».</li>
      </ul>
      <label class="suppr-champ"><span>Pour confirmer, écris ton pseudo : <b>${echapperTexte(pseudo)}</b></span>
        <input type="text" id="supprPseudo" autocomplete="off" autocapitalize="off" spellcheck="false"></label>
      <p class="prix-erreur" id="supprErreur" role="alert"></p>
      <div class="prix-boutons">
        <button type="button" class="open-btn secondary" data-annuler>Annuler</button>
        <button type="submit" class="open-btn suppr-ok" disabled>Supprimer définitivement</button>
      </div>
    </form>`);
  const form = document.querySelector('#fenetre form.suppr');
  const champ = document.getElementById('supprPseudo');
  const ok = form.querySelector('.suppr-ok');
  const erreur = document.getElementById('supprErreur');
  const pareil = () => champ.value.trim().toLowerCase() === pseudo.trim().toLowerCase() && pseudo !== '';
  champ.addEventListener('input', () => { ok.disabled = !pareil(); erreur.textContent = ''; });
  form.querySelector('[data-annuler]').addEventListener('click', () => fermer(null));
  champ.focus();
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if(!pareil()) return;
    ok.disabled = true; ok.textContent = 'Suppression…';
    const { error } = await sb.rpc('supprimer_mon_compte', { p_confirmation: champ.value });
    if(error){
      erreur.textContent = messageLisible(error.message);
      ok.textContent = 'Supprimer définitivement'; ok.disabled = !pareil();
      return;
    }
    // le compte n'existe plus : on oublie la session sur cet appareil seulement
    try { await sb.auth.signOut({ scope: 'local' }); } catch(err){}
    form.outerHTML = `<div class="fenetre suppr" role="dialog" aria-modal="true">
      <h2>Compte supprimé</h2>
      <p>Tes données ont été effacées. Merci d'avoir joué à TerraFront.</p>
      <div class="prix-boutons"><button type="button" class="open-btn" id="supprFin">Fermer</button></div></div>`;
    document.getElementById('supprFin').addEventListener('click', () => location.replace('./'));
  });
}''', 'profil suppression')

# Radar : adversaire supprimé
js = rempl(js, u"const nomAdv = adv ? echapperTexte(adv.pseudo) : '';",
               u"const nomAdv = adv ? echapperTexte(adv.pseudo || 'un joueur') : '';", 'radar nom 1')
js = rempl(js, u"contre ${adv.pseudo} : ${fmt(p.total_km)} km",
               u"contre ${adv.pseudo || 'un joueur'} : ${fmt(p.total_km)} km", 'radar partage')
js = rempl(js, u"<span class=\"rd-c-lui\">${echapperTexte(adv.pseudo)} ${dit(m.lui)}</span>",
               u"<span class=\"rd-c-lui\">${echapperTexte(adv.pseudo || 'un joueur')} ${dit(m.lui)}</span>", 'radar focus')
ecrire('app.js', js)

# ---------------------------------------------------------------------
# style.css
# ---------------------------------------------------------------------
css = lire('style.css')
MARQUE = u'/* ---------- Pages légales et suppression de compte (patch75) ---------- */'
assert MARQUE not in css, u'patch75 déjà passé'
css = css.rstrip('\n') + u'\n\n' + MARQUE + u'''
.lp-legal{ flex-basis:100%; font-size:.8rem; }
.lp-legal a{ color: var(--brume); }
.auth-legal{ font-size:.74rem; line-height:1.45; color: var(--brume); text-align:center; margin:8px 2px 0; }
.auth-legal[hidden]{ display:none; }
.auth-legal a{ color: var(--brume); text-decoration:underline; }
.liens-legaux{ font-size:.72rem; line-height:1.5; color: rgba(169,188,212,.75); margin:10px 0 0; }
.liens-legaux a{ color: inherit; text-decoration:none; }
.liens-legaux a:hover{ color:#fff; text-decoration:underline; }
.pf-compte{ margin-top:28px; padding-top:16px; border-top:1px solid rgba(169,188,212,.16);
  display:flex; flex-wrap:wrap; gap:12px 20px; align-items:center; justify-content:space-between; }
.pf-legal{ margin:0; font-size:.8rem; color: var(--brume); }
.pf-legal a{ color: var(--brume); }
.pf-legal a:hover{ color:#fff; }
.pf-suppr{ font:inherit; font-size:.84rem; font-weight:600; color:#FF8A8D; background:transparent;
  border:1px solid rgba(229,72,77,.45); border-radius:10px; padding:8px 14px; cursor:pointer; }
.pf-suppr:hover{ background: rgba(229,72,77,.12); border-color: rgba(229,72,77,.8); }
.fenetre.suppr{ width:min(430px, 100%); text-align:left; }
.fenetre.suppr h2{ font-family: var(--titre); font-weight:900; font-size:1.9rem; text-transform:uppercase; margin:0 0 6px; color:#FF8A8D; }
.suppr-alerte{ margin:0 0 12px; font-weight:600; color:#fff; }
.suppr-liste{ margin:0 0 16px; padding-left:18px; color: var(--brume); font-size:.9rem; line-height:1.5; }
.suppr-liste li{ margin:4px 0; }
.suppr-liste b{ color:#fff; }
.suppr-champ{ display:flex; flex-direction:column; gap:6px; font-size:.86rem; color: var(--brume); }
.suppr-champ b{ color:#fff; }
.suppr-champ input{ font:inherit; font-size:1rem; color:#fff; background: var(--nuit); border:1px solid rgba(169,188,212,.3);
  border-radius:10px; padding:10px 12px; }
.suppr-champ input:focus{ outline:2px solid #E5484D; outline-offset:1px; }
.fenetre.suppr .open-btn.suppr-ok{ background:#E5484D; color:#fff; }
.fenetre.suppr .open-btn.suppr-ok:disabled{ opacity:.4; cursor:not-allowed; }
'''
ecrire('style.css', css)

# les trois pages
subprocess.check_call([sys.executable, os.path.join(ICI, 'pages-legales.py')])
print(u'patch75 : OK')
