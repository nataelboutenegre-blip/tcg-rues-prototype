# patch367 (7/11/2026) : la protection contre les séries noires (s2-113, demande de Nataël).
#
# Après 2 assauts perdus aux dés d'affilée sur une même commune, les suivants
# sur elle ont +15 % (90 % au plus) jusqu'à la prochaine victoire aux dés ;
# jamais contre une commune en garnison. Le serveur décide (sieges.pertes_suite,
# serie_noire_bonus) ; le jeu l'explique :
#   - fiche d'attaque : « Série noire : … celui-ci a +15 % » (ou « pas de coup
#     de pouce contre une garnison ») ;
#   - scène d'assaut : sous « Repoussé », « Série noire : … tes prochains auront +15 % » ;
#   - règles : une phrase.
import pathlib

def rep(s, avant, apres, n=1):
    c = s.count(avant)
    assert c == n, f'{c} fois au lieu de {n} : {avant[:70]!r}'
    return s.replace(avant, apres)

F = pathlib.Path('app.js'); s = F.read_text(encoding='utf-8')
assert 'patch367' not in s, 'patch367 déjà appliqué'

s = rep(s, "let attaqueEnGarnison = false;   // patch91 : la cible ouverte est-elle en garnison",
"""let attaqueEnGarnison = false;   // patch91 : la cible ouverte est-elle en garnison
// patch367 : la série noire (s2-113) ; le réglage vit côté serveur (config_jeu 'serie_noire')
const SN_PERTES = 2, SN_BONUS = 15;
let attaquePertes = 0, attaquePertesCode = null;
const ICONE_TREFLE = '<svg class="sn-ic" viewBox="0 0 24 24" aria-hidden="true"><g fill="currentColor"><circle cx="8.5" cy="8.5" r="4"/><circle cx="15.5" cy="8.5" r="4"/><circle cx="8.5" cy="15.5" r="4"/><circle cx="15.5" cy="15.5" r="4"/></g><path d="M12 12l5 9" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/></svg>';""")

s = rep(s, """    sb.from('sieges').select('victoires_consecutives, dernier_round')
      .eq('attacker_id', uid).eq('commune_code', code).maybeSingle(),""",
"""    sb.from('sieges').select('victoires_consecutives, dernier_round, pertes_suite')   // patch367
      .eq('attacker_id', uid).eq('commune_code', code).maybeSingle(),""")

s = rep(s, """  const serie = siege ? siege.victoires_consecutives : 0;
  const dernier = siege && siege.dernier_round ? new Date(siege.dernier_round).getTime() : 0;""",
"""  const serie = siege ? siege.victoires_consecutives : 0;
  const dernier = siege && siege.dernier_round ? new Date(siege.dernier_round).getTime() : 0;
  // patch367 : la série noire (le siège expire après 24 h sans assaut)
  attaquePertes = siege && dernier > Date.now() - 24 * 3600e3 ? Number(siege.pertes_suite) || 0 : 0;
  attaquePertesCode = code;""")

s = rep(s, """      : `<div class="db-badge">${ICONE_DEBUTANT}<span><b>Bonus de débutant</b> · ${debutantReste()} : ${a.chances}\\u00a0% ici, même en prudent et même loin de chez toi. Il s’arrête à ta première conquête.</span></div>`) : ''}""",
"""      : `<div class="db-badge">${ICONE_DEBUTANT}<span><b>Bonus de débutant</b> · ${debutantReste()} : ${a.chances}\\u00a0% ici, même en prudent et même loin de chez toi. Il s’arrête à ta première conquête.</span></div>`) : ''}
    ${SAISON2 && attaquePertes >= SN_PERTES ? (attaqueEnGarnison
      ? `<div class="sn-badge non">${ICONE_TREFLE}<span><b>Série noire</b> : ${attaquePertes} assauts perdus d’affilée ici, mais pas de coup de pouce contre une commune en garnison.</span></div>`
      : `<div class="sn-badge">${ICONE_TREFLE}<span><b>Série noire</b> : ${attaquePertes} assauts perdus d’affilée ici. Celui-ci a <b>+${SN_BONUS}\\u00a0%</b>, jusqu’à ta prochaine victoire sur cette commune.</span></div>`) : ''}""")

s = rep(s, """    // patch86 : l'assaut mis en scene remplace les notifications
    mettreEnSceneAssaut(cibleVue, r);""",
"""    // patch367 : série noire, compter les assauts perdus aux dés (le serveur fait foi, la fiche le relit ensuite)
    if(SAISON2 && !r.conquise && attaquePertesCode === code && !attaqueEnGarnison){
      attaquePertes = (r.gagne || r.par_garnison) ? 0 : attaquePertes + 1;
      if(!r.gagne && !r.par_garnison) r.sn_pertes = attaquePertes;
    }
    // patch86 : l'assaut mis en scene remplace les notifications
    mettreEnSceneAssaut(cibleVue, r);""")

# patch367 : la scène d'assaut le dit, sous « Repoussé » (une notification passerait sous le voile)
s = rep(s, """          : `${nomCible} tient bon. Retente ta chance : une défaite ne te fait rien perdre.`;
      if(!passe) sonsOuverture.assautPerdu();""",
"""          : `${nomCible} tient bon. Retente ta chance : une défaite ne te fait rien perdre.`;
      if(!parGarnison && r.sn_pertes >= SN_PERTES) d.innerHTML += `<span class="as-sn">${ICONE_TREFLE}<span><b>Série noire</b> : ${r.sn_pertes === SN_PERTES
        ? `2 assauts perdus d’affilée ici, tes prochains auront <b>+${SN_BONUS}\\u00a0%</b>`
        : `tes prochains assauts ici gardent <b>+${SN_BONUS}\\u00a0%</b>`}, jusqu’à ta prochaine victoire.</span></span>`;   // patch367
      if(!passe) sonsOuverture.assautPerdu();""")

F.write_text(s, encoding='utf-8')

C = pathlib.Path('style.css'); css = C.read_text(encoding='utf-8')
assert 'patch367' not in css
css += """
/* patch367 : la série noire */
.sn-ic{ width:18px; height:18px; flex:none; color:#7FE3B4; }
.sn-badge{ display:flex; align-items:flex-start; gap:8px; margin-top:10px; padding:9px 10px; border-radius:10px;
  background:rgba(127,227,180,.09); border:1px solid rgba(127,227,180,.4); font-size:.8rem; line-height:1.4; }
.sn-badge b{ color:#A6F0CC; }
.sn-badge.non{ background:rgba(169,188,212,.08); border-color:rgba(169,188,212,.3); }
.sn-badge.non .sn-ic{ color:#A9BCD4; }
.sn-badge.non b{ color:#fff; }
.as-sn{ display:flex; align-items:flex-start; gap:7px; margin:12px auto 0; max-width:300px; padding:8px 10px; border-radius:10px; text-align:left;
  background:rgba(127,227,180,.1); border:1px solid rgba(127,227,180,.4); font-size:.82rem; line-height:1.4; }
.as-sn b{ color:#A6F0CC; }
"""
C.write_text(css, encoding='utf-8')

H = pathlib.Path('index.html'); h = H.read_text(encoding='utf-8')
assert 'patch367' not in h
h = rep(h, """Ensuite, tout redevient normal.</p><!-- patch365 -->""",
"""Ensuite, tout redevient normal.</p><!-- patch365 -->
            <p><b>Série noire</b> : après 2 assauts perdus d'affilée aux dés sur une même commune, tes assauts suivants sur elle ont <b>+15 %</b>, jusqu'à ta prochaine victoire (90 % au plus). Pas de coup de pouce contre une commune en garnison.</p><!-- patch367 -->""")
H.write_text(h, encoding='utf-8')
print('patch367 appliqué')
