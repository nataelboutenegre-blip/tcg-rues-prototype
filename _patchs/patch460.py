# patch460 : bonus de territoire selon la population (s3-30) — textes de la saison 3 (html.topo)
import sys, os
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(fichier, a, b, n=1):
    p = os.path.join(R, fichier); s = open(p, encoding='utf-8').read()
    assert s.count(a) == n, (fichier, a[:80], s.count(a)); s = s.replace(a, b); open(p, 'w', encoding='utf-8').write(s)
H, A = 'index.html', 'app.js'
L = '<span class="nom-s2">60</span><span class="nom-s3">45</span>'
rep(H, '<tr><td>Chaque commune tenue</td><td class="chiffre or">1 · 3 · 12 · 25 · 60</td></tr>',
       '<tr><td>Chaque commune tenue</td><td class="chiffre or">1 · 3 · 12 · 25 · ' + L + '</td></tr><!-- patch460 -->')
rep(H, '<p>Par département, seul le palier le plus haut compte (métropole<span data-s3="suisse"> et cantons suisses</span>).',
       '<p>Par département, seul le palier le plus haut compte (métropole<span data-s3="suisse"> et cantons suisses</span>).<span class="nom-s3"> Les bonus de département et de région sont <b>multipliés selon leur population</b> : × 0,6 pour les moins peuplés (Lozère, Creuse…) jusqu\'à × 1,6 pour les plus peuplés (Nord, Paris, Bouches-du-Rhône, Zurich…) ; un département moyen (environ 540 000 habitants) reste à × 1. Les seuils restent en pourcentage de communes.</span><!-- patch460 -->')
s = open(os.path.join(R, A), encoding='utf-8').read()
i = s.index('const CL_CALC_FRONT = `'); j = s.index('`;', i)
bloc = s[i:j]
a1 = 'légendaire <b>60</b>'
assert bloc.count(a1) == 1, bloc[:300]
a2 = 'dans plus de la moitié de ses départements.</span></div></div>'
assert bloc.count(a2) == 1
bloc2 = bloc.replace(a1, 'légendaire <b>' + L + '</b>').replace(a2, 'dans plus de la moitié de ses départements.<span class="nom-s3"> Ces bonus sont multipliés selon la population du département ou de la région : <b>× 0,6</b> à <b>× 1,6</b>.</span></span></div></div>')
s = s[:i] + bloc2 + s[j:]
open(os.path.join(R, A), 'w', encoding='utf-8').write(s)
rep(A, "`${String(x.part).replace('.', ',')} % (${nb(x.n)} / ${nb(x.taille)})${x.seul ? ' · seul en tête' : ''} · palier ${x.palier} %`,",
       "`${String(x.part).replace('.', ',')} % (${nb(x.n)} / ${nb(x.taille)})${x.seul ? ' · seul en tête' : ''} · palier ${x.palier} %${x.coef != null && Number(x.coef) !== 1 ? ` · population × ${String(Number(x.coef).toFixed(2)).replace('.', ',')}` : ''}`,   // patch460")
rep(A, "`Région ${e(r.region)}`, plus(r.pts), `${r.n} départements sur ${r.total} à 10 % ou plus`)).join('');",
       "`Région ${e(r.region)}`, plus(r.pts), `${r.n} départements sur ${r.total} à 10 % ou plus${r.coef != null && Number(r.coef) !== 1 ? ` · population × ${String(Number(r.coef).toFixed(2)).replace('.', ',')}` : ''}`)).join('');   // patch460")
print('patch460 : ok')
