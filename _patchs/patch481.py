# patch481 : échange depuis la carte (entre clans ou dans le clan) : tes communes qui ne peuvent pas être
# échangées pour l'instant (en garnison, prise il y a moins de 24 h, échangée il y a moins de 48 h) sont grisées
# comme les autres raretés, et leur fiche dit pourquoi. Idée d'Arkhannou (21/11). Le serveur donne déjà la raison
# (clan_ech_communes -> clan_ech_raison) ; rien à changer côté serveur.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A = 'app.js'
rep(A, "          if(eccHors && c.joueur === ID_MOI) (c.tier === echCarte.tier ? eccOk : eccHors).addPath(p);   // patch411",
       "          if(eccHors && c.joueur === ID_MOI) (c.tier === echCarte.tier && !(echCarte.bloquees && echCarte.bloquees.has(code)) ? eccOk : eccHors).addPath(p);   // patch411, patch481")
rep(A, """  joueursSurlignes = new Set([ID_MOI]);   // tes communes ressortent
  try{ fermerPanneau(); }catch(e){}
  eccBandeau();
  renderMapOverlay(); demanderDessin();
}""", """  joueursSurlignes = new Set([ID_MOI]);   // tes communes ressortent
  try{ fermerPanneau(); }catch(e){}
  eccBandeau();
  renderMapOverlay(); demanderDessin();
  eccChargerBloquees(echCarte);   // patch481
}
// patch481 : mes communes qui ne peuvent pas partir pour l'instant (et pourquoi)
async function eccChargerBloquees(ec){
  try{
    if(!monUidClan){ const { data: u } = await sb.auth.getUser(); monUidClan = u && u.user ? u.user.id : null; }
    if(!monUidClan) return;
    const l = await ceCommunesDe(monUidClan);
    if(!l || echCarte !== ec) return;
    ec.bloquees = new Map(l.filter(c => c.raison).map(c => [c.code, c.raison]));
    eccBandeau();
    if(typeof CV !== 'undefined') CV.donneesSignature = '';
    renderMapOverlay(); demanderDessin();
  }catch(e){}
}""")
rep(A, "Seules tes communes <b class=\"rarete ${t}\">${eccLibelle(t)}s</b> ressortent, entourées de jaune : touches-en une pour la proposer.${echCarte.inter ? ' Un échange entre clans par jour.' : ''}</span>",
       "Seules tes communes <b class=\"rarete ${t}\">${eccLibelle(t)}s</b> ressortent, entourées de jaune : touches-en une pour la proposer.${echCarte.bloquees && echCarte.bloquees.size ? ' Les autres sont grisées : en garnison, prises il y a moins de 24 h ou échangées il y a moins de 48 h.' : ''}${echCarte.inter ? ' Un échange entre clans par jour.' : ''}</span>")
rep(A, """    return `<p class="pc-note ecc-non">🤝 Pour l’échange avec ${echapperHtml(echCarte.pseudo)}, choisis une commune <b>${eccLibelle(echCarte.tier)}</b>, de la même rareté que ${echapperHtml(echCarte.nom)}.</p>`;
""", """    return `<p class="pc-note ecc-non">🤝 Pour l’échange avec ${echapperHtml(echCarte.pseudo)}, choisis une commune <b>${eccLibelle(echCarte.tier)}</b>, de la même rareté que ${echapperHtml(echCarte.nom)}.</p>`;
  if(echCarte.bloquees && echCarte.bloquees.has(code))   // patch481
    return `<p class="pc-note ecc-non">🤝 ${echapperHtml(c.nom || 'Cette commune')} ne peut pas être échangée pour l’instant : ${echapperHtml(echCarte.bloquees.get(code))}.</p>`;
""")
print('patch481 : fini')
