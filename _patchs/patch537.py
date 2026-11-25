# patch537 (Maroli, Arkhannou) : échange de clan avec un cran d'écart de rareté, 1 par jour (s3-76) ;
# les communes déjà dans une proposition envoyée sont grisées (toujours sélectionnables).
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')

# la rareté propre à chaque commune d'une proposition (s3-76 la renvoie)
rep('app.js', "  const t = ceTier(tier || c.tier);\n  return `<span class=\"ce-com\">",
              "  const t = ceTier(c.tier || tier);   // patch537 : chaque côté a sa rareté\n  return `<span class=\"ce-com\">")

# listes : grisage des communes déjà proposées
rep('app.js', """  return l.slice(0, 80).map(c => `<button type="button" class="ce-choix" data-${cle}="${echapperTexte(c.code)}" aria-pressed="${c.code === choisi}"${c.raison ? ' disabled' : ''}>${ceCommune(c)}${c.raison ? `<span class="ce-raison">${echapperTexte(c.raison)}</span>` : ''}</button>`).join('');
}""", """  const pro = cePropose(cote);   // patch537
  return l.slice(0, 80).map(c => { const qui = !c.raison && pro.get(c.code);
    return `<button type="button" class="ce-choix${qui ? ' ce-pro' : ''}" data-${cle}="${echapperTexte(c.code)}" aria-pressed="${c.code === choisi}"${c.raison ? ' disabled' : ''}${qui ? ` title="Déjà proposée à ${echapperTexte(qui)}"` : ''}>${ceCommune(c)}${c.raison ? `<span class="ce-raison">${echapperTexte(c.raison)}</span>` : qui ? '<span class="ce-tag-pro">⇄ proposée</span>' : ''}</button>`; }).join('');
}
// patch537 : communes déjà dans une de mes propositions en attente (côté 1 : les miennes ; côté 2 : celles du coéquipier choisi)
function cePropose(cote){
  const m = new Map(), env = (clanEch.etat && clanEch.etat.envoyes) || [];
  const qui = ((clanEch.etat && clanEch.etat.membres) || []).find(x => x.id === clanEch.qui);
  for(const x of env){
    if(cote === 1 && x.donne) m.set(x.donne.code, x.pseudo);
    if(cote === 2 && x.recoit && qui && x.pseudo === qui.pseudo) m.set(x.recoit.code, x.pseudo);
  }
  return m;
}
// patch537 : un cran d'écart de rareté permis une fois par jour, si ni moi ni le coéquipier ne l'avons déjà fait
function ceEcartOk(){
  const e = clanEch.etat, qui = ((e && e.membres) || []).find(x => x.id === clanEch.qui);
  return !!(e && 'ecart_fait' in e && !e.ecart_fait && qui && !qui.ecart_fait);
}
function ceRang(t){ return ['commun', 'peucommun', 'rare', 'epique', 'legendaire'].indexOf(t); }""")

rep('app.js', "  return mienne ? clanEch.leurs.filter(c => c.tier === mienne.tier) : clanEch.leurs;",
              "  if(!mienne) return clanEch.leurs;\n  const ok = ceEcartOk();   // patch537\n  return clanEch.leurs.filter(c => c.tier === mienne.tier || (ok && Math.abs(ceRang(c.tier) - ceRang(mienne.tier)) === 1));")

rep('app.js', """    ? `<span>Tu donnes <b>${echapperTexte(m.nom)}</b> à ${echapperTexte(qui.pseudo)} contre <b>${echapperTexte(s.nom)}</b>.</span>""",
              """    ? `<span>Tu donnes <b>${echapperTexte(m.nom)}</b> à ${echapperTexte(qui.pseudo)} contre <b>${echapperTexte(s.nom)}</b>.${m.tier !== s.tier ? ' <small class="ce-ecart">Rareté différente : ton échange de ce type du jour.</small>' : ''}</span>""")

rep('app.js', "  if(t3) t3.textContent = '3. Tu reçois · ' + (mienne ? ceTier(mienne.tier).label.toLowerCase() : 'même rareté');",
              """  if(t3) t3.textContent = '3. Tu reçois · ' + (!mienne ? 'même rareté ou un cran d\\'écart'   // patch537
    : ceEcartOk() ? TIERS.filter(t => Math.abs(ceRang(t.id) - ceRang(mienne.tier)) <= 1).map(t => t.label.toLowerCase()).join(', ')
    : ceTier(mienne.tier).label.toLowerCase() + (clanEch.qui ? ' (écart de rareté déjà utilisé aujourd\\'hui)' : ''));""")

rep('app.js', "<li>Seulement entre membres du clan, une commune contre une commune de même rareté.</li>",
              "<li>Seulement entre membres du clan, une commune contre une commune de même rareté. <b>Une fois par jour</b>, chacun peut aussi faire un échange avec <b>un cran d'écart</b> (légendaire ↔ épique, épique ↔ rare, rare ↔ peu commun, peu commun ↔ commun).</li>")

rep('style.css', ".ce-raison{ font-size:.72rem; color: var(--brume); white-space:nowrap; }",
""".ce-raison{ font-size:.72rem; color: var(--brume); white-space:nowrap; }
.ce-choix.ce-pro .ce-com{ opacity:.5; }   /* patch537 : déjà proposée */
.ce-tag-pro{ font-size:.7rem; color: var(--c-legendaire); border:1px solid rgba(240,180,41,.45); border-radius:6px; padding:1px 6px; white-space:nowrap; }
.ce-ecart{ display:block; color: var(--brume); font-size:.76rem; margin-top:2px; }""")
