# patch553 (+ s3-86) : « Mes garnisons » : un bouton « Retirer » à côté de « Recharger » (2 touches : la 2e annonce l'énergie rendue).
# Retirer une garnison rend maintenant 100 % de son énergie (dans la limite du plafond).
# Avant, on ne pouvait retirer une garnison que depuis la fiche de la commune sur la carte (question d'ADR_RDM).
import os, sys, json
R = sys.argv[1] if len(sys.argv) > 1 else '.'
def rep(f, a, b, n=1):
    p = os.path.join(R, f); t = open(p, encoding='utf-8').read()
    if t.count(a) != n:
        if b in t: print(f'{f} : déjà fait'); return
        raise SystemExit(f'{f} : {t.count(a)} occurrence(s) pour {a[:80]!r}')
    open(p, 'w', encoding='utf-8').write(t.replace(a, b)); print(f'{f} : ok')
rep('app.js', """        <button class="gl-r${gnDose === code ? ' actif' : ''}" data-gn-recharger="${code}" ${g.energie >= 10 ? 'disabled' : ''}>Recharger</button></div>""",
"""        <span class="gl-acts"><button class="gl-r${gnDose === code ? ' actif' : ''}" data-gn-recharger="${code}" ${g.energie >= 10 ? 'disabled' : ''}>Recharger</button>
        <button type="button" class="gl-x${gnRetraitListe === code ? ' arme' : ''}" data-gn-retirer-l="${code}">${gnRetraitListe === code ? `Retirer : +${Math.max(0, Math.min(g.energie, energiePlafond() - Math.floor(Number((energieEtat || {}).energie) || 0)))} ⚡ ?` : 'Retirer'}</button></span></div>""")   # patch553
rep('app.js', """      const b = e.target.closest('[data-gn-recharger]');
      if(b){ gnDose = gnDose === b.dataset.gnRecharger ? null : b.dataset.gnRecharger; renderGarnisons(); return; }""",
"""      const b = e.target.closest('[data-gn-recharger]');
      if(b){ gnRetraitListe = null; gnDose = gnDose === b.dataset.gnRecharger ? null : b.dataset.gnRecharger; renderGarnisons(); return; }
      const rx = e.target.closest('[data-gn-retirer-l]');   // patch553 : retirer depuis la liste, en deux touches
      if(rx){
        const code = rx.dataset.gnRetirerL;
        if(gnRetraitListe !== code){ gnRetraitListe = code; gnDose = null; renderGarnisons(); clearTimeout(gnRetraitMinuteur); gnRetraitMinuteur = setTimeout(() => { if(gnRetraitListe === code){ gnRetraitListe = null; renderGarnisons(); } }, 5000); return; }
        gnRetraitListe = null; rx.disabled = true;
        garnisonAction(code, 'retirer');
        return;
      }""")
rep('app.js', "  const rendu = Math.floor(g.energie * 3 / 4);", "  const rendu = g.energie;   // s3-86 : 100 % (avant : 75 %)")
rep('index.html', "Retirer une garnison rend les trois quarts de son énergie.", "Retirer une garnison rend <b>toute</b> son énergie (sans dépasser ton plafond).")
rep('app.js', "let gnRecherche = '';\n", "let gnRecherche = '';\nlet gnRetraitListe = null, gnRetraitMinuteur = 0;   // patch553\n")
css = """
/* patch553 : « Retirer » dans Mes garnisons */
.gl-acts{ flex:none; display:flex; flex-direction:column; align-items:flex-end; gap:4px; }
.gl-x{ border:none; background:none; color:var(--brume, #93A4C3); font:inherit; font-size:.74rem; padding:2px 4px; text-decoration:underline; text-underline-offset:2px; cursor:pointer; }
.gl-x:hover{ color:#fff; }
.gl-x.arme{ text-decoration:none; color:#fff; background:rgba(229,72,77,.3); border:1px solid rgba(229,72,77,.8); border-radius:999px; padding:4px 10px; }
"""
p = os.path.join(R, 'style.css'); t = open(p, encoding='utf-8').read()
if 'patch553' not in t: open(p, 'a', encoding='utf-8').write(css); print('style.css : ajouté')
p = os.path.join(R, 'data/nouveautes.json'); d = json.load(open(p, encoding='utf-8'))
n1 = "🛡️ Défendre › Mes garnisons : un bouton « Retirer » à côté de « Recharger ». Tu récupères toute l'énergie de la garnison (avant : 75 %) et la place se libère. Question d'ADR_RDM."
if n1 not in d[0]['nouveautes']: d[0]['nouveautes'].append(n1)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('nouveautes : ok')
