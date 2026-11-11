# patch410 (11/11/2026) : les points d'une bombe selon son niveau (s2-136, idée d'Oshannir)
#  - Classement › « Comment c'est calculé » et Règles : « Bombe lancée : niveau 1 +150 · niveau 2 +300 · niveau 3 +500 » ;
#  - fiche du Centre (Défendre) : les points de chaque niveau sous les tuiles, et dans le texte avant de préparer.
# Les montants viennent de score_s2 (bombe_1..3) ; le jeu les écrit en dur (bombePoints), à changer ensemble.
import sys
def rep(chemin, avant, apres, nb=1):
    t = open(chemin, encoding='utf-8').read()
    n = t.count(avant)
    if n != nb: sys.exit(f'{chemin} : {n} au lieu de {nb} pour {avant[:70]!r}')
    open(chemin, 'w', encoding='utf-8').write(t.replace(avant, apres))
A, I, C = 'app.js', 'index.html', 'style.css'
if 'patch410' in open(A, encoding='utf-8').read(): sys.exit('déjà appliqué')

rep(A, """<br>Bombe lancée <b>+300</b>. Rébellion""",
"""<br>Bombe lancée, selon son niveau : <b>+150</b> · <b>+300</b> · <b>+500</b>. Rébellion""")
rep(I, """                  <tr><td>Bombe lancée</td><td class="chiffre or">+300</td></tr>""",
"""                  <tr><td>Bombe lancée, selon son niveau (1 · 2 · 3)</td><td class="chiffre or">+150 · +300 · +500</td></tr><!-- patch410 -->""")
rep(A, """      return `<div class="cr-niv${fait ? ' fait' : ''}${cours ? ' cours' : ''}"><b>${R[i]} km</b><span>${cours ? 'dans ' + formatDuree((H[i] * 3600 - ec) * 1000) : `Niveau ${i + 1} · ${H[i]} h`}</span>""",
"""      return `<div class="cr-niv${fait ? ' fait' : ''}${cours ? ' cours' : ''}"><b>${R[i]} km</b><span>${cours ? 'dans ' + formatDuree((H[i] * 3600 - ec) * 1000) : `Niveau ${i + 1} · ${H[i]} h`}</span><em class="cr-pts">+${bombePoints(i + 1)} pts</em>""")
rep(A, """      <p class="cr-txt">Une bombe est prête en <b>${H[0]} h</b> (rayon ${R[0]} km), puis grossit : <b>${R[1]} km</b> à ${H[1]} h, <b>${R[2]} km</b> à ${H[2]} h.""",
"""      <p class="cr-txt">Une bombe est prête en <b>${H[0]} h</b> (rayon ${R[0]} km), puis grossit : <b>${R[1]} km</b> à ${H[1]} h, <b>${R[2]} km</b> à ${H[2]} h. Au classement : <b>+${bombePoints(1)}</b>, <b>+${bombePoints(2)}</b> ou <b>+${bombePoints(3)}</b> selon son niveau.""")
open(A, 'a', encoding='utf-8').write("""
// ---------- patch410 : les points d'une bombe selon son niveau (s2-136 : score_s2 bombe_1..3) ----------
function bombePoints(n){ return [150, 300, 500][n - 1] || 300; }
""")
open(C, 'a', encoding='utf-8').write("""
/* ---------- patch410 : les points d'une bombe sous chaque niveau ---------- */
.cr-niv .cr-pts{ display:block; font-style:normal; font-size:.66rem; font-weight:700; color:#FFD36B; margin-top:2px; }
.cr-niv.cours .cr-pts{ margin-bottom:4px; }
""")
print('patch410 OK')
