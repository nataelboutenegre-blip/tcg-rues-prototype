# patch431 (13/11/2026) : les merveilles plus justes (va avec s2-143 ; Oshannir : « le premier qui clique est premier »).
#  - fenêtre d'ouverture : bandeau « Encore 9 h pour envoyer ton équipe : elle comptera depuis l'ouverture » + cloche ;
#  - paliers : ✦ mécène (24 h), ◆ bâtisseur (1 000 h) gravé pour toujours (au lieu des 10 premiers) ;
#  - savoir-faire : +2 % de rythme par monument restauré (40 % au plus), dans la carte « Ton équipe ».
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, S = 'app.js', 'style.css'
if 'patch431' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')

# savoir-faire dans « Ton équipe »
rep(A, """      <p>Outils niveau ${chNb(E.outils)} : ton équipe fait <b>${chVirgule(E.rythme)} heures</b> de travail par heure, sur ton chantier comme sur la merveille.</p>
""", """      <p>Outils niveau ${chNb(E.outils)} : ton équipe fait <b>${chVirgule(E.rythme)} heures</b> de travail par heure, sur ton chantier comme sur la merveille.</p>
      ${chSavoirHtml(E)}
""")

# la merveille : le texte, le bandeau d'ouverture, les paliers
rep(A, """      <p class="ch-note">Une seule à la fois, pour tout le jeu. Envoie ton équipe : ton propre chantier s’arrête pendant ce temps. Avec au moins ${seuil} h de travail données, tu deviens mécène : +${chR('mecene_tp', 20)} TP par jour, pour toujours. Les ${graves} plus gros contributeurs sont gravés.</p>""",
"""      <p class="ch-note">Une seule à la fois, pour tout le jeu. Envoie ton équipe : ton propre chantier s’arrête pendant ce temps. Envoyée dans les <b>${chR('ouverture_h', 12)} premières heures</b>, elle compte depuis l’ouverture. Avec au moins ${seuil} h données, tu deviens mécène : +${chR('mecene_tp', 20)} TP par jour, pour toujours. À partir de <b>${chNb(chR('batisseur', 1000))} h</b>, tu es bâtisseur : ton nom est gravé sur la merveille.</p>
      ${chOuvertureHtml(M, actif)}""")
rep(A, """        <div class="ch-carte merv"><div class="ch-haut"><h3>Les mécènes</h3><span class="ch-petit">${chNb(M.mecenes)} mécène${Number(M.mecenes) > 1 ? 's' : ''}</span></div>""",
"""        <div class="ch-carte merv"><div class="ch-haut"><h3>Les mécènes</h3><span class="ch-petit">${chNb(M.mecenes)} mécène${Number(M.mecenes) > 1 ? 's' : ''}${Number(M.batisseurs) ? ` · ${chNb(M.batisseurs)} bâtisseur${Number(M.batisseurs) > 1 ? 's' : ''}` : ''}</span></div>""")
rep(A, """<span>${x.moi ? 'Toi' : echapperTexte(x.pseudo)}${Number(x.heures) >= seuil ? ' ✦' : ''}</span>""",
"""<span>${x.moi ? 'Toi' : echapperTexte(x.pseudo)}${Number(x.heures) >= chR('batisseur', 1000) ? ' <i class="ch-bat" title="Bâtisseur">◆</i>' : Number(x.heures) >= seuil ? ' ✦' : ''}</span>""")
rep(A, """          <p class="ch-petit">✦ mécène (au moins ${seuil} h). Les ${graves} premiers sont gravés pour toujours.</p></div>""",
"""          <p class="ch-petit">✦ mécène (au moins ${seuil} h) · <i class="ch-bat">◆</i> bâtisseur (au moins ${chNb(chR('batisseur', 1000))} h) : tous les bâtisseurs sont gravés pour toujours.</p></div>""")
rep(A, """      : (mh >= seuil ? `Tu es mécène (${chNb(mh)} h). Continue pour monter parmi les ${chR('graves', 10)} premiers.`""",
"""      : (mh >= chR('batisseur', 1000) ? `Tu es bâtisseur (${chNb(mh)} h) : ton nom sera gravé sur la merveille.`
         : mh >= seuil ? `Tu es mécène (${chNb(mh)} h). Encore ${chNb(Math.ceil(chR('batisseur', 1000) - mh))} h pour devenir bâtisseur et être gravé.`""")
rep(A, """      ? `Ton équipe (${chNb(CH.equipe.ouvriers)} ouvriers, casques blancs) travaille sur la merveille.${c ? ' <b>Ton chantier est en pause.</b>' : ''} ${mh < seuil ? `Encore ${Math.ceil(seuil - mh)} h pour devenir mécène.` : 'Tu es mécène.'}`""",
"""      ? `Ton équipe (${chNb(CH.equipe.ouvriers)} ouvriers, casques blancs) travaille sur la merveille.${c ? ' <b>Ton chantier est en pause.</b>' : ''} ${mh < seuil ? `Encore ${Math.ceil(seuil - mh)} h pour devenir mécène.` : mh < chR('batisseur', 1000) ? `Tu es mécène. Encore ${chNb(Math.ceil(chR('batisseur', 1000) - mh))} h pour devenir bâtisseur.` : 'Tu es bâtisseur : ton nom sera gravé.'}`""")

# la cloche : une merveille vient d'ouvrir
rep(A, """    SAISON2 && CLANS ? rpc('clan_diplo_etat') : null,   // patch400
  ]);""", """    SAISON2 && CLANS ? rpc('clan_diplo_etat') : null,   // patch400
    SAISON2 ? rpc('merveille_ouverture') : null,   // patch431
  ]);""")
rep(A, """  const [prefs, journal, sieges, ech, clanE, alertes, quetes, recolte, clan, effaces, diplo] = await Promise.all([""",
"""  const [prefs, journal, sieges, ech, clanE, alertes, quetes, recolte, clan, effaces, diplo, merv] = await Promise.all([""")
rep(A, """  NC.d = { journal, sieges, ech, clanE, alertes, quetes, recolte: Array.isArray(recolte) ? recolte[0] : recolte, clan, effaces, diplo };""",
"""  NC.d = { journal, sieges, ech, clanE, alertes, quetes, recolte: Array.isArray(recolte) ? recolte[0] : recolte, clan, effaces, diplo, merv };""")
rep(A, """  if(SAISON2 && BATIMENTS && Array.isArray(BATIMENTS.banque_reperee_par)){   // patch375 : un Radar voit ma Banque""",
"""  if(d.merv && !d.merv.envoye && new Date(d.merv.fin_fenetre).getTime() > Date.now()){   // patch431 : une merveille ouvre
    const f = new Date(d.merv.fin_fenetre), hh = f.getHours() + 'h' + String(f.getMinutes()).padStart(2, '0');
    items.push({ cle: `merv|${d.merv.code}`, sec: 'afaire', c: 'alerte', i: '🏛️', mode: 'terra',
      t: `La merveille <b>${echapperTexte(chMaj(d.merv.nom || ''))}</b> ouvre : envoie ton équipe`,
      s: `Avant ${hh} : elle comptera depuis l’ouverture`, a: 'Envoyer',
      aller: () => ncAller('terra', 'monuments', () => setTimeout(() => { const el = document.querySelector('.ch-h3.merv'); if(el) el.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 600)) });
  }
  if(SAISON2 && BATIMENTS && Array.isArray(BATIMENTS.banque_reperee_par)){   // patch375 : un Radar voit ma Banque""")

open(A, 'a', encoding='utf-8').write(r"""
// ---------- patch431 : merveilles plus justes (s2-143) ----------
function chSavoirHtml(E){
  if(!E || E.savoir == null) return '';
  const n = Number(E.restaures) || 0, pct = Math.round((Number(E.savoir) || 0) * 100), max = Math.round(chR('savoir_max', 0.4) * 100);
  return `<p class="ch-savoir"><b>Savoir-faire +${pct} %</b> · ${n} monument${n > 1 ? 's' : ''} restauré${n > 1 ? 's' : ''} chez toi. Chacun ajoute ${Math.round(chR('savoir_pct', 0.02) * 100)} % au rythme de ton équipe${pct >= max ? ' : le maximum est atteint.' : `, jusqu’à ${max} %.`}</p>`;
}
function chOuvertureHtml(M, actif){
  if(!M || !M.ouverte_le) return '';
  const fin = new Date(M.ouverte_le).getTime() + chR('ouverture_h', 12) * 3600e3, reste = fin - Date.now();
  if(reste <= 0) return '';
  const deja = actif || (M.moi && Number(M.moi.heures) > 0);
  return `<div class="ch-ouverture${deja ? ' ok' : ''}"><b>Ouverture</b><span>${deja ? 'Ton équipe compte depuis l’ouverture.' : `Encore <b>${formatDuree(reste)}</b> pour envoyer ton équipe : elle comptera depuis l’ouverture, comme les premiers.`}</span></div>`;
}
""")

open(S, 'a', encoding='utf-8').write("""
/* patch431 : merveilles plus justes */
.ch-savoir{ margin:6px 0 0; font-size:.86rem; color:var(--brume); line-height:1.45; }
.ch-savoir b{ color:var(--c-legendaire); }
.ch-bat{ font-style:normal; color:var(--c-legendaire); }
.ch-ouverture{ display:flex; gap:10px; align-items:center; margin:8px 0 12px; padding:10px 12px; border-radius:12px; background:rgba(240,180,41,.12); border:1px solid rgba(240,180,41,.45); font-size:.9rem; line-height:1.4; }
.ch-ouverture > b{ flex:none; font-family:var(--titre); font-weight:800; text-transform:uppercase; letter-spacing:.05em; color:var(--c-legendaire); }
.ch-ouverture.ok{ background:rgba(34,160,107,.12); border-color:rgba(34,160,107,.45); }
.ch-ouverture.ok > b{ color:#5fd39e; }
""")
print('patch431 OK')
