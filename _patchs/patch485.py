# patch485 : l'attaquant apprend qu'on l'a défendu, ou que son siège est tombé (idée d'ASMFCB), avec s3-43.
# Cloche : une ligne bleue « défense » par siège (À faire tant que le siège court, avec « Relancer »),
# et un bandeau bleu la première fois. Aperçu validé le 22/11 à 10 h 46.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A, C = 'app.js', 'style.css'

rep(A, """  const [prefs, journal, sieges, ech, clanE, alertes, quetes, recolte, clan, effaces, diplo, merv] = await Promise.all([""",
       """  const [prefs, journal, sieges, ech, clanE, alertes, quetes, recolte, clan, effaces, diplo, merv, siegeAl] = await Promise.all([""")
rep(A, """    SAISON2 ? rpc('merveille_ouverture') : null,   // patch431
  ]);""", """    SAISON2 ? rpc('merveille_ouverture') : null,   // patch431
    SAISON2 ? rpc('mes_alertes_siege') : null,   // patch485
  ]);""")
rep(A, """  NC.d = { journal, sieges, ech, clanE, alertes, quetes, recolte: Array.isArray(recolte) ? recolte[0] : recolte, clan, effaces, diplo, merv };""",
       """  NC.d = { journal, sieges, ech, clanE, alertes, quetes, recolte: Array.isArray(recolte) ? recolte[0] : recolte, clan, effaces, diplo, merv, siegeAl };""")
rep(A, """  await vusP;   // patch482
  ncConstruire();
}""", """  await vusP;   // patch482
  ncConstruire();
  ncDefenseBandeau();   // patch485
}

// patch485 : la première fois qu'on apprend une défense, un bandeau bleu (une fois par appareil et par compte)
var NC_DEF_VUS = new Set();
function ncDefenseBandeau(){
  const vus = ncVus();
  const neufs = NC.items.filter(x => x.c === 'defense' && x.sec === 'afaire' && !vus.has(x.cle)
    && !NC_DEF_VUS.has(x.cle) && !CV_VUS.set.has('bd:' + x.cle));
  if(!neufs.length) return;
  neufs.forEach(x => NC_DEF_VUS.add(x.cle));
  vusCompteMarquer(neufs.map(x => 'bd:' + x.cle));
  const it = neufs[0];
  const el = document.createElement('div');
  el.className = 'grande-conquete gc-defense';
  el.setAttribute('role', 'status');
  el.innerHTML = `<span class="gc-ico">🛡️</span><span class="gc-tx"><b>${it.t.replace(/<\\/?b>/g, '')}</b><small>${it.s}</small></span>`;
  el.addEventListener('click', () => { el.remove(); if(it.aller) it.aller(); });
  document.body.appendChild(el);
  requestAnimationFrame(() => el.classList.add('visible'));
  setTimeout(() => { el.classList.remove('visible'); setTimeout(() => el.remove(), 400); }, 7000);
}""")
rep(A, """  // patch344 : on me cite dans la discussion""", """  // patch485 : l'attaquant apprend qu'on l'a défendu, ou que son siège est tombé (idée d'ASMFCB)
  if(Array.isArray(d.siegeAl)){
    const fr = (x) => Number(x || 0).toLocaleString('fr-FR');
    for(const a of d.siegeAl){
      const nomA = `<b>${echapperTexte(a.nom || a.commune_code)}</b>`;
      if(a.type === 'defendu'){
        const jauge = a.resistance ? ` (${fr(a.degats)} / ${fr(a.resistance)})` : '';
        items.push({ cle: `sd|${a.siege_id}|${a.n}`, sec: a.ouvert ? 'afaire' : 'histo', c: 'defense', i: '🛡️', mode: 'front',
          t: `<b>${echapperTexte(a.defenseur_pseudo || 'Le défenseur')}</b> a défendu ${nomA}`,
          s: `−${fr(a.recul)} sur ta jauge${jauge}${a.devient_long ? ' · le siège devient long' : ''} · ${ilYA(a.le)}`,
          a: a.ouvert ? 'Relancer' : null, aller: () => { ncFermer(); ouvrirSiege(a.commune_code); } });
      } else if(a.type === 'tombee'){
        items.push({ cle: `st|${a.siege_id}`, sec: 'histo', c: 'defense', i: '⌛', mode: 'front',
          t: `Ton siège de ${nomA} est tombé`,
          s: `${siegeExpirationH()} h sans vague${a.energie_rendue ? ` · ${fr(a.energie_rendue)} ⚡ rendus` : ''} · ${ilYA(a.le)}` });
      }
    }
  }
  // patch344 : on me cite dans la discussion""")
rep(A, """// patch485 : la première fois qu'on apprend une défense""", """function siegeExpirationH(){ return 24; }   // patch485 : config_jeu 'siege'.expiration_h (le jeu ne le lit pas encore)
// patch485 : la première fois qu'on apprend une défense""")
rep(C, """.grande-conquete.gc-bombe .gc-tx b em{ color:#FF9C95; }""", """.grande-conquete.gc-bombe .gc-tx b em{ color:#FF9C95; }
/* patch485 : la défense, en bleu */
.grande-conquete.gc-defense{ background:linear-gradient(90deg,#0E2A4A,#13284A 60%); border-color:#3898EC; box-shadow:0 14px 40px rgba(0,0,0,.5), 0 0 30px rgba(56,152,236,.3); cursor:pointer; }
.grande-conquete.gc-defense .gc-tx small{ color:#A9C8EC; }
.nc-ico.defense{ background:rgba(56,152,236,.22); }
.nc-item:has(.nc-ico.defense){ box-shadow: inset 3px 0 0 #3898EC; }""")
print('patch485 : fini')
