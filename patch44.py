# -*- coding: utf-8 -*-
"""
patch44 — L'onglet Profil, les statistiques et les niveaux.

CE QUI EXISTAIT
  Le profil n'etait qu'une fenetre modale, atteignable depuis le menu
  « Plus » sur telephone et depuis nulle part sur ordinateur.

CE QUE FAIT CE CORRECTIF
  1. Un vrai onglet Profil, avec son panneau. Sur telephone il passe
     automatiquement dans « Plus » : il suffit de l'ajouter a
     ONGLETS_MENU, le mecanisme pose lundi s'occupe du reste. L'entree
     « Mon profil » ecrite en dur dans le menu disparait, sinon elle y
     figurerait deux fois.
  2. Le niveau, en anneau autour de l'avatar. Six grades de dix niveaux,
     aux couleurs des raretes. L'anneau se decoupe en dix segments : un
     par niveau du grade, on voit sa progression sans lire un chiffre.
  3. Les statistiques : attaque, defense, assiduite, cartes tirees.
     Toutes viennent du journal et de l'historique, donc avec
     l'anteriorite complete.

  La fenetre des AUTRES joueurs reste une fenetre — on veut les consulter
  sans quitter ce qu'on fait — mais elle gagne le meme anneau. Le niveau
  est un statut : il est fait pour etre vu.

  Le panneau et la fenetre partagent le meme corps de statistiques, pour
  ne pas se retrouver avec deux rendus qui divergent.

DEPEND DE _sql/niveaux.sql. Sans lui, profil_joueur ne renvoie ni niveau
ni compteurs : le panneau affiche alors la collection seule, sans anneau
ni blocs de combat, au lieu de montrer des trous.
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


# ===========================================================================
#  index.html
# ===========================================================================
html = lire('index.html')

html = rempl(html,
u"""      <div class="tab" data-tab="succes">""",
u"""      <div class="tab" data-tab="profil">
        <div class="icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="8" r="3.6"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/>
          </svg>
        </div>
        Profil
      </div>

      <div class="tab" data-tab="succes">""",
u'onglet Profil dans la barre')

html = rempl(html,
u"""    <section class="tab-panel" id="panel-regles">""",
u"""    <section class="tab-panel" id="panel-profil">
      <h1>Profil</h1>
      <div class="sub">Ton niveau monte avec ce que tu fais : conquérir, défendre, signer des contrats, revenir chaque jour. Il ne redescend jamais, même quand on te prend des communes.</div>
      <div id="pfCorps"></div>
      <p class="collection-empty" id="pfVide" hidden>Chargement…</p>
    </section>

    <section class="tab-panel" id="panel-regles">""",
u'panneau Profil')

ecrire('index.html', html)


# ===========================================================================
#  style.css
# ===========================================================================
css = lire('style.css')

css = rempl(css,
u"""  .ct-avert{ font-size:0.75rem; color:#7F91AB; text-align:center; margin:9px 0 0; line-height:1.5; }""",
u"""  /* ---------- Le panneau Profil ---------- */
  #panel-profil #pfCorps{ width:100%; }

  /* l'anneau de niveau : dix segments, un par niveau du grade */
  .niv{ position:relative; flex-shrink:0; }
  .niv svg{ position:absolute; inset:0; transform:rotate(-90deg); }
  .niv .niv-fond{ fill:none; stroke:rgba(169,188,212,0.16); }
  .niv .niv-seg{ fill:none; stroke-linecap:round; }
  .niv-av{
    position:absolute; border-radius:50%; display:grid; place-items:center;
    background: var(--nuit); box-shadow:0 6px 18px rgba(0,0,0,0.45);
  }
  .niv-n{
    position:absolute; left:50%; bottom:-7px; transform:translateX(-50%);
    font-family: var(--titre); font-weight:900; line-height:1;
    padding:3px 9px; border-radius:9px; color: var(--encre);
    box-shadow:0 3px 8px rgba(0,0,0,0.45); white-space:nowrap;
  }

  /* dans la fenetre, l'anneau remplace .pr-avatar qui etait centre par
     sa marge auto : il faut le recentrer explicitement */
  .pr-avatar-niv{ display:flex; justify-content:center; margin:0 0 10px; }

  .pf-tete{
    display:flex; gap:24px; align-items:center; background: var(--nuit-2);
    border:1px solid rgba(169,188,212,0.16); border-radius:16px; padding:20px 24px;
  }
  .pf-id{ flex:1; min-width:0; }
  .pf-id h2{ font:900 2.3rem/1 var(--titre); margin:0;
             text-transform:uppercase; letter-spacing:.02em; }
  .pf-rangs{ display:flex; align-items:center; gap:9px; flex-wrap:wrap; margin:8px 0 0; }
  .pf-grade{ font:700 .78rem/1 var(--texte); padding:4px 10px; border-radius:8px; }
  .pf-titre{ font-size:.86rem; color: var(--brume); }
  .pf-titre b{ color: var(--joueur); }
  .pf-place{
    font-family: var(--titre); font-weight:900; font-size:.9rem;
    background: var(--c-legendaire); color: var(--encre); padding:2px 9px; border-radius:7px;
  }
  .pf-xp{ margin-top:13px; }
  .pf-xp-h{ display:flex; justify-content:space-between; gap:12px;
            font-size:.73rem; color:#7F91AB; margin-bottom:5px; }
  .pf-xp-b{ height:7px; border-radius:4px; background:rgba(169,188,212,0.14); overflow:hidden; }
  .pf-xp-b i{ display:block; height:100%; border-radius:4px; transition:width .5s ease; }

  /* align-items:start pour que chaque bloc s'arrete a son contenu : sinon
     le plus haut de la rangee laisse du vide sous les autres */
  .pf-grille{ display:grid; grid-template-columns:repeat(auto-fit,minmax(410px,1fr));
              gap:13px; margin-top:13px; align-items:start; }
  .pf-bloc{ background: var(--nuit-2); border:1px solid rgba(169,188,212,0.16);
            border-radius:14px; padding:15px 17px; }
  .pf-bloc h3{ font:700 .68rem/1 var(--texte); letter-spacing:.1em; text-transform:uppercase;
               color: var(--brume); margin:0 0 13px; }
  .pf-paire{ display:grid; grid-template-columns:1fr 1fr; gap:11px; }
  .pf-ch{ background: var(--nuit); border-radius:10px; padding:10px 12px; }
  .pf-ch b{ display:block; font:900 1.5rem/1 var(--titre); }
  .pf-ch span{ display:block; font-size:.72rem; color:#7F91AB; margin-top:3px; }
  .pf-ch.ok b{ color:#3DD68C; }
  .pf-ch.ko b{ color:#E5484D; }
  .pf-ratio{ font-size:.75rem; color:#7F91AB; margin:11px 0 0; text-align:center; }
  .pf-ratio b{ color:#fff; }
  .pf-ratio:empty{ display:none; }
  .pf-ligne{ display:flex; justify-content:space-between; align-items:baseline; gap:14px;
             padding:7px 0; border-bottom:1px solid rgba(169,188,212,0.09); font-size:.85rem; }
  .pf-ligne:last-child{ border-bottom:0; }
  .pf-ligne span{ color:#9FB0C6; }
  .pf-ligne b{ font-weight:700; white-space:nowrap; }
  .pf-boutons{ display:flex; gap:9px; flex-wrap:wrap; margin-top:13px; }
  .pf-boutons .pr-btn{ width:auto; flex:0 0 auto; }

  @media (max-width: 720px){
    .pf-tete{ flex-direction:column; text-align:center; gap:16px; padding:18px 16px; }
    .pf-id h2{ font-size:1.9rem; }
    .pf-rangs{ justify-content:center; }
    .pf-grille{ grid-template-columns:1fr; }
    .pf-xp-h{ font-size:.7rem; }
  }

  .ct-avert{ font-size:0.75rem; color:#7F91AB; text-align:center; margin:9px 0 0; line-height:1.5; }""",
u'styles du panneau Profil')

ecrire('style.css', css)


# ===========================================================================
#  app.js
# ===========================================================================
js = lire('app.js')

# --- 1. les grades, l'anneau, le corps partage -----------------------------
js = rempl(js,
u"""function avatarHtml(p, couleur){""",
u"""// Six grades de dix niveaux. Les couleurs reprennent celles des raretes :
// c'est la meme echelle de prestige que les cartes, le joueur la connait
// deja. Rallonger l'echelle un jour = ajouter une ligne ici, et changer le
// 60 dans niveau_de() cote base.
const GRADES = [
  { de:  1, a: 10, nom: 'Éclaireur',   couleur: '#7E8BA0' },
  { de: 11, a: 20, nom: 'Arpenteur',   couleur: '#22A06B' },
  { de: 21, a: 30, nom: 'Géomètre',    couleur: '#2F7CF6' },
  { de: 31, a: 40, nom: 'Cartographe', couleur: '#8E7CF6' },
  { de: 41, a: 50, nom: 'Géographe',   couleur: '#E5484D' },
  { de: 51, a: 60, nom: 'Cassini',     couleur: '#F0B429' },
];
const gradeDe = (n) => GRADES.find(g => n >= g.de && n <= g.a) || GRADES[GRADES.length - 1];

// L'anneau : dix segments, un par niveau du grade. On voit ou on en est
// sans avoir a lire le chiffre.
function anneauNiveau(p, taille){
  const niveau = Number(p.niveau || 0);
  const emoji = avatarHtml(p, p.est_moi ? COULEUR_MOI : colorForPlayer(p.id));
  const T = taille || 112, R = T / 2 - 5, ep = Math.max(4, T / 22);
  if(!niveau){
    // niveaux.sql pas encore passe : on montre l'avatar seul, pas un trou
    return `<div class="niv" style="width:${T}px;height:${T}px">
      <div class="niv-av" style="inset:${ep + 2}px;font-size:${T * 0.3}px">${emoji}</div>
    </div>`;
  }
  const g = gradeDe(niveau);
  const pris = niveau - g.de + 1;                  // 1 a 10 dans le grade
  const C = 2 * Math.PI * R, ecart = C * 0.018, seg = C / 10 - ecart;
  const segments = Array.from({ length: 10 }, (_, i) =>
    `<circle class="niv-seg" cx="${T / 2}" cy="${T / 2}" r="${R}" stroke-width="${ep}"
       stroke="${i < pris ? g.couleur : 'transparent'}"
       stroke-dasharray="${seg.toFixed(2)} ${(C - seg).toFixed(2)}"
       stroke-dashoffset="${(-i * C / 10).toFixed(2)}"/>`).join('');
  return `<div class="niv" style="width:${T}px;height:${T}px">
    <svg viewBox="0 0 ${T} ${T}" width="${T}" height="${T}" aria-hidden="true">
      <circle class="niv-fond" cx="${T / 2}" cy="${T / 2}" r="${R}" stroke-width="${ep}"/>
      ${segments}
    </svg>
    <div class="niv-av" style="inset:${ep + 4}px;font-size:${T * 0.29}px">${emoji}</div>
    <div class="niv-n" style="background:${g.couleur};font-size:${T * 0.085}px"
         title="${g.nom} — niveaux ${g.de} à ${g.a}">${niveau}</div>
  </div>`;
}

// Les blocs de statistiques, communs au panneau et a la fenetre : une
// seule source, pour ne pas voir les deux rendus diverger.
function blocsProfil(p){
  const nb = (x) => Number(x || 0).toLocaleString('fr-FR');
  const pct = (a, b) => (a + b) > 0 ? Math.round(100 * a / (a + b)) : null;
  const att = pct(Number(p.conquetes || 0), Number(p.attaques_ratees || 0));
  const def = pct(Number(p.defenses_ok || 0), Number(p.communes_perdues || 0));
  const depuis = p.depuis
    ? new Date(p.depuis).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
    : null;
  const combat = p.niveau ? `
    <div class="pf-bloc">
      <h3>Attaque</h3>
      <div class="pf-paire">
        <div class="pf-ch ok"><b>${nb(p.conquetes)}</b><span>conquêtes réussies</span></div>
        <div class="pf-ch ko"><b>${nb(p.attaques_ratees)}</b><span>attaques repoussées</span></div>
      </div>
      <p class="pf-ratio">${att === null ? '' : `Tu l'emportes <b>${att} %</b> du temps quand tu attaques`}</p>
    </div>
    <div class="pf-bloc">
      <h3>Défense</h3>
      <div class="pf-paire">
        <div class="pf-ch ok"><b>${nb(p.defenses_ok)}</b><span>défenses réussies</span></div>
        <div class="pf-ch ko"><b>${nb(p.communes_perdues)}</b><span>communes perdues</span></div>
      </div>
      <p class="pf-ratio">${def === null ? '' : `Tu tiens <b>${def} %</b> des assauts contre toi`}</p>
    </div>
    <div class="pf-bloc">
      <h3>Assiduité</h3>
      ${depuis ? `<div class="pf-ligne"><span>Membre depuis</span><b>${echapperTexte(depuis)}</b></div>` : ''}
      <div class="pf-ligne"><span>Jours actifs</span><b>${nb(p.jours_actifs)}</b></div>
      <div class="pf-ligne"><span>Série en cours</span><b>${nb(p.serie)} jour${Number(p.serie) > 1 ? 's' : ''}</b></div>
      <div class="pf-ligne"><span>Contrats signés</span><b>${nb(p.contrats)}</b></div>
      <div class="pf-ligne"><span>Cartes tirées</span><b>${nb(p.cartes_tirees)}</b></div>
    </div>` : '';
  return `
    <div class="pf-grille">
      <div class="pf-bloc">
        <h3>La collection</h3>
        <div class="pf-paire">
          <div class="pf-ch"><b style="color:var(--joueur)">${nb(p.communes)}</b><span>communes</span></div>
          <div class="pf-ch"><b>${nb(p.departements)}</b><span>départements</span></div>
          <div class="pf-ch"><b style="color:var(--c-legendaire)">${nb(p.legendaires)}</b><span>légendaires</span></div>
          <div class="pf-ch"><b style="color:var(--c-rare)">${nb(p.rares)}</b><span>rares</span></div>
        </div>
        <p class="pf-ratio"><b>${nb(p.habitants)}</b> habitants sous sa garde</p>
      </div>
      ${combat}
    </div>`;
}

function avatarHtml(p, couleur){""",
u'grades, anneau et blocs')

# --- 2. le panneau ---------------------------------------------------------
js = rempl(js,
u"""let profilEnCours = null;
let fermerProfil = null;""",
u"""let profilEnCours = null;
let fermerProfil = null;
let profilPanneau = null;

async function loadProfilPanneau(){
  const corps = document.getElementById('pfCorps');
  const vide = document.getElementById('pfVide');
  if(!corps) return;
  const id = window.__monId || null;
  if(!id){ if(vide){ vide.hidden = false; vide.textContent = 'Profil indisponible.'; } return; }
  if(!profilPanneau){
    const { data, error } = await sb.rpc('profil_joueur', { p_joueur: id });
    if(error || !data){
      corps.innerHTML = '';
      if(vide){ vide.hidden = false; vide.textContent = "Ton profil n'est pas encore disponible."; }
      return;
    }
    profilPanneau = data;
  }
  if(vide) vide.hidden = true;
  rendreProfilPanneau();
}

function rendreProfilPanneau(){
  const p = profilPanneau, corps = document.getElementById('pfCorps');
  if(!p || !corps) return;
  const nb = (x) => Number(x || 0).toLocaleString('fr-FR');
  const g = p.niveau ? gradeDe(Number(p.niveau)) : null;
  const bas = Number(p.lieues_niveau || 0), haut = Number(p.lieues_suivant || 0);
  const lieues = Number(p.lieues || 0);
  const part = haut > bas ? Math.max(0, Math.min(100, Math.round(100 * (lieues - bas) / (haut - bas)))) : 0;
  const plafond = p.niveau && Number(p.niveau) >= GRADES[GRADES.length - 1].a;

  corps.innerHTML = `
    <div class="pf-tete" style="--joueur:${COULEUR_MOI}">
      ${anneauNiveau(p, 112)}
      <div class="pf-id">
        <h2>${echapperTexte(p.pseudo)}</h2>
        <div class="pf-rangs">
          ${g ? `<span class="pf-grade" style="background:${g.couleur}22;color:${g.couleur}">${g.nom}</span>` : ''}
          <span class="pf-titre"><b>${echapperTexte(titreDepuisDeps(p.deps))}</b></span>
          ${p.rang > 0 ? `<span class="pf-place">${p.rang}${p.rang === 1 ? 'er' : 'e'}</span>` : ''}
        </div>
        ${p.niveau ? `<div class="pf-xp">
          <div class="pf-xp-h">
            <span>Niveau ${p.niveau} · ${nb(lieues)} lieues</span>
            <span>${plafond ? 'Dernier niveau atteint'
                            : `${nb(haut - lieues)} lieues avant le niveau ${Number(p.niveau) + 1}`}</span>
          </div>
          <div class="pf-xp-b"><i style="width:${plafond ? 100 : part}%;background:${g.couleur}"></i></div>
        </div>` : ''}
      </div>
    </div>
    ${blocsProfil(p)}
    <div class="pf-boutons">
      <button class="pr-btn" data-pf="editer">Changer d'avatar ou de pseudo</button>
    </div>`;
}

// Le bouton ouvre la fiche, ou les deux actions existent deja. Les
// dupliquer ici ferait deux chemins pour une meme chose.
document.getElementById('pfCorps').addEventListener('click', (e) => {
  if(e.target.closest('[data-pf="editer"]')) ouvrirProfil(window.__monId || null);
});

// Apres un changement d'avatar ou de pseudo, le panneau doit se resservir
// des nouvelles valeurs plutot que de garder sa copie.
function rafraichirPanneauProfil(){
  profilPanneau = null;
  const panneau = document.getElementById('panel-profil');
  if(panneau && panneau.classList.contains('active')) loadProfilPanneau();
}""",
u'panneau Profil')

js = rempl(js,
u"""    profilEnCours.avatar = emoji;
    rendreProfil();""",
u"""    profilEnCours.avatar = emoji;
    rendreProfil();
    rafraichirPanneauProfil();""",
u'rafraichir le panneau apres l\'avatar')

js = rempl(js,
u"""    profilEnCours.pseudo = data;""",
u"""    profilEnCours.pseudo = data;
    rafraichirPanneauProfil();""",
u'rafraichir le panneau apres le pseudo')

# --- 3. la fenetre gagne l'anneau ------------------------------------------
js = rempl(js,
u"""        <div class="pr-avatar">${avatarHtml(p, couleur)}</div>""",
u"""        <div class="pr-avatar-niv">${anneauNiveau(p, 92)}</div>""",
u'anneau dans la fenetre')

js = rempl(js,
u"""        <p class="pr-sous"><b>${echapperTexte(titreDepuisDeps(p.deps))}</b>${
          p.rang > 0 ? ` · <span class="pr-rang">${p.rang}${p.rang === 1 ? 'er' : 'e'}</span>` : ''}</p>""",
u"""        <p class="pr-sous">${p.niveau ? `<span class="pf-grade" style="background:${
          gradeDe(Number(p.niveau)).couleur}22;color:${gradeDe(Number(p.niveau)).couleur}">${
          gradeDe(Number(p.niveau)).nom}</span> ` : ''}<b>${echapperTexte(titreDepuisDeps(p.deps))}</b>${
          p.rang > 0 ? ` · <span class="pr-rang">${p.rang}${p.rang === 1 ? 'er' : 'e'}</span>` : ''}</p>""",
u'grade dans la fenetre')

# --- 4. sur telephone, l'onglet passe dans « Plus » -------------------------
js = rempl(js,
u"""const ONGLETS_MENU = ['territoire', 'communaute', 'bourse', 'echange', 'contrat', 'succes'];""",
u"""const ONGLETS_MENU = ['territoire', 'communaute', 'bourse', 'echange', 'contrat', 'succes', 'profil'];""",
u'profil dans le menu Plus')

# l'entree ecrite en dur ferait doublon avec celle que ONGLETS_MENU genere
js = rempl(js,
u"""    <div class="fp-sep"></div>
    <button class="fp-item" data-aller="profil">${ICONE_PROFIL}Mon profil</button>
    <button class="fp-item" data-aller="regles">${ICONE_REGLES}Règles du jeu</button>""",
u"""    <div class="fp-sep"></div>
    <button class="fp-item" data-aller="regles">${ICONE_REGLES}Règles du jeu</button>""",
u'suppression du doublon Mon profil')

js = rempl(js,
u"""  if(b.dataset.aller === 'profil'){ ouvrirProfil(window.__monId || null); return; }
""", u'', u'suppression du renvoi vers la fenetre')

# --- 5. le crochet de l'onglet ---------------------------------------------
js = rempl(js,
u"""    if(tab.dataset.tab === 'succes') loadSucces();""",
u"""    if(tab.dataset.tab === 'succes') loadSucces();
    if(tab.dataset.tab === 'profil') loadProfilPanneau();""",
u'crochet de l\'onglet Profil')

ecrire('app.js', js)

print(u'patch44 applique.')
