# patch487 : les promos du week-end dans la boutique, avec s3-44 (lancé le 22/11 ; promos planifiées 27/11, 4/12, 11/12).
# Le prix barré est le prix de référence envoyé par le serveur (le plus bas des 30 jours avant la promo),
# badge « −30 % · jusqu'à dimanche » sur la carte, À la une montre une collection en promo, et la fiche
# dit jusqu'à quand. Avant la promo, rien ne change à l'écran.
import os, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait ({a[:50]!r})'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) au lieu de {n} pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok ({a[:50]!r})')
A, C = 'app.js', 'style.css'

rep(A, """function bqePrixHtml(a){
  const moi = bqePrixMoi(a), plein = Number(a.prix_centimes);""", """// patch487 : la promo du week-end (s3-44) ; le prix barré est le prix de référence du serveur
const bqePromo = (a) => a && a.promo && a.promo.fin && new Date(a.promo.fin).getTime() > Date.now() ? a.promo : null;
function bqePromoFin(p){
  const f = new Date(new Date(p.fin).getTime() - 60000);   // la promo finit à minuit : « jusqu'à dimanche »
  const j = Math.floor((new Date(f.toDateString()) - new Date(new Date().toDateString())) / 86400000);
  return j <= 0 ? 'jusqu’à ce soir minuit' : j === 1 ? 'jusqu’à demain soir' : 'jusqu’à ' + f.toLocaleDateString('fr-FR', { weekday: 'long' });
}
function bqePromoBadge(a){
  const p = bqePromo(a);
  return p && !a.possede ? `<span class="bqe-promo">−${p.remise} % · ${bqePromoFin(p)}</span>` : '';
}
function bqePrixHtml(a){
  const p = bqePromo(a);
  if(p) return `<s>${euros(p.barre)}</s> ` + euros(bqePrixMoi(a));   // patch487
  const moi = bqePrixMoi(a), plein = Number(a.prix_centimes);""")
rep(A, """  return `<button type="button" class="bq-article bqe-article bqe-t-${a.type}" data-bqe="${echapperTexte(a.id)}">
      ${bqxEcrin(bqeVignette(a))}""", """  return `<button type="button" class="bq-article bqe-article bqe-t-${a.type}${bqePromo(a) && !a.possede ? ' bqe-en-promo' : ''}" data-bqe="${echapperTexte(a.id)}">
      ${bqePromoBadge(a)}${bqxEcrin(bqeVignette(a))}""")
rep(A, """  const libres = arts.filter(a => !a.possede && !a.livraison_le && !a.reserve_og && a.type !== 'effet');
  const cols = libres.filter(a => a.type === 'collection');
  const liste = cols.length ? cols : libres;""", """  const libres = arts.filter(a => !a.possede && !a.livraison_le && !a.reserve_og && a.type !== 'effet');
  const cols = libres.filter(a => a.type === 'collection');
  const promos = libres.filter(a => bqePromo(a));   // patch487 : le week-end, une collection en promo
  const liste = promos.length ? promos : cols.length ? cols : libres;""")
rep(A, """        <span class="bqx-sur">À la une · ${genre}</span>""", """        <span class="bqx-sur">${bqePromo(a) ? `Promo du week-end · −${bqePromo(a).remise} %` : 'À la une · ' + genre}</span>""")
rep(A, """        <span class="bqx-une-prix">${bqePrixHtml(a)}</span>
      </div></button>`;""", """        <span class="bqx-une-prix">${bqePrixHtml(a)}</span>${bqePromo(a) ? `<span class="bqx-une-promo">${bqePromoFin(bqePromo(a))}</span>` : ''}
      </div></button>`;""")
# la fiche : « tu en as déjà une partie » ne doit pas s'afficher à cause de la promo ; prix barré et date de fin
rep(A, """${bqePrixMoi(a) < Number(a.prix_centimes) ? ' (tu en as déjà une partie : tu ne paies que ce qui te manque)' : ''}`""",
       """${bqePrixMoi(a) < Number(bqePromo(a) ? bqePromo(a).prix : a.prix_centimes) ? ' (tu en as déjà une partie : tu ne paies que ce qui te manque)' : ''}`""")
rep(A, """          <h2 id="bqeNom">${echapperTexte(nom)}</h2><b class="bqe-gros-prix">${prix}</b></div></div>""",
       """          <h2 id="bqeNom">${echapperTexte(nom)}</h2><b class="bqe-gros-prix">${bqePromo(a) ? `<s>${euros(bqePromo(a).barre)}</s> ` : ''}${prix}</b></div></div>
      ${bqePromo(a) ? `<p class="bqe-info bqe-promo-info">−${bqePromo(a).remise} % ${bqePromoFin(bqePromo(a))} (fin le ${new Date(new Date(bqePromo(a).fin).getTime() - 60000).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })} à minuit). Le prix barré est le prix le plus bas des 30 jours avant la promo.</p>` : ''}""")

rep(C, """/* patch486 : l'onglet Atelier de la boutique */""", """/* patch487 : la promo du week-end */
.bqe-article.bqe-en-promo{ position:relative; }
.bqe-promo{ position:absolute; top:8px; left:8px; z-index:3; font-size:.72rem; font-weight:800; letter-spacing:.01em; color:#1A1404;
  background:#F0B429; border-radius:8px; padding:3px 7px; box-shadow:0 2px 8px rgba(0,0,0,.35); }
.bqe-prix s, .bqx-une-prix s, .bqe-gros-prix s{ opacity:.6; font-weight:500; margin-right:2px; }
.bqx-une-promo{ display:inline-block; margin-left:8px; font-size:.78rem; font-weight:700; color:#F0B429; }
.bqe-promo-info{ border-left:3px solid #F0B429; padding:6px 10px; text-align:left; font-size:.88rem; }
/* patch486 : l'onglet Atelier de la boutique */""")
print('patch487 : fini')
