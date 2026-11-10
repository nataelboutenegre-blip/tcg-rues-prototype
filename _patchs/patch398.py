# patch398 (10/11/2026) : échanges de communes entre clans différents (s2-133, idée de zintox, 9/11).
# Depuis la carte : fiche d'une commune d'un joueur d'un autre clan -> « Proposer un échange » -> même parcours
# que l'échange de clan sur la carte (lot 8/11). Un échange entre clans par semaine.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A = 'app.js'
# la fiche : le bouton pour un joueur d'un autre clan
rep(A, """  else if(!mienne && protegee) note = 'Protégée par un bouclier : impossible de l’attaquer pour l’instant.';""",
"""  let echInter = '';   // patch398 : échange entre clans (s2-133)
  if(!allie && !mienne && c.joueurId && enFrontClan() && CLANS){
    const e = clanEch.etat, sonClan = clansCarte.get(c.joueurId), monClan = clansCarte.get(window.__monId);
    if(e && e.clan && sonClan && (!monClan || sonClan.tag !== monClan.tag)){
      const dispo = e.inter_dispo_le ? new Date(e.inter_dispo_le) : null;
      const raison = e.pret_le ? 'Échanges possibles 48 h après ton arrivée dans ton clan'
        : dispo && dispo.getTime() > Date.now() ? `Un échange entre clans par semaine : le prochain le ${dispo.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })} à ${dispo.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}` : '';
      echInter = `<button class="pc-action pc-ech-inter" data-pc="ech-inter"${raison ? ` disabled title="${echapperHtml(raison)}"` : ''}><span aria-hidden="true">🤝</span>Proposer un échange <small>· 1 par semaine</small></button>${raison ? `<p class="pc-note">${echapperHtml(raison)}.</p>` : ''}`;
    }
  }
  if(allie && enFrontClan()){}   // la suite des notes, comme avant
  else if(!mienne && protegee) note = 'Protégée par un bouclier : impossible de l’attaquer pour l’instant.';""")
rep(A, """      `<button class="pc-action ${cl}" data-pc="${ic}" title="${echapperHtml(titre)}">${ICONES_PC[ic]}${txt}</button>`).join('')}</div>` : ''}${btActions}${libBloc}`;""",
"""      `<button class="pc-action ${cl}" data-pc="${ic}" title="${echapperHtml(titre)}">${ICONES_PC[ic]}${txt}</button>`).join('')}</div>` : ''}${echInter}${btActions}${libBloc}`;""")
rep(A, """  if(quoi === 'ech-clan'){ const o = othersMap.get(code); if(o && o.joueurId) eccDemarrer(o, code); return; }   // patch316, lot 8/11 : sans quitter la carte""",
"""  if(quoi === 'ech-clan'){ const o = othersMap.get(code); if(o && o.joueurId) eccDemarrer(o, code); return; }   // patch316, lot 8/11 : sans quitter la carte
  if(quoi === 'ech-inter'){ const o = othersMap.get(code); if(o && o.joueurId) eccDemarrer(o, code, true); return; }   // patch398""")
# le parcours sur la carte
rep(A, """function eccDemarrer(o, code){
  echCarte = { qui: o.joueurId, pseudo: o.pseudo || 'ton coéquipier', recoit: code, nom: o.nom, tier: eccTier(o), avant: new Set(joueursSurlignes) };""",
"""function eccDemarrer(o, code, inter){
  echCarte = { qui: o.joueurId, pseudo: o.pseudo || (inter ? 'ce joueur' : 'ton coéquipier'), recoit: code, nom: o.nom, tier: eccTier(o), inter: !!inter, avant: new Set(joueursSurlignes) };   // patch398 : inter""")
rep(A, """  el.innerHTML = `<span class="ecc-ic">🤝</span><div class="ecc-txt">Échange avec <b>${echapperHtml(echCarte.pseudo)}</b> : tu reçois <b>${echapperHtml(echCarte.nom)}</b> (${eccLibelle(t)}).<br><span>Touche une de tes communes <b class="rarete ${t}">${eccLibelle(t)}s</b> pour la proposer.</span></div>
    <div class="ecc-btns"><button type="button" data-ecc="clan">Onglet Clan</button><button type="button" data-ecc="annuler">Annuler</button></div>`;""",
"""  el.innerHTML = `<span class="ecc-ic">🤝</span><div class="ecc-txt">${echCarte.inter ? 'Échange entre clans' : 'Échange'} avec <b>${echapperHtml(echCarte.pseudo)}</b> : tu reçois <b>${echapperHtml(echCarte.nom)}</b> (${eccLibelle(t)}).<br><span>Touche une de tes communes <b class="rarete ${t}">${eccLibelle(t)}s</b> pour la proposer.${echCarte.inter ? ' Un échange entre clans par semaine.' : ''}</span></div>
    <div class="ecc-btns">${echCarte.inter ? '' : '<button type="button" data-ecc="clan">Onglet Clan</button>'}<button type="button" data-ecc="annuler">Annuler</button></div>`;   // patch398""")
rep(A, """  const { data, error } = await sb.rpc('clan_ech_proposer', { p_cible: echCarte.qui, p_ma: code, p_sa: echCarte.recoit });""",
"""  const { data, error } = await sb.rpc(echCarte.inter ? 'clan_ech_inter_proposer' : 'clan_ech_proposer', { p_cible: echCarte.qui, p_ma: code, p_sa: echCarte.recoit });   // patch398""")
# l'onglet Clan : les propositions entre clans, la règle
rep(A, """      <div class="ce-qui">${recu ? `<b>${echapperTexte(x.pseudo)}</b> te propose` : `à <b>${echapperTexte(x.pseudo)}</b> · en attente`} · ${ceDans(x.expire_le)}</div>""",
"""      <div class="ce-qui">${recu ? `<b>${echapperTexte(x.pseudo)}</b> te propose` : `à <b>${echapperTexte(x.pseudo)}</b> · en attente`}${x.inter ? ' · <span class="ce-inter">entre clans</span>' : ''} · ${ceDans(x.expire_le)}</div>""")
rep(A, """<li>Il faut être dans le clan depuis 48 h. Un échange ne rapporte aucun point de combat.</li></ul></div>`;""",
"""<li>Il faut être dans le clan depuis 48 h. Un échange ne rapporte aucun point de combat.</li><li><b>Entre clans</b> : touche sur la carte une commune d’un joueur d’un autre clan, puis « Proposer un échange ». Mêmes règles, mais <b>un échange par semaine</b>${clanEch.etat && clanEch.etat.inter_dispo_le && new Date(clanEch.etat.inter_dispo_le).getTime() > Date.now() ? ` (ton prochain le ${new Date(clanEch.etat.inter_dispo_le).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })})` : ''}.</li></ul></div>`;   // patch398""")
rep(A, """        t: `<b>${echapperTexte(x.pseudo || 'Un membre')}</b> te propose un échange de clan`,""",
"""        t: `<b>${echapperTexte(x.pseudo || 'Un membre')}</b> te propose un échange ${x.inter ? 'entre clans' : 'de clan'}`,   // patch398""")
rep('style.css', "/* patch396 : le fil de la roue */",
"""/* patch398 : échanges entre clans */
.ce-inter{ display:inline-block; padding:1px 6px; border-radius:999px; background:rgba(110,195,240,.16); color:#9FD8F5; font-size:.66rem; font-weight:700; }
.pc-action.pc-ech-inter{ margin-top:6px; color:#9FD8F5; border-color:rgba(110,195,240,.35); }
.pc-action.pc-ech-inter small{ color:#7F92AA; font-size:.72rem; }
.pc-action.pc-ech-inter:disabled{ opacity:.55; cursor:default; }
/* patch396 : le fil de la roue */""")
rep('index.html', """et les 3 h de protection ne jouent pas contre lui.</p><!-- patch341 -->""",
"""et les 3 h de protection ne jouent pas contre lui. <b>Entre clans différents</b> : touche sur la carte une commune d'un joueur d'un autre clan, puis « Proposer un échange » ; mêmes règles (chacun dans son clan depuis 48 h), mais <b>un échange par semaine</b> par joueur, 2 propositions en attente au plus.</p><!-- patch341, patch398 -->""")
print('patch398 ok')
