# patch491 : les textes du jeu suivent s3-45 (bonus de région au prorata sous 500 communes).
# « Mon score › Territoires » dit « petite région × 0,20 », les règles et « Comment c'est calculé » l'expliquent,
# et la cloche du 22/11 l'annonce. Aucun changement de calcul ici : il est fait par le serveur.
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A, H = 'app.js', 'index.html'
rep(A, """${r.coef != null && Number(r.coef) !== 1 ? ` · population × ${String(Number(r.coef).toFixed(2)).replace('.', ',')}` : ''}`)).join('');   // patch460""",
       """${r.coef != null && Number(r.coef) !== 1 ? ` · population × ${String(Number(r.coef).toFixed(2)).replace('.', ',')}` : ''}${r.prorata != null && Number(r.prorata) < 1 ? ` · petite région × ${String(Number(r.prorata).toFixed(2)).replace('.', ',')}` : ''}`)).join('');   // patch460, patch491""")
rep(A, """Région : <b>+1&nbsp;200</b> si tu es seul en tête avec 10 % ou plus dans plus de la moitié de ses départements.""",
       """Région : <b>+1&nbsp;200</b> si tu es seul en tête avec 10 % ou plus dans plus de la moitié de ses départements (au prorata pour une région de moins de 500 communes : Luxembourg, Corse).""")
rep(H, """<tr><td>Région : seul en tête avec 10 % ou plus dans plus de la moitié de ses départements</td><td class="chiffre or">+1 200</td></tr><!-- patch339 -->""",
       """<tr><td>Région : seul en tête avec 10 % ou plus dans plus de la moitié de ses départements. Une région de moins de 500 communes (Luxembourg, Corse) rapporte au prorata de ses communes</td><td class="chiffre or">+1 200</td></tr><!-- patch339, patch491 -->""")
p = os.path.join(R, 'data', 'nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
e = next(x for x in d if x.get('date') == '2026-11-22')
l = "⚖️ Classement : le bonus de région est maintenant au prorata pour les régions de moins de 500 communes (Luxembourg × 0,2, Corse × 0,7). Avec ses 100 communes, le Luxembourg donnait un bonus de région entier dès les premiers paquets."
c = "Sur les nouvelles cartes, le bandeau du monument ne recouvre plus le nom de la commune. Après un duel classé, le jeu annonce les tickets du Mess gagnés."
if l not in e['nouveautes']:
    e['nouveautes'] = [l] + e['nouveautes']
    e.setdefault('correctifs', [])
    if c not in e['correctifs']: e['correctifs'] = [c] + e['correctifs']
    s = json.dumps(d, indent=2, ensure_ascii=False); json.loads(s)
    open(p, 'w', encoding='utf-8').write(s + '\n'); print('cloche : ok')
print('patch491 : fini')
